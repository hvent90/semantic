"""Main CLI entry point for the Codebase Summarizer tool."""

import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(
    name="semantic",
    help="A CLI tool that generates semantic summaries of codebases for AI coding agents",
    add_completion=False,
)


@app.command()
def generate(
    path: Optional[Path] = typer.Argument(
        None,
        help="The root path of the codebase to scan. Defaults to the current directory.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Force regeneration of all agents.md files, even if they appear up-to-date.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable detailed logging output.",
    ),
) -> None:
    """
    The primary command to perform a one-time scan and generation of agents.md files.
    """
    import logging
    from services.traversal_engine import TraversalEngine
    from services.analysis_orchestrator import AnalysisOrchestrator
    from services.summary_generator import SummaryGenerator
    from services.vcs_interface import VcsInterface
    
    target_path = path or Path.cwd()
    
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Reduce noise from HTTP requests unless in verbose mode
    if not verbose:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)
    
    logger.info(f"Generating summaries for codebase at: {target_path}")
    
    if force:
        logger.info("Force regeneration enabled")
    
    try:
        # Initialize components
        traversal_engine = TraversalEngine(target_path)
        orchestrator = AnalysisOrchestrator()
        generator = SummaryGenerator()
        vcs = VcsInterface(target_path)
        
        # Get commit hash for metadata
        commit_hash = vcs.get_current_commit_hash()
        
        # Process each directory
        directories_processed = 0
        for directory in traversal_engine.get_directories_to_process():
            logger.info(f"Processing directory: {directory}")
            
            # Skip if agents.md exists and force is not enabled
            agents_file = directory / "agents.md"
            if agents_file.exists() and not force:
                logger.info(f"Skipping {directory}: agents.md already exists (use --force to regenerate)")
                continue
            
            # Analyze the directory
            analysis = orchestrator.analyze_directory(directory)
            
            # Generate metadata
            metadata = generator.create_metadata(commit_hash)
            
            # Generate content
            content = generator.generate_agents_md_content(analysis, metadata)
            
            # Write to file
            generator.write_to_file(content, agents_file)
            logger.info(f"Generated agents.md for {directory}")
            directories_processed += 1
        
        typer.echo(f"✓ Successfully processed {directories_processed} directories")
        
        # Log final LLM usage summary
        from services.llm_usage_metrics import llm_usage_collector
        if llm_usage_collector._total_calls > 0:
            summary = llm_usage_collector.get_session_summary()
            typer.echo(f"📊 LLM Usage Summary: {summary['total_calls']} calls, {summary['total_tokens']} tokens, ${summary['total_estimated_cost']:.4f} total cost")
        
    except Exception as e:
        logger.error(f"Error during generation: {e}")
        typer.echo(f"✗ Generation failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def verify(
    path: Optional[Path] = typer.Argument(
        None,
        help="The root path of the codebase to verify. Defaults to the current directory.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
) -> None:
    """
    A command intended for CI/CD pipelines to verify that committed agents.md files 
    are in sync with the source code. Exits with non-zero status code if out of sync.
    """
    import logging
    from services.traversal_engine import TraversalEngine
    from services.analysis_orchestrator import AnalysisOrchestrator
    from services.summary_generator import SummaryGenerator
    from services.vcs_interface import VcsInterface
    
    target_path = path or Path.cwd()
    
    # Configure logging for CI (less verbose by default)
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info(f"Verifying summaries for codebase at: {target_path}")
    
    try:
        # Initialize components
        traversal_engine = TraversalEngine(target_path)
        orchestrator = AnalysisOrchestrator()
        generator = SummaryGenerator()
        vcs = VcsInterface(target_path)
        
        # Get commit hash for metadata
        commit_hash = vcs.get_current_commit_hash()
        
        out_of_sync_files = []
        directories_checked = 0
        
        # Process each directory that should have an agents.md file
        for directory in traversal_engine.get_directories_to_process():
            logger.debug(f"Checking directory: {directory}")
            
            agents_file = directory / "agents.md"
            if not agents_file.exists():
                logger.warning(f"Missing agents.md file: {agents_file}")
                out_of_sync_files.append(str(agents_file))
                continue
            
            # Analyze the directory to get current state
            analysis = orchestrator.analyze_directory(directory)
            
            # Generate what the current content should be
            metadata = generator.create_metadata(commit_hash)
            expected_content = generator.generate_agents_md_content(analysis, metadata)
            expected_markdown = generator.serialize_to_markdown(expected_content)
            
            # Read the existing file
            try:
                with open(agents_file, 'r', encoding='utf-8') as f:
                    actual_markdown = f.read()
            except (IOError, UnicodeDecodeError) as e:
                logger.error(f"Could not read {agents_file}: {e}")
                out_of_sync_files.append(str(agents_file))
                continue
            
            # Compare content intelligently (ignore metadata differences)
            if not _content_matches(actual_markdown, expected_markdown):
                logger.warning(f"Content mismatch: {agents_file}")
                out_of_sync_files.append(str(agents_file))
            
            directories_checked += 1
        
        # Report results
        if out_of_sync_files:
            typer.echo(f"✗ Verification failed: {len(out_of_sync_files)} files out of sync", err=True)
            typer.echo("Out of sync files:", err=True)
            for file_path in out_of_sync_files:
                typer.echo(f"  - {file_path}", err=True)
            typer.echo("Run 'semantic generate --force' to update files", err=True)
            raise typer.Exit(1)
        else:
            typer.echo(f"✓ Verification passed: {directories_checked} directories checked")
            
    except typer.Exit:
        # Re-raise typer.Exit to preserve exit code
        raise
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        typer.echo(f"✗ Verification failed due to error: {e}", err=True)
        raise typer.Exit(1)


def _content_matches(actual: str, expected: str) -> bool:
    """
    Compare two agents.md contents, ignoring metadata differences.
    This function intelligently ignores fields like last_generated_utc and commit_hash
    that are expected to differ between runs.
    """
    # Split into lines for easier processing
    actual_lines = actual.strip().split('\n')
    expected_lines = expected.strip().split('\n')
    
    # Remove metadata lines that are expected to differ
    actual_filtered = _filter_metadata_lines(actual_lines)
    expected_filtered = _filter_metadata_lines(expected_lines)
    
    # Compare the filtered content
    return actual_filtered == expected_filtered


def _filter_metadata_lines(lines: list) -> list:
    """
    Filter out metadata lines that are expected to change between runs.
    """
    filtered = []
    for line in lines:
        line = line.strip()
        # Skip metadata fields that change between runs
        if (line.startswith('- last_generated_utc:') or 
            line.startswith('- commit_hash:')):
            continue
        filtered.append(line)
    return filtered


@app.command()
def init(
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing .semanticsrc file if it exists.",
    ),
) -> None:
    """
    Initialize a .semanticsrc configuration file in the current directory.
    """
    from services.config import SemanticConfig
    
    config_path = Path.cwd() / ".semanticsrc"
    
    if config_path.exists() and not force:
        typer.echo(f"✗ Configuration file already exists: {config_path}")
        typer.echo("Use --force to overwrite the existing file")
        raise typer.Exit(1)
    
    try:
        # Create example configuration
        config = SemanticConfig(Path.cwd())
        example_content = config.create_example_config()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(example_content)
        
        typer.echo(f"✓ Created configuration file: {config_path}")
        typer.echo("Edit the file to customize exclusion patterns for your project")
        
    except Exception as e:
        typer.echo(f"✗ Failed to create configuration file: {e}", err=True)
        raise typer.Exit(1)


hook_app = typer.Typer(help="Hook management commands")
app.add_typer(hook_app, name="hook")


@hook_app.command("install")
def hook_install(
    hook_type: str = typer.Option(
        "pre-commit",
        "--type",
        help="The type of hook to install (e.g., pre-commit).",
    ),
) -> None:
    """
    A helper command to install the summarizer into a Git pre-commit hook.
    """
    import yaml
    import logging
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    
    if hook_type != "pre-commit":
        typer.echo(f"✗ Unsupported hook type: {hook_type}. Currently only 'pre-commit' is supported.", err=True)
        raise typer.Exit(1)
    
    try:
        # Path to .pre-commit-config.yaml
        config_path = Path.cwd() / ".pre-commit-config.yaml"
        
        # Create or update .pre-commit-config.yaml
        hook_config = {
            "repos": [
                {
                    "repo": "local",
                    "hooks": [
                        {
                            "id": "generate-summaries",
                            "name": "Generate agents.md summaries", 
                            "entry": "semantic generate .",
                            "language": "system",
                            "files": r"\.(py|js|go|ts|tsx|jsx|java|kt|scala|c|cpp|cc|cxx|h|hpp|rs|rb|php|cs|swift|r|R|sql|sh|bash|yaml|yml|json|toml|ini|cfg|md|rst)$",
                            "stages": ["commit"]
                        }
                    ]
                }
            ]
        }
        
        if config_path.exists():
            # Read existing configuration
            with open(config_path, 'r', encoding='utf-8') as f:
                existing_config = yaml.safe_load(f) or {}
            
            # Check if our hook already exists
            repos = existing_config.get('repos', [])
            semantic_repo = None
            semantic_hook_exists = False
            
            for repo in repos:
                if repo.get('repo') == 'local':
                    semantic_repo = repo
                    hooks = repo.get('hooks', [])
                    for hook in hooks:
                        if hook.get('id') == 'generate-summaries':
                            semantic_hook_exists = True
                            break
                    break
            
            if semantic_hook_exists:
                typer.echo("ℹ Pre-commit hook for semantic tool already exists")
                return
            
            # Add our hook to existing local repo or create new local repo
            if semantic_repo:
                if 'hooks' not in semantic_repo:
                    semantic_repo['hooks'] = []
                semantic_repo['hooks'].append(hook_config['repos'][0]['hooks'][0])
            else:
                existing_config.setdefault('repos', []).append(hook_config['repos'][0])
                
            # Write updated configuration
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_config, f, default_flow_style=False, sort_keys=False)
                
        else:
            # Create new configuration file
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(hook_config, f, default_flow_style=False, sort_keys=False)
        
        typer.echo(f"✓ Successfully installed pre-commit hook in {config_path}")
        typer.echo("To complete the installation, run:")
        typer.echo("  pre-commit install")
        
    except ImportError:
        typer.echo("✗ PyYAML is required to install pre-commit hooks. Install it with: pip install PyYAML", err=True)
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Error installing hook: {e}")
        typer.echo(f"✗ Failed to install pre-commit hook: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
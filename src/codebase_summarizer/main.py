"""Main CLI entry point for the Codebase Summarizer tool."""

import typer
import asyncio
from pathlib import Path
from typing import Optional, List

from services.config import SemanticConfig
from services.llm_client import llm_client
from services.llm_usage_metrics import LLMProvider, AVAILABLE_MODELS

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
    provider: str = typer.Option(
        "openai",
        "--provider",
        help="LLM provider to use (openai, anthropic, google)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        help="Specific model to use (uses provider default if not specified)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Force regeneration of all summary files, even if they appear up-to-date.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable detailed logging output.",
    ),
    output_format: str = typer.Option(
        None,
        "--output-format",
        help="Output file format: agents or claude. Overrides .semanticsrc setting.",
    ),
) -> None:
    """
    The primary command to perform a one-time scan and generation of semantic summary files.

    Output files are named based on the --output-format option or .semanticsrc configuration:
    - agents: Creates agents.md files (default)
    - claude: Creates claude.md files
    """
    import logging
    from services.traversal_engine import TraversalEngine
    from services.analysis_orchestrator import AnalysisOrchestrator

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
    
    logger.info(f"Generating semantic summaries for codebase at: {target_path}")

    if force:
        logger.info("Force regeneration enabled")

    # Load configuration
    config = SemanticConfig(target_path)

    # Determine provider with inference support (CLI > inferred > config > default)
    if provider == "openai":  # default value, check if we can infer from model
        if model is not None:
            # Try to infer provider from model first
            inferred_provider = _infer_provider_from_model(model)
            if inferred_provider:
                llm_provider = inferred_provider
            else:
                # Model specified but can't infer provider, will error later in validation
                llm_provider = config.get_llm_provider()
        else:
            # No model specified, use config or default
            llm_provider = config.get_llm_provider()
    else:
        # Provider explicitly specified, validate it
        try:
            llm_provider = LLMProvider(provider)
        except ValueError:
            valid_providers = [p.value for p in LLMProvider]
            typer.echo(f"✗ Invalid provider '{provider}'. Valid options: {', '.join(valid_providers)}", err=True)
            raise typer.Exit(1)

    # Log provider inference for transparency
    if provider == "openai" and model is not None and llm_provider != LLMProvider.OPENAI:
        logger.info(f"Inferred provider '{llm_provider.value}' from model '{model}'")

    # Determine model (CLI > config > provider default)
    if model is None:
        model = config.get_llm_model(llm_provider)

    # Validate and resolve model if specified
    if model:
        resolved_model = _resolve_model_alias(llm_provider, model)
        if not resolved_model:
            # Check if user provided a model for wrong provider
            correct_provider = _infer_provider_from_model(model)
            if correct_provider and correct_provider != llm_provider:
                typer.echo(f"✗ Model '{model}' belongs to {correct_provider.value}, but {llm_provider.value} provider was specified.", err=True)
                typer.echo(f"💡 Try: --model {model} (without --provider) or --provider {correct_provider.value} --model {model}", err=True)
            else:
                available = AVAILABLE_MODELS[llm_provider]["models"]
                aliases = AVAILABLE_MODELS[llm_provider].get("aliases", {})
                all_options = list(available) + list(aliases.keys())
                typer.echo(f"✗ Invalid model '{model}' for {llm_provider.value}. Available: {', '.join(all_options)}", err=True)
            raise typer.Exit(1)
        model = resolved_model

    # Initialize LLM client with selected provider/model
    from services.llm_client import LLMClient
    global llm_client
    llm_client = LLMClient(provider=llm_provider, model=model)
    
    try:
        # Initialize components
        traversal_engine = TraversalEngine(target_path)
        orchestrator = AnalysisOrchestrator()

        # Process directories in parallel with rate limiting
        directories_processed = asyncio.run(_process_directories_async(
            traversal_engine, orchestrator, logger, force, output_format, max_concurrent=15
        ))
        
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

async def _process_directories_async(traversal_engine, orchestrator, logger, force: bool, output_format: Optional[str] = None, max_concurrent: int = 5) -> int:
    """
    Process directories asynchronously with semaphore-based rate limiting.

    Args:
        traversal_engine: Engine to get directories to process
        orchestrator: Analysis orchestrator
        logger: Logger instance
        force: Whether to force regeneration
        output_format: Output format override from CLI
        max_concurrent: Maximum number of concurrent LLM operations

    Returns:
        Number of directories processed
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def _process_single_directory(directory, output_format: Optional[str] = None):
        """Process a single directory with semaphore protection."""
        async with semaphore:
            logger.info(f"Processing directory: {directory}")

            # Get output format from CLI option, config, or default
            config = SemanticConfig(directory.parent if directory.parent.exists() else directory)
            effective_format = output_format or config.get_output_format()
            output_filename = config.format_to_filename(effective_format)
            output_file = directory / output_filename

            # Skip if output file exists and force is not enabled
            if output_file.exists() and not force:
                logger.info(f"Skipping {directory}: {output_filename} already exists (use --force to regenerate)")
                return False

            # Collect file contents from the directory
            file_contents_str = ""

            # Get all source files in the directory (non-recursive)
            config = SemanticConfig(directory.parent if directory.parent.exists() else directory)
            source_files = orchestrator._get_source_files(directory, config)
            logger.debug(f"Found {len(source_files)} source files")

            for file_path in source_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        # Get file extension for syntax highlighting
                        file_extension = file_path.suffix.lstrip('.')
                        file_contents_str += f"\n### File: {file_path.name}\n"
                        file_contents_str += f"```{file_extension}\n"
                        file_contents_str += file_content
                        file_contents_str += "\n```\n"
                except (IOError, UnicodeDecodeError) as e:
                    logger.warning(f"Could not read file {file_path}: {e}")
                    file_contents_str += f"\n### File: {file_path.name}\n"
                    file_contents_str += f"[Error reading file: {e}]\n"
            
            prompt = f"""You are an expert technical documentation generator that creates semantic summary files for AI coding agents.

            Your role is to generate a structured overview of a codebase directory for AI agents to understand and navigate effectively.

            Here is an example of the expected format:

            ```markdown
            ## Required Skillsets
            - Python
            - FastAPI
            - SQL

            ## APIs
            ### `user_service.py`
            class Authenticator (lines 10-100): Handles user authentication and authorization. 
              - (lines 25-45) public getUserById(id: number) -> User: Fetches a user record from the database by their primary ID.
              - (lines 58-70) public deleteUser(id: number) -> bool: Removes a user record from the database.
            ```

            Requirements: 
            - Format APIs grouped by source file with proper markdown formatting
            - Include line numbers where applicable
            - Focus on APIs, classes, functions, and important interfaces
            - Identify required skillsets/technologies used
            - For each function and class, add a one or two sentence (MAX) description after writing the signature.

            Now generate the complete file content for the files in this directory:

            {file_contents_str}

            Generate the complete overview now:"""

            try:
                content = await llm_client.summarize_async(prompt)

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)

                logger.info(f"Generated {output_filename} for {directory}")
                return True
            except Exception as e:
                logger.error(f"Error processing directory {directory}: {e}")
                return False
    
    # Create tasks for all directories
    directories = list(traversal_engine.get_directories_to_process())
    tasks = [_process_single_directory(directory, output_format) for directory in directories]
    
    # Process tasks and count successful completions
    directories_processed = 0
    for completed_task in asyncio.as_completed(tasks):
        try:
            success = await completed_task
            if success:
                directories_processed += 1
        except Exception as e:
            logger.error(f"Task failed: {e}")
    
    return directories_processed


def _resolve_model_alias(provider: LLMProvider, model: str) -> Optional[str]:
    """Resolve model alias to full model name."""
    provider_config = AVAILABLE_MODELS[provider]

    # Check if it's already a valid full model name
    if model in provider_config["models"]:
        return model

    # Check if it's an alias
    aliases = provider_config.get("aliases", {})
    if model in aliases:
        return aliases[model]

    return None


def _infer_provider_from_model(model: str) -> Optional[LLMProvider]:
    """
    Infer the LLM provider from a model name by checking all available models and aliases.

    Args:
        model: The model name to analyze

    Returns:
        The inferred LLMProvider, or None if no match found
    """
    # Check each provider's models and aliases
    for provider in LLMProvider:
        provider_config = AVAILABLE_MODELS[provider]

        # Check direct model name match
        if model in provider_config["models"]:
            return provider

        # Check alias match
        aliases = provider_config.get("aliases", {})
        if model in aliases:
            return provider

    return None


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
                            "name": "Generate semantic summaries",
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
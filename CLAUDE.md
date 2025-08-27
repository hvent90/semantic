# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<!-- NAUTEX_SECTION_START -->

# Nautex MCP Integration

This project uses Nautex Model-Context-Protocol (MCP). Nautex manages requirements and task-driven LLM assisted development.
 
Whenever user requests to operate with nautex, the following applies: 

- read full Nautex workflow guidelines from `.nautex/CLAUDE.md`
- note that all paths managed by nautex are relative to the project root
- note primary workflow commands: `next_scope`, `tasks_update` 
- NEVER edit files in `.nautex` directory

<!-- NAUTEX_SECTION_END -->

## Tech Stack

- **Language**: Python 3.10+ 
- **CLI Framework**: Typer with all extras (typer[all]>=0.9.0)
- **Data Validation**: Pydantic 2.0+ for type-safe data models
- **LLM Integration**: OpenAI API 1.0+ for code analysis and summarization
- **Configuration**: PyYAML for .semanticsrc config files
- **File Pattern Matching**: pathspec>=0.11.0 for gitignore-style patterns
- **Date/Time**: python-dateutil>=2.8.0 for timestamp handling
- **Build System**: setuptools with pyproject.toml configuration
- **Code Quality**: Black formatter, isort import sorting, flake8 linting, mypy type checking

## Project Structure

- `src/`: Main source code directory with package-based organization
  - `codebase_summarizer/`: Primary CLI module
    - `main.py`: Typer CLI application entry point with commands
  - `models/`: Pydantic data models
    - `data_models.py`: Core data structures (ApiInfo, DirectoryAnalysis, etc.)
  - `services/`: Business logic and external service integration
    - `analysis_orchestrator.py`: Coordinates file analysis and LLM processing
    - `config.py`: Handles .semanticsrc configuration file parsing
    - `llm_client.py`: OpenAI API integration and prompt management
    - `llm_usage_metrics.py`: Tracks LLM API usage and costs
    - `traversal_engine.py`: Directory traversal with exclusion pattern support
    - `vcs_interface.py`: Git version control system integration
- `debug_runner.py`: Development utility script for testing
- `pyproject.toml`: Project configuration, dependencies, and tool settings
- `.semanticsrc`: Configuration file for exclude patterns
- `.env.example`: Environment variable template (OpenAI API key)

## Commands

The project provides a `semantic` CLI tool with the following commands:

### Core Commands
- `semantic generate [path]`: Generate .semantic files for codebase analysis
  - `--force`: Force regeneration of existing .semantic files  
  - `--verbose`: Enable detailed logging output
- `semantic init`: Create a .semanticsrc configuration file
  - `--force`: Overwrite existing configuration file

### Hook Management  
- `semantic hook install --type pre-commit`: Install pre-commit hook for automatic generation
  - Requires PyYAML and pre-commit packages
  - Creates/updates .pre-commit-config.yaml

### Development Commands
- `pip install -e .`: Install in development mode
- `python debug_runner.py`: Run development tests/debugging (if present)

### Inferred Commands from Dependencies
- `black src/`: Format Python code (line-length: 88, target: py310)
- `isort src/`: Sort imports (black-compatible profile)  
- `flake8 src/`: Lint code for style issues
- `mypy src/`: Static type checking (strict mode enabled)
- `pytest`: Run test suite (pytest>=7.0.0 in dev dependencies)

## Code Style

- **Formatting**: Black formatter with 88-character line length, Python 3.10 target
- **Import Sorting**: isort with black-compatible profile, src_paths configured for src/ and tests/
- **Type Checking**: mypy with strict configuration:
  - `python_version = "3.10"`
  - `warn_return_any = true`
  - `warn_unused_configs = true`
  - `disallow_untyped_defs = true`
- **Linting**: flake8 for additional style checking
- **Import Style**: Relative imports within packages, absolute imports for external dependencies
- **Naming Conventions**: 
  - snake_case for variables, functions, and modules
  - PascalCase for classes and Pydantic models
  - UPPER_CASE for constants
- **Documentation**: Docstrings follow Google/NumPy style with type hints in signatures
- **Error Handling**: Comprehensive logging with structured error messages

## Workflow

### Development Setup
1. Clone repository and navigate to project root
2. Create Python virtual environment (`python -m venv .venv`)
3. Activate virtual environment (`source .venv/bin/activate`)
4. Install in development mode: `pip install -e .[dev]`
5. Set up environment variables: Copy `.env.example` to `.env` and add OpenAI API key
6. Initialize configuration: `semantic init`

### Testing & Quality Assurance
- Run type checking: `mypy src/`
- Format code: `black src/`
- Sort imports: `isort src/`
- Lint code: `flake8 src/`
- Run tests: `pytest` (if test suite exists)
- Test CLI: `python debug_runner.py` or `semantic --help`

### Git Workflow
- Feature branch development (currently on `twill_claude/ENG-8`)
- Commit messages follow conventional format
- Recent commits show iterative refinement and cleanup
- Pre-commit hooks can be configured via `semantic hook install`

### Deployment Process
- Package built via setuptools with pyproject.toml configuration
- CLI entry point: `semantic = "codebase_summarizer.main:app"`
- Distribution via pip: `pip install semantic` (when published)
- Supports Python 3.10, 3.11, and 3.12

### Configuration Management
- `.semanticsrc`: YAML configuration for exclusion patterns
- `.env`: Environment variables for API keys and settings
- Patterns support gitignore-style exclusions for directories and files
- Default exclusions: node_modules/, .venv/, __pycache__/, build/, dist/, .git/

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

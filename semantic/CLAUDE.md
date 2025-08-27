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

# Tech Stack

- **Language**: Python 3.10+ (supports 3.10, 3.11, 3.12)
- **CLI Framework**: Typer (>=0.9.0) with full completion support
- **Data Validation**: Pydantic (>=2.0.0) for data models
- **LLM Integration**: OpenAI API (>=1.0.0) for semantic analysis
- **Build System**: setuptools with modern pyproject.toml configuration
- **Code Quality**: Black, isort, flake8, mypy for formatting and type checking
- **Testing**: pytest with coverage support (pytest-cov)
- **File Processing**: pathspec for glob pattern matching, python-dateutil for timestamps
- **Optional Dependencies**: PyYAML for configuration files, pre-commit for Git hooks

# Project Structure

- `src/`: Main source code directory using modern Python packaging layout
  - `codebase_summarizer/`: Primary CLI application module
    - `main.py`: CLI entry point with Typer commands (generate, init, hook)
  - `models/`: Data models and schemas
    - `data_models.py`: Pydantic models for structured data
  - `services/`: Core business logic and service layer
    - `analysis_orchestrator.py`: Coordinates semantic analysis workflow
    - `config.py`: Configuration file handling for `.semanticsrc` files
    - `llm_client.py`: OpenAI API client wrapper for LLM interactions
    - `llm_usage_metrics.py`: Token usage tracking and cost estimation
    - `traversal_engine.py`: Directory traversal and file discovery
    - `vcs_interface.py`: Version control system integrations
- `debug_runner.py`: Development utility for local testing
- `pyproject.toml`: Modern Python packaging configuration with all metadata
- `.gitignore`: Comprehensive Python/IDE ignore patterns
- `README.md`: User documentation with installation and usage instructions

# Commands

- `pip install -e .`: Install in development mode with editable installation
- `semantic generate`: Generate `.semantic` files for current directory
- `semantic generate /path/to/codebase`: Generate summaries for specific path
- `semantic generate --force`: Force regeneration of existing files
- `semantic generate --verbose`: Enable detailed logging output
- `semantic init`: Initialize `.semanticsrc` configuration file
- `semantic init --force`: Overwrite existing configuration file
- `semantic hook install --type pre-commit`: Install pre-commit Git hooks
- `python debug_runner.py`: Run local development/testing script
- `pytest`: Run test suite (when tests are implemented)
- `pytest --cov`: Run tests with coverage reporting
- `black src/`: Format code with Black (88 character line length)
- `isort src/`: Sort imports using Black-compatible profile
- `flake8 src/`: Lint code for style violations
- `mypy src/`: Type checking with strict configuration

# Code Style

- **Formatting**: Black with 88-character line length, Python 3.10+ target
- **Import Sorting**: isort with Black-compatible profile, organized by source paths
- **Linting**: flake8 for PEP 8 compliance and code quality
- **Type Checking**: mypy with strict configuration (disallow_untyped_defs enabled)
- **Docstrings**: Google-style docstrings with type annotations
- **Error Handling**: Comprehensive try-catch blocks with logging
- **Async Patterns**: async/await for LLM operations with semaphore-based rate limiting
- **Path Handling**: Pathlib for cross-platform file operations
- **Configuration**: Pydantic models for structured configuration validation
- **Logging**: Standard library logging with configurable levels and formatters

# Workflow

- **Development**: Clone repository, install with `pip install -e .` for editable mode
- **Configuration**: Initialize project with `semantic init` to create `.semanticsrc`
- **Local Testing**: Use `debug_runner.py` for development and debugging
- **Code Quality**: Run black, isort, flake8, and mypy before commits
- **Git Integration**: Install pre-commit hooks with `semantic hook install`
- **Environment Setup**: Requires Python 3.10+, OpenAI API key for LLM integration
- **File Processing**: Tool processes source files and generates `.semantic` summaries
- **Token Management**: Built-in usage tracking and cost estimation for LLM operations
- **Error Handling**: Comprehensive logging and graceful failure recovery
- **Extensibility**: Service-oriented architecture for easy feature additions

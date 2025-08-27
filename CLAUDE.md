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

- **Language**: Python 3.10+ (supports Python 3.10, 3.11, 3.12)
- **CLI Framework**: Typer with rich support (`typer[all]>=0.9.0`)
- **Data Validation**: Pydantic 2.0+ for models and configuration
- **LLM Integration**: OpenAI API (`openai>=1.0.0`) for semantic analysis
- **Package Manager**: pip with setuptools build system
- **File Pattern Matching**: pathspec for gitignore-style patterns
- **Configuration**: YAML support via PyYAML (optional dependency)
- **Git Integration**: Git hooks via pre-commit framework

## Development Dependencies
- **Testing**: pytest with coverage (`pytest>=7.0.0`, `pytest-cov>=4.0.0`)
- **Code Formatting**: Black (`black>=23.0.0`) with 88 character line length
- **Import Sorting**: isort (`isort>=5.12.0`) with Black profile
- **Linting**: flake8 (`flake8>=6.0.0`)
- **Type Checking**: mypy (`mypy>=1.0.0`) with strict configuration

# Project Structure

- `src/`: Main source code directory using flat package structure
  - `codebase_summarizer/`: Main CLI application module
    - `main.py`: CLI entry point with Typer commands (`semantic generate`, `semantic init`, `semantic hook`)
  - `models/`: Pydantic data models and type definitions
    - `data_models.py`: Core models (ApiInfo, DirectoryAnalysis, AgentsMdContent, etc.)
  - `services/`: Core business logic and service classes
    - `analysis_orchestrator.py`: Orchestrates the semantic analysis process
    - `config.py`: Configuration file handling for `.semanticsrc`
    - `llm_client.py`: OpenAI API client with usage metrics tracking
    - `llm_usage_metrics.py`: LLM usage tracking and cost estimation
    - `traversal_engine.py`: Directory traversal and file discovery
    - `vcs_interface.py`: Git integration utilities
- `debug_runner.py`: Development script for running the CLI locally
- `.semanticsrc`: Project configuration file with exclusion patterns
- `pyproject.toml`: Modern Python packaging configuration with tool settings

# Commands

## Core CLI Commands
- `semantic generate [PATH]`: Generate .semantic summary files for codebase
  - `--force`: Force regeneration of existing files
  - `--verbose`: Enable detailed logging output
- `semantic init`: Initialize `.semanticsrc` configuration file
  - `--force`: Overwrite existing configuration
- `semantic hook install`: Install pre-commit Git hooks
  - `--type pre-commit`: Install as pre-commit hook (default)

## Development Commands
- `python debug_runner.py`: Run CLI locally during development
- `pip install -e .`: Install package in editable mode
- `pip install semantic[dev]`: Install with development dependencies

## Testing & Quality (when available)
- `pytest`: Run test suite with coverage
- `black src/`: Format code with Black
- `isort src/`: Sort imports
- `flake8 src/`: Run linting checks
- `mypy src/`: Run type checking

# Code Style

- **Formatting**: Black with 88-character line length, Python 3.10+ target
- **Import Sorting**: isort with Black profile compatibility
- **Type Checking**: mypy with strict mode enabled (`disallow_untyped_defs: true`)
- **Linting**: flake8 for additional code quality checks
- **Package Structure**: Flat package layout under `src/` directory
- **Import Style**: Relative imports within packages, absolute for external dependencies
- **Naming Conventions**:
  - Snake_case for functions, variables, and modules
  - PascalCase for classes and Pydantic models
  - ALL_CAPS for constants
- **Documentation**: Docstrings follow Google style with type hints
- **Error Handling**: Comprehensive logging with different levels (DEBUG, INFO, WARNING, ERROR)

# Workflow

## Development
- **Local Setup**: Use `debug_runner.py` for development testing
- **Environment**: Supports `.env` file for API keys (OPENAI_API_KEY)
- **Package Installation**: `pip install -e .` for development mode
- **Configuration**: `.semanticsrc` file for project-specific settings

## Code Quality
- **Type Safety**: Full type hints with mypy strict mode
- **Code Formatting**: Automatic formatting with Black (88 chars)
- **Import Organization**: Sorted imports with isort
- **Testing**: pytest framework with coverage reporting (when tests exist)

## Git Integration
- **Pre-commit Hooks**: Automatic `.semantic` file generation on commits
- **Branch Strategy**: Feature branches (currently on `twill_claude/ENG-9`)
- **Commit History**: Clean commits with descriptive messages

## Deployment
- **Distribution**: Standard Python package via setuptools
- **Entry Point**: CLI available as `semantic` command after installation
- **Dependencies**: Core runtime dependencies kept minimal, dev dependencies separated
- **Python Compatibility**: Supports Python 3.10, 3.11, and 3.12

## Key Features
- **Semantic Analysis**: Generates `.semantic` files with skillsets and API documentation
- **LLM Integration**: Uses OpenAI API for intelligent code summarization
- **Configuration-Driven**: Flexible exclusion patterns via `.semanticsrc`
- **Git Hooks**: Automated generation via pre-commit hooks
- **Async Processing**: Concurrent directory processing with rate limiting
- **Usage Tracking**: Built-in LLM usage metrics and cost estimation
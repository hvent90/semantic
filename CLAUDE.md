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

- **Language**: Python 3.10+ (supports 3.10, 3.11, 3.12)
- **Framework**: Typer CLI framework with async support
- **Runtime**: Python with asyncio for concurrent processing
- **Build Tool**: setuptools (modern build-system configuration)
- **Testing**: pytest with coverage support (pytest-cov)
- **Package Manager**: pip with pyproject.toml configuration
- **LLM Integration**: OpenAI API client for AI-powered code analysis
- **Configuration**: YAML-based configuration files (.semanticsrc)

## Project Structure

- `src/`: Primary source code location organized by modules
- `src/codebase_summarizer/`: Main CLI application entry point
- `src/services/`: Core business logic and service components
  - `analysis_orchestrator.py`: Orchestrates the semantic analysis process
  - `llm_client.py`: OpenAI API client for LLM interactions
  - `traversal_engine.py`: File system traversal and directory processing
  - `config.py`: Configuration management for .semanticsrc files
  - `llm_usage_metrics.py`: Tracks and reports LLM usage statistics
  - `vcs_interface.py`: Version control system integration
- `src/models/`: Data models and type definitions (Pydantic models)
- `debug_runner.py`: Development utility script for running the CLI locally
- `.semanticsrc`: Project-specific configuration for exclusion patterns
- `.env.example`: Environment variable template for OpenAI API key

## Commands

- **Development**: `python debug_runner.py` or `python -m src.codebase_summarizer.main`
- **Install**: `pip install -e .` (editable install for development)
- **Install Dependencies**: `pip install -e .[dev]` (includes development dependencies)
- **CLI Usage**: 
  - `semantic generate [path]` - Generate .semantic files for codebase analysis
  - `semantic init` - Create a .semanticsrc configuration file
  - `semantic hook install --type pre-commit` - Install pre-commit hook
- **Testing**: `pytest` (with coverage: `pytest --cov`)
- **Linting**: 
  - `black src/` - Code formatting
  - `isort src/` - Import sorting
  - `flake8 src/` - Style checking
  - `mypy src/` - Type checking

## Code Style

- **Formatting**: Black with 88-character line length, targeting Python 3.10+
- **Import Sorting**: isort configured with "black" profile for consistency
- **Type Checking**: mypy with strict configuration (disallow_untyped_defs enabled)
- **Linting**: flake8 for style enforcement
- **Documentation**: Google-style docstrings with type hints
- **Naming Conventions**: 
  - Snake_case for variables, functions, and module names
  - PascalCase for class names
  - ALL_CAPS for constants
- **File Organization**: Modular structure with separate concerns (services, models, CLI)
- **Import Style**: Absolute imports from src root, grouped by standard/third-party/local

## Workflow

- **Development**: 
  - Use `debug_runner.py` for local testing and development
  - Install in editable mode with `pip install -e .[dev]`
  - Set up OpenAI API key in `.env` file (copy from `.env.example`)
- **Testing**: 
  - Run `pytest` for unit tests
  - Use `pytest --cov` for coverage reports
  - Test files should follow pytest naming conventions
- **Code Quality**:
  - Run black, isort, flake8, and mypy before committing
  - Follow type hints throughout the codebase
  - Use Pydantic for data validation and modeling
- **Deployment**: 
  - Package as Python wheel using setuptools
  - Distribute via PyPI or direct installation
  - CLI script entry point: `semantic` command
- **Git Integration**: 
  - Supports pre-commit hooks for automatic .semantic file generation
  - Use `semantic hook install --type pre-commit` to set up automation
- **Configuration**: 
  - Use `.semanticsrc` files for project-specific exclusion patterns
  - Initialize with `semantic init` command

## Important Instructions

- **Do what has been asked; nothing more, nothing less**
- **NEVER create files unless they're absolutely necessary for achieving your goal**
- **ALWAYS prefer editing an existing file to creating a new one**
- **NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User**
- When working with the semantic CLI tool, use the existing service architecture
- Respect the async/concurrent processing patterns used in the analysis orchestrator
- Follow the established error handling and logging patterns
- Use the existing configuration system for any new features requiring settings

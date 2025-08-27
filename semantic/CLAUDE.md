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
- **Framework**: Typer CLI framework for command-line interface
- **Build Tool**: setuptools with pyproject.toml configuration
- **Testing**: pytest with coverage support
- **Package Manager**: pip with pyproject.toml dependencies
- **LLM Integration**: OpenAI GPT models via openai>=1.0.0
- **Data Validation**: Pydantic v2.0+ for data models
- **File Pattern Matching**: pathspec for .gitignore-style exclusions
- **Configuration**: YAML-based .semanticsrc files (optional PyYAML dependency)

# Project Structure

- `src/`: Main source code directory
  - `codebase_summarizer/`: Core CLI application
    - `main.py`: Entry point with Typer CLI commands (generate, init, hook install)
  - `models/`: Data models and schemas
    - `data_models.py`: Pydantic models for API info, directory analysis, and content structure
  - `services/`: Core business logic and services
    - `analysis_orchestrator.py`: Orchestrates directory analysis and .semantic file generation
    - `config.py`: Configuration handling for .semanticsrc files
    - `llm_client.py`: OpenAI client wrapper with usage metrics tracking
    - `llm_usage_metrics.py`: LLM API call tracking and cost estimation
    - `traversal_engine.py`: Directory traversal with configurable exclusions
    - `vcs_interface.py`: Version control system integration
- `debug_runner.py`: Development debug script for running CLI locally
- `.semanticsrc`: Example configuration file for directory/file exclusions
- `pyproject.toml`: Project metadata, dependencies, and tool configuration

# Commands

- `python -m codebase_summarizer.main generate [PATH]`: Generate .semantic files for codebase directory
- `python -m codebase_summarizer.main generate --force`: Force regeneration of existing .semantic files
- `python -m codebase_summarizer.main generate --verbose`: Enable detailed logging output
- `python -m codebase_summarizer.main init`: Initialize .semanticsrc configuration file
- `python -m codebase_summarizer.main init --force`: Overwrite existing .semanticsrc file
- `python -m codebase_summarizer.main hook install --type pre-commit`: Install pre-commit hook for automatic generation
- `python debug_runner.py`: Run CLI locally during development
- `pip install -e .`: Install package in development mode
- `pip install semantic`: Install published package (if available)

## Development Commands

- `pytest`: Run test suite (if tests exist)
- `pytest --cov`: Run tests with coverage reporting
- `black .`: Format code using Black formatter (line-length 88)
- `isort .`: Sort and organize imports
- `flake8 .`: Lint code for style issues
- `mypy .`: Type check with strict typing enabled

# Code Style

- **Formatting**: Black formatter with 88 character line length
- **Import Organization**: isort with Black profile for consistent import sorting
- **Linting**: flake8 for code quality and style enforcement  
- **Type Checking**: mypy with strict typing (`disallow_untyped_defs = true`)
- **Target Version**: Python 3.10+ compatibility
- **Docstrings**: Google/Napoleon style docstrings with type hints
- **Naming Conventions**: 
  - snake_case for functions, variables, and modules
  - PascalCase for classes (e.g., `SemanticConfig`, `TraversalEngine`)
  - UPPER_CASE for constants
- **Import Style**: Absolute imports from project root, grouped by standard/third-party/local
- **Async Code**: Uses async/await pattern for LLM API calls with semaphore-based rate limiting

# Workflow

- **Development**: 
  - Use `debug_runner.py` for local testing and development
  - Install in development mode with `pip install -e .`
  - Set `OPENAI_API_KEY` environment variable for LLM features
  - Create `.env` file for local environment variables

- **Configuration**:
  - Run `semantic init` to create `.semanticsrc` configuration
  - Configure exclusion patterns for directories/files to ignore
  - Uses YAML format with optional PyYAML dependency

- **Testing**: 
  - Configure pytest in pyproject.toml for test discovery
  - Use pytest-cov for coverage reporting
  - Type checking with mypy ensures code quality

- **Code Quality**:
  - Black formatting enforced (88 chars line length)
  - isort for import organization 
  - flake8 linting for style compliance
  - mypy type checking with strict mode

- **Pre-commit Integration**:
  - Install hooks with `semantic hook install --type pre-commit`
  - Automatic .semantic file generation on git commits
  - Requires separate `pre-commit install` to complete setup

- **Deployment**:
  - Build with setuptools (`pip install build && python -m build`)
  - Entry point: `semantic` command maps to `codebase_summarizer.main:app`
  - Installable as standard Python package

## Project Purpose

This tool generates semantic summary files (`.semantic`) for codebases to help AI coding agents understand project structure and content efficiently without processing every individual file. Each directory gets a summary with required skillsets and API documentation including precise line numbers for navigation.
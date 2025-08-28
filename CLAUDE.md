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
- **Framework**: Typer CLI framework with asyncio for async operations
- **Runtime**: Python with asyncio runtime for concurrent processing
- **Build Tool**: setuptools with pyproject.toml configuration
- **Testing**: pytest with coverage (pytest-cov)
- **Package Manager**: pip with optional dependencies structure
- **LLM Integration**: OpenAI API client for semantic analysis
- **Database**: File-based storage (generates .semantic files)

# Project Structure

- `src/`: Primary source code location
- `src/codebase_summarizer/`: Main CLI application entry point
- `src/models/`: Pydantic data models for API structures and analysis results
- `src/services/`: Core business logic and service layer components
- `pyproject.toml`: Project configuration, dependencies, and tool settings
- `README.md`: Project documentation and usage instructions
- `debug_runner.py`: Development utility for debugging and testing

# Commands

- **Development**: `python -m src.codebase_summarizer.main` or `semantic` (after installation)
- **Build**: `pip install -e .` (editable installation for development)
- **Test**: `pytest` (requires dev dependencies: `pip install -e .[dev]`)
- **Lint**: `flake8 src/` (configured in pyproject.toml dev dependencies)
- **Format**: `black src/` and `isort src/` (configured with line-length 88)
- **Type Check**: `mypy src/` (configured for strict type checking)
- **Install**: `pip install -e .` (development) or `pip install semantic` (production)
- **CLI Usage**:
  - `semantic init` - Initialize .semanticsrc configuration
  - `semantic generate [path]` - Generate semantic summaries
  - `semantic generate --force` - Force regeneration of existing files
  - `semantic generate --verbose` - Enable detailed logging
  - `semantic hook install --type pre-commit` - Install pre-commit hook

# Code Style

- **Formatting**: Black auto-formatter (line-length: 88, target Python 3.10+)
- **Linting**: Flake8 for code quality and style enforcement
- **Type Checking**: MyPy with strict configuration (disallow_untyped_defs: true)
- **Import Style**: isort with "black" profile for consistent import organization
- **Naming Conventions**: 
  - Snake_case for functions, variables, and modules
  - PascalCase for classes (Pydantic models: ApiInfo, DirectoryAnalysis)
  - UPPER_CASE for constants
- **File Organization**: 
  - Services layer pattern (services/ directory)
  - Pydantic models in separate models/ directory
  - Single main CLI entry point in codebase_summarizer/

# Workflow

- **Development**: 
  - Clone repository and install with `pip install -e .[dev]`
  - Requires Python 3.10+ and OpenAI API key in .env file
  - Use asyncio for concurrent LLM operations (max 15 concurrent by default)
- **Testing**: 
  - Run `pytest` for test execution
  - Includes pytest-cov for coverage reporting
  - No existing test files found - tests would go in tests/ directory
- **Code Quality**: 
  - Use Black (line-length 88) and isort for formatting
  - Run flake8 for linting
  - MyPy for static type checking with strict configuration
- **Deployment**: 
  - Package as Python wheel with setuptools
  - CLI entry point: `semantic` command globally available after installation
  - Supports pre-commit hook integration for automated generation
- **Configuration**: 
  - Uses .semanticsrc YAML files for exclusion patterns
  - Supports .env files for environment variables (OpenAI API key)
  - Git integration with pre-commit hooks for automated semantic file generation

# Important Instructions

- **Core Functionality**: This tool generates `.semantic` files containing structured summaries of codebases for AI agents
- **LLM Integration**: Uses OpenAI API for semantic analysis - requires OPENAI_API_KEY environment variable
- **Async Processing**: Leverages asyncio with semaphore-based rate limiting for concurrent LLM operations
- **File Exclusions**: Respects .semanticsrc configuration files for excluding directories/files during analysis
- **Output Format**: Generates Markdown files with "Required Skillsets" and "APIs" sections including line numbers
- **CLI Design**: Built with Typer framework, includes subcommands for init, generate, and hook management
- **Pre-commit Integration**: Supports automatic regeneration via pre-commit hooks on code changes

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

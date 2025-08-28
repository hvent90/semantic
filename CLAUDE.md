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

- **Language**: Python 3.10+ 
- **Framework**: Typer CLI framework for command-line interface
- **Runtime**: Python 3.10, 3.11, 3.12
- **Build Tool**: setuptools with pyproject.toml configuration
- **Testing**: pytest with coverage support (pytest-cov)
- **Package Manager**: pip with optional dependencies for development
- **Database**: N/A (file-based tool)
- **LLM Integration**: OpenAI API for semantic analysis

## Key Dependencies

- `typer[all]>=0.9.0` - Modern CLI framework
- `pydantic>=2.0.0` - Data validation and modeling
- `openai>=1.0.0` - LLM API integration
- `pathspec>=0.11.0` - File pattern matching (gitignore-style)
- `python-dateutil>=2.8.0` - Date/time utilities

## Development Dependencies

- `black>=23.0.0` - Code formatting
- `isort>=5.12.0` - Import sorting
- `flake8>=6.0.0` - Code linting
- `mypy>=1.0.0` - Static type checking
- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Test coverage

# Project Structure

- `src/` - Primary source code location
- `src/codebase_summarizer/` - Main CLI application module
- `src/models/` - Pydantic data models for analysis results
- `src/services/` - Core business logic and services
- `pyproject.toml` - Package configuration and dependencies
- `.semanticsrc` - Configuration file for exclusion patterns
- `debug_runner.py` - Development utility for debugging

## Key Files

- `src/codebase_summarizer/main.py` - CLI entry point and command definitions
- `src/models/data_models.py` - Data models for analysis results
- `src/services/analysis_orchestrator.py` - Coordinates analysis workflow
- `src/services/llm_client.py` - OpenAI API integration
- `src/services/config.py` - Configuration file handling
- `src/services/traversal_engine.py` - Directory traversal logic
- `src/services/vcs_interface.py` - Version control integration

# Commands

## Installation Commands
```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## Core Commands
- **Development**: `python debug_runner.py` - Run tool in debug mode
- **CLI Usage**: `semantic generate` - Generate .semantic files for codebase
- **Initialize**: `semantic init` - Create .semanticsrc configuration file
- **Hook Install**: `semantic hook install --type pre-commit` - Install Git pre-commit hook
- **Test**: `pytest` - Run test suite with pytest
- **Coverage**: `pytest --cov=src` - Run tests with coverage report

## Code Quality Commands
- **Format**: `black src/` - Format code with Black
- **Sort Imports**: `isort src/` - Sort imports
- **Lint**: `flake8 src/` - Check code style
- **Type Check**: `mypy src/` - Static type checking

## CLI Options
- `semantic generate --force` - Force regeneration of existing .semantic files
- `semantic generate --verbose` - Enable detailed logging
- `semantic generate /path/to/codebase` - Analyze specific directory

# Code Style

- **Formatting**: Black formatter with 88 character line length
- **Import Style**: isort with "black" profile for compatibility
- **Type Checking**: mypy with strict settings (disallow_untyped_defs=true)
- **Linting**: flake8 for code quality checks
- **Target Version**: Python 3.10+ syntax and features

## Formatting Configuration
```toml
[tool.black]
line-length = 88
target-version = ['py310']

[tool.isort] 
profile = "black"
src_paths = ["src", "tests"]
```

## Type Checking Configuration
```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## Naming Conventions
- Classes: PascalCase (e.g., `AnalysisOrchestrator`, `SemanticConfig`)
- Functions/methods: snake_case (e.g., `generate_semantic_files`, `load_config`)
- Constants: UPPER_SNAKE_CASE
- Files/modules: snake_case (e.g., `data_models.py`, `llm_client.py`)

# Workflow

## Development Environment
1. Clone repository: `git clone https://github.com/hvent90/semantic`
2. Install in development mode: `pip install -e ".[dev]"`
3. Run tests: `pytest`
4. Use debug runner for testing: `python debug_runner.py`

## Code Quality Workflow
1. **Format**: Run `black src/` before committing
2. **Import sorting**: Run `isort src/` to organize imports
3. **Linting**: Check with `flake8 src/` for style issues
4. **Type checking**: Verify types with `mypy src/`
5. **Testing**: Ensure `pytest` passes with good coverage

## Git Integration
- **Hook Support**: Install pre-commit hook with `semantic hook install --type pre-commit`
- **Pre-commit Integration**: Tool integrates with pre-commit framework
- **File Patterns**: Hooks trigger on source code changes (.py, .js, .ts, etc.)

## Deployment Process
- **Distribution**: Built using setuptools with pyproject.toml
- **CLI Entry**: Installed as `semantic` command via `project.scripts`
- **Package Structure**: Source code in `src/` directory structure
- **Dependencies**: Core and optional dependencies separated for flexibility

## Release Process
- **Versioning**: Semantic versioning in pyproject.toml
- **Build**: Uses setuptools build backend
- **Distribution**: Packaged for PyPI distribution
- **Installation**: Supports both regular and editable installation modes

# Important Instructions

- **File Creation**: NEVER create files unless absolutely necessary for achieving your goal
- **File Editing**: ALWAYS prefer editing an existing file to creating a new one  
- **Documentation**: NEVER proactively create documentation files (*.md) or README files unless explicitly requested
- **Scope**: Do what has been asked; nothing more, nothing less

## Tool-Specific Guidelines

- This is a CLI tool for generating semantic summaries of codebases
- The tool creates `.semantic` files containing structured overviews for AI agents
- Uses OpenAI API for LLM-powered analysis and summarization
- Supports configuration via `.semanticsrc` files for excluding directories/files
- Integrates with Git workflows through pre-commit hooks
- Focus on token-efficient summaries for AI coding agents

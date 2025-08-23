# Semantic

A CLI tool that generates semantic summaries of codebases for AI coding agents.

## Overview

Semantic creates a "semantic layer" over software codebases, enabling AI coding agents to gain high-level understanding of project structure and content without processing every individual file. The tool generates concise, machine-readable summary files (`.semantic`) within each directory, providing essential context in a token-efficient manner.

## Problem Statement

Current AI coding agents face token limits and inefficiency when they must ingest large amounts of code into their context window to perform tasks. Semantic solves this by creating structured, high-signal summaries that allow AI agents to navigate and comprehend entire codebases quickly and effectively.

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd semantic

# Install dependencies
pip install -e .

# Or install directly
pip install semantic
```

## Quick Start

### Initialize Configuration

```bash
# Create a .semanticsrc configuration file
semantic init
```

### Generate Summaries

```bash
# Generate .semantic files for current directory
semantic generate

# Generate for specific path
semantic generate /path/to/codebase

# Force regeneration of existing files
semantic generate --force

# Enable verbose logging
semantic generate --verbose
```

### Install Git Hooks

```bash
# Install pre-commit hook for automatic generation
semantic hook install --type pre-commit

# Complete the installation
pre-commit install
```

## Configuration

The `.semanticsrc` file allows you to customize which files and directories to exclude:

```yaml
# .semanticsrc Example
exclude:
  - node_modules/
  - .venv/
  - venv/
  - '*.log'
  - dist/
  - build/
  - __pycache__/
  - .pytest_cache/
  - .git/
  - .DS_Store
```

## Output Format

Semantic generates `.semantic` files in each directory with the following structure:

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

Each `.semantic` file includes:
- **Required Skillsets**: Technologies and expertise needed to work with the directory
- **APIs**: Functions, classes, and interfaces with semantic descriptions
- **Line Numbers**: Precise location references for navigation for the AI agent to read a minimal amount from the desired file

## Requirements

- Python 3.10+
- OpenAI API access (for LLM integration)
- Git (for version control integration)

### Dependencies

- `typer[all]>=0.9.0` - CLI framework
- `pydantic>=2.0.0` - Data validation
- `openai>=1.0.0` - LLM integration
- `pathspec>=0.11.0` - File pattern matching
- `python-dateutil>=2.8.0` - Date/time utilities

### Optional Dependencies

- `PyYAML` - Required for pre-commit hook installation
- `pre-commit` - For automated hook-based generation

## License

MIT License

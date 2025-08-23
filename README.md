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
- **Line Numbers**: Precise location references for navigation
- **Semantic Descriptions**: AI-generated summaries of functionality

## Architecture

The system is built with several key components:

- **TraversalEngine**: Handles directory traversal and file discovery
- **AnalysisOrchestrator**: Orchestrates the analysis workflow
- **SummaryGenerator**: Creates structured `.semantic` files
- **LLMClient**: Interfaces with language models for semantic analysis
- **VcsInterface**: Integrates with version control systems
- **SemanticConfig**: Manages configuration and exclusion patterns

## Use Cases

### For AI Coding Agents
- Quickly understand codebase structure without reading every file
- Identify relevant files, APIs, and required expertise for tasks
- Navigate efficiently while staying within operational context limits

### For Developers
- Integrate into existing development workflows (IDE, Version Control, CI/CD)
- Ensure generated summaries are accurate and up-to-date
- Improve effectiveness of AI coding assistant tools

### For DevOps Engineers
- Configure automatic generation in CI/CD pipelines
- Maintain synchronized summaries with latest code changes
- Monitor and track LLM usage costs

## Performance

- **Large Codebases**: Capable of processing repositories with 10,000+ files
- **Medium Repositories**: Scans completed in under 5 minutes on typical CI/CD runners
- **Directory Processing**: Individual directories (up to 100 files) processed in under 30 seconds
- **Concurrent Processing**: Configurable parallelism with rate limiting (default: 15 concurrent operations)

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

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black .
isort .

# Type checking
mypy src/

# Linting
flake8 src/
```

## Future Roadmap

- Plugin-based architecture for language extension
- Advanced metadata analysis (dependencies, performance metrics)
- Full IDE integration with user interface
- Enhanced framework-specific summarization
- Success metrics and analytics framework

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass and code is properly formatted
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues, feature requests, or questions, please use the GitHub issue tracker.

# Semantic

A CLI tool that generates semantic summaries of codebases for AI coding agents.

## Overview

Semantic creates a "semantic layer" over software codebases, enabling AI coding agents to gain high-level understanding of project structure and content without processing every individual file. The tool generates concise, machine-readable summary files (`agents.md` or `claude.md`) within each directory, providing essential context in a token-efficient manner.

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
# Generate agents.md files for current directory (default)
semantic generate

# Generate claude.md files
semantic generate --output-format=claude

# Generate for specific path
semantic generate /path/to/codebase

# Force regeneration of existing files
semantic generate --force

# Enable verbose logging
semantic generate --verbose

# NEW: Provider auto-inference - no need to specify --provider!
semantic generate --model gpt-4           # infers openai
semantic generate --model sonnet          # infers anthropic
semantic generate --model gemini-2.5-pro  # infers google
```

### Model Selection

#### Supported Providers

The tool supports three AI model providers:

##### OpenAI
- **Default Model**: `gpt-5-nano`
- **Available Models**:
  - `gpt-4`
  - `gpt-4-turbo`
  - `gpt-4o`
  - `gpt-4o-mini`
  - `gpt-3.5-turbo`
  - `gpt-5`
  - `gpt-5-mini`
  - `gpt-5-nano`

##### Anthropic
- **Default Model**: `claude-sonnet-4-20250514`
- **Available Models**:
  - `claude-sonnet-4-20250514` (alias: `sonnet`)
  - `claude-opus-4-1-20250805` (alias: `opus`)

##### Google
- **Default Model**: `gemini-2.5-flash`
- **Available Models**:
  - `gemini-2.5-pro`
  - `gemini-2.5-flash`

#### Usage Examples

```bash
# Use default provider (Anthropic) with default model
semantic generate

# Specify provider (uses provider's default model)
semantic generate --provider openai
semantic generate --provider google
semantic generate --provider anthropic

# NEW: Simplified usage with automatic provider inference
semantic generate --model gpt-4           # infers openai
semantic generate --model sonnet          # infers anthropic
semantic generate --model gemini-2.5-pro  # infers google
```

#### Configuration File

You can set default provider and model in `.semanticsrc`:

```yaml
llm:
  provider: anthropic    # openai, anthropic, google
  model: sonnet         # optional, uses provider default if not specified
```

#### Environment Setup

Set the appropriate API key for your chosen provider:

```bash
# For OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# For Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# For Google
export GOOGLE_API_KEY="your-google-api-key"
```

### Install Git Hooks

```bash
# Install pre-commit hook for automatic generation
semantic hook install --type pre-commit

# Complete the installation
pre-commit install
```

## Configuration

The `.semanticsrc` file allows you to customize the output format, LLM provider/model, and which files and directories to exclude:

```yaml
# .semanticsrc Example
# Defines the output file format for generated summaries
output_format: agents  # Options: agents, claude

# LLM configuration
llm:
  provider: anthropic    # openai, anthropic, google
  model: sonnet         # optional, uses provider default if not specified

# Defines which directories/files to explicitly ignore during traversal
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

### Supported Model Patterns

#### OpenAI Models
- `gpt-5`
- `gpt-5-micro`
- `gpt-5-nano`

#### Anthropic Models
- `claude-sonnet-4-20250514` (alias: `sonnet`)
- `claude-opus-4-1-20250805` (alias: `opus`)

#### Google Models
- `gemini-2.5-pro`
- `gemini-2.5-flash`

## Output Format

Semantic generates summary files (`agents.md` or `claude.md`) in each directory with the following structure:

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

Each summary file includes:
- **Required Skillsets**: Technologies and expertise needed to work with the directory
- **APIs**: Functions, classes, and interfaces with semantic descriptions
- **Line Numbers**: Precise location references for navigation for the AI agent to read a minimal amount from the desired file

## Requirements

- Python 3.10+
- API access for your chosen LLM provider (OpenAI, Anthropic, or Google)
- Git (for version control integration)

### Dependencies

- `typer[all]>=0.9.0` - CLI framework
- `pydantic>=2.0.0` - Data validation
- `openai>=1.0.0` - OpenAI API integration
- `pathspec>=0.11.0` - File pattern matching
- `python-dateutil>=2.8.0` - Date/time utilities

### Optional Dependencies

- `anthropic>=0.23.0` - Anthropic Claude API integration
- `google-generativeai>=0.3.0` - Google Gemini API integration
- `PyYAML` - Required for configuration file and pre-commit hook support
- `pre-commit` - For automated hook-based generation

### Examples

```bash
# Generate agents.md files (new default)
semantic generate

# Generate claude.md files
semantic generate --output-format=claude

# Set project default in .semanticsrc
echo "output_format: claude" >> .semanticsrc
semantic generate
```

## License

MIT License

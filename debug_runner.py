#!/usr/bin/env python3
"""Debug runner for semantic CLI."""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the main app
from codebase_summarizer.main import app

if __name__ == "__main__":
    app()
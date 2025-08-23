"""Python language parser for extracting APIs and skillsets."""

import ast
import re
from pathlib import Path
from typing import List, Set
from .language_parser_interface import LanguageParserInterface
from models.data_models import AnalysisFragment, ApiInfo
from services.llm_client import llm_client


class PythonParser(LanguageParserInterface):
    """
    Python language parser that extracts APIs and identifies skillsets
    from Python source files using the AST module.
    """
    
    def __init__(self):
        """Initialize the Python parser."""
        self.supported_extensions = {'.py', '.pyi'}
        self.framework_patterns = {
            'Django': [
                r'from django\.',
                r'import django',
                r'models\.Model',
                r'@admin\.register',
                r'HttpResponse',
                r'render\(',
            ],
            'Flask': [
                r'from flask',
                r'import flask',
                r'@app\.route',
                r'Flask\(__name__\)',
            ],
            'FastAPI': [
                r'from fastapi',
                r'import fastapi',
                r'@app\.(get|post|put|delete)',
                r'FastAPI\(',
                r'APIRouter',
            ],
            'Pandas': [
                r'import pandas',
                r'from pandas',
                r'pd\.',
                r'DataFrame',
                r'\.read_csv',
            ],
            'NumPy': [
                r'import numpy',
                r'from numpy',
                r'np\.',
                r'ndarray',
            ],
            'SQLAlchemy': [
                r'from sqlalchemy',
                r'import sqlalchemy',
                r'declarative_base',
                r'Column\(',
                r'relationship\(',
            ],
            'Pytest': [
                r'import pytest',
                r'from pytest',
                r'@pytest\.',
                r'def test_',
            ],
            'Asyncio': [
                r'import asyncio',
                r'async def',
                r'await ',
                r'asyncio\.',
            ],
            'Requests': [
                r'import requests',
                r'requests\.',
                r'\.get\(',
                r'\.post\(',
            ],
            'Pydantic': [
                r'from pydantic',
                r'import pydantic',
                r'BaseModel',
                r'Field\(',
            ],
            'Typer': [
                r'import typer',
                r'from typer',
                r'typer\.Typer',
                r'@app\.command',
            ]
        }
    
    def supports_extension(self, ext: str) -> bool:
        """Check if this parser supports the given file extension."""
        return ext.lower() in self.supported_extensions
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return list(self.supported_extensions)
    
    def parse(self, file_content: str, file_path: str) -> AnalysisFragment:
        """
        Parse Python file and extract APIs and skillsets.
        
        Args:
            file_content: Raw content of the Python file
            file_path: Path to the file being analyzed
            
        Returns:
            AnalysisFragment with extracted APIs and skillsets
        """
        try:
            tree = ast.parse(file_content)
            apis = self._extract_apis(tree, file_path, file_content.split('\n'))
            skillsets = self._identify_skillsets(file_content)
            
            return AnalysisFragment(
                file_extension=Path(file_path).suffix,
                apis=apis,
                skillsets=skillsets,
                source_file=file_path
            )
            
        except SyntaxError as e:
            # Handle malformed Python files gracefully
            return AnalysisFragment(
                file_extension=Path(file_path).suffix,
                apis=[],
                skillsets=['Python'],  # At least we know it's Python
                source_file=file_path
            )
    
    def _extract_apis(self, tree: ast.AST, file_path: str, lines: List[str]) -> List[ApiInfo]:
        """Extract function and class definitions from the AST."""
        apis = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                api_info = self._create_function_api_info(node, file_path, lines)
                apis.append(api_info)
                
            elif isinstance(node, ast.AsyncFunctionDef):
                api_info = self._create_async_function_api_info(node, file_path, lines)
                apis.append(api_info)
                
            elif isinstance(node, ast.ClassDef):
                api_info = self._create_class_api_info(node, file_path, lines)
                apis.append(api_info)
        
        return apis
    
    def _create_function_api_info(self, node: ast.FunctionDef, file_path: str, lines: List[str]) -> ApiInfo:
        """Create ApiInfo for a regular function."""
        semantic_desc = self._generate_semantic_description(node, lines)
        end_line = self._find_end_line(node, lines)
        
        return ApiInfo(
            name=node.name,
            semantic_description=semantic_desc,
            source_file=file_path,
            start_line=node.lineno,
            end_line=end_line
        )
    
    def _create_async_function_api_info(self, node: ast.AsyncFunctionDef, file_path: str, lines: List[str]) -> ApiInfo:
        """Create ApiInfo for an async function."""
        semantic_desc = self._generate_async_semantic_description(node, lines)
        end_line = self._find_end_line(node, lines)
        
        return ApiInfo(
            name=f"async {node.name}",
            semantic_description=semantic_desc,
            source_file=file_path,
            start_line=node.lineno,
            end_line=end_line
        )
    
    def _create_class_api_info(self, node: ast.ClassDef, file_path: str, lines: List[str]) -> ApiInfo:
        """Create ApiInfo for a class definition."""
        semantic_desc = self._generate_class_semantic_description(node, lines)
        end_line = self._find_end_line(node, lines)
        
        return ApiInfo(
            name=f"class {node.name}",
            semantic_description=semantic_desc,
            source_file=file_path,
            start_line=node.lineno,
            end_line=end_line
        )
    
    def _generate_semantic_description(self, node: ast.FunctionDef, lines: List[str]) -> str:
        """Generate semantic description for a function using LLM or fallback methods."""
        # Try to extract docstring first as it's authoritative
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Str)):
            docstring = node.body[0].value.s
            # Return first line of docstring, cleaned up
            first_line = docstring.split('\n')[0].strip()
            if first_line:
                return first_line
        
        # Try to use LLM for semantic description
        if llm_client.is_available():
            api_code = self._extract_function_code(node, lines)
            if api_code:
                llm_description = llm_client.generate_api_description(
                    api_code, node.name, "python_file"
                )
                if llm_description and llm_description != f"Function {node.name} in python_file":
                    return llm_description
        
        # Fallback: Generate description based on function name and structure
        name_desc = self._describe_function_name(node.name)
        
        # Check for common patterns
        if node.name.startswith('test_'):
            return f"Test function for {node.name[5:].replace('_', ' ')}"
        elif node.name.startswith('get_'):
            return f"Retrieves {node.name[4:].replace('_', ' ')}"
        elif node.name.startswith('set_'):
            return f"Sets {node.name[4:].replace('_', ' ')}"
        elif node.name.startswith('create_'):
            return f"Creates {node.name[7:].replace('_', ' ')}"
        elif node.name.startswith('delete_'):
            return f"Deletes {node.name[7:].replace('_', ' ')}"
        elif node.name.startswith('update_'):
            return f"Updates {node.name[7:].replace('_', ' ')}"
        elif node.name == '__init__':
            return "Constructor method for class initialization"
        elif node.name.startswith('__') and node.name.endswith('__'):
            return f"Special method {node.name}"
        
        return name_desc
    
    def _generate_async_semantic_description(self, node: ast.AsyncFunctionDef, lines: List[str]) -> str:
        """Generate semantic description for an async function using LLM or fallback methods."""
        # Try to extract docstring first as it's authoritative
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Str)):
            docstring = node.body[0].value.s
            # Return first line of docstring, cleaned up
            first_line = docstring.split('\n')[0].strip()
            if first_line:
                return first_line
        
        # Try to use LLM for semantic description
        if llm_client.is_available():
            api_code = self._extract_async_function_code(node, lines)
            if api_code:
                llm_description = llm_client.generate_api_description(
                    api_code, f"async {node.name}", "python_file"
                )
                if llm_description and llm_description != f"Function async {node.name} in python_file":
                    return llm_description
        
        # Fallback: Generate description based on function name and structure
        return f"Async function that handles {node.name.replace('_', ' ').lower()}"
    
    def _generate_class_semantic_description(self, node: ast.ClassDef, lines: List[str]) -> str:
        """Generate semantic description for a class using LLM or fallback methods."""
        # Try to extract docstring first as it's authoritative
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Str)):
            docstring = node.body[0].value.s
            first_line = docstring.split('\n')[0].strip()
            if first_line:
                return first_line
        
        # Try to use LLM for semantic description
        if llm_client.is_available():
            api_code = self._extract_class_code(node, lines)
            if api_code:
                llm_description = llm_client.generate_api_description(
                    api_code, f"class {node.name}", "python_file"
                )
                if llm_description and llm_description != f"Function class {node.name} in python_file":
                    return llm_description
        
        # Fallback: Check for common class patterns
        if any(isinstance(base, ast.Name) and 'Exception' in base.id for base in node.bases if hasattr(base, 'id')):
            return f"Custom exception class"
        elif any(isinstance(base, ast.Name) and base.id in ['BaseModel', 'Model'] for base in node.bases if hasattr(base, 'id')):
            return f"Data model class"
        elif node.name.endswith('Test'):
            return f"Test class for {node.name[:-4]}"
        elif node.name.endswith('Service'):
            return f"Service class providing business logic"
        elif node.name.endswith('Manager'):
            return f"Manager class for handling operations"
        
        return f"Class defining {node.name.replace('_', ' ').lower()} functionality"
    
    def _extract_function_code(self, node: ast.FunctionDef, lines: List[str]) -> str:
        """Extract the complete code for a function."""
        try:
            start_line = node.lineno - 1  # Convert to 0-based indexing
            end_line = self._find_end_line(node, lines)
            
            if start_line < len(lines) and end_line <= len(lines):
                function_lines = lines[start_line:end_line]
                return '\n'.join(function_lines)
        except Exception:
            pass
        return ""
    
    def _extract_async_function_code(self, node: ast.AsyncFunctionDef, lines: List[str]) -> str:
        """Extract the complete code for an async function."""
        try:
            start_line = node.lineno - 1  # Convert to 0-based indexing
            end_line = self._find_end_line(node, lines)
            
            if start_line < len(lines) and end_line <= len(lines):
                function_lines = lines[start_line:end_line]
                return '\n'.join(function_lines)
        except Exception:
            pass
        return ""
    
    def _extract_class_code(self, node: ast.ClassDef, lines: List[str]) -> str:
        """Extract the complete code for a class (or first few methods if too long)."""
        try:
            start_line = node.lineno - 1  # Convert to 0-based indexing
            end_line = self._find_end_line(node, lines)
            
            if start_line < len(lines) and end_line <= len(lines):
                class_lines = lines[start_line:end_line]
                class_code = '\n'.join(class_lines)
                
                # If class is very long, truncate to first 50 lines for LLM analysis
                if len(class_lines) > 50:
                    truncated_lines = class_lines[:50]
                    class_code = '\n'.join(truncated_lines) + '\n    # ... (truncated)'
                
                return class_code
        except Exception:
            pass
        return ""
    
    def _describe_function_name(self, name: str) -> str:
        """Convert function name to human readable description."""
        # Convert snake_case to space-separated words
        words = name.replace('_', ' ').lower()
        return f"Function that handles {words}"
    
    def _find_end_line(self, node: ast.AST, lines: List[str]) -> int:
        """Find the end line of a node by looking for the next node or end of indentation."""
        # This is a simplified approach - find the last line with content at the same or deeper indentation
        start_line = node.lineno - 1  # Convert to 0-based indexing
        if start_line >= len(lines):
            return node.lineno
            
        # Find the indentation level of the definition line
        def_line = lines[start_line]
        base_indent = len(def_line) - len(def_line.lstrip())
        
        # Look for the last line that's part of this definition
        current_line = start_line + 1
        last_content_line = start_line
        
        while current_line < len(lines):
            line = lines[current_line]
            
            # Skip empty lines
            if not line.strip():
                current_line += 1
                continue
                
            # Calculate current line's indentation
            current_indent = len(line) - len(line.lstrip())
            
            # If we've returned to the same or less indentation as the definition,
            # we've reached the end of this block
            if current_indent <= base_indent:
                break
                
            last_content_line = current_line
            current_line += 1
        
        return last_content_line + 1  # Convert back to 1-based indexing
    
    def _identify_skillsets(self, file_content: str) -> List[str]:
        """Identify Python frameworks and libraries used in the code."""
        skillsets = {'Python'}  # Always include Python as base skillset
        
        for framework, patterns in self.framework_patterns.items():
            for pattern in patterns:
                if re.search(pattern, file_content, re.MULTILINE):
                    skillsets.add(framework)
                    break  # Found one match, no need to check other patterns
        
        return sorted(list(skillsets))
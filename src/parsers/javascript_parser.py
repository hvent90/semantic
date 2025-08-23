"""JavaScript/TypeScript language parser for extracting APIs and skillsets."""

import re
from pathlib import Path
from typing import List, Set
from .language_parser_interface import LanguageParserInterface
from models.data_models import AnalysisFragment, ApiInfo
from services.llm_client import llm_client


class JavaScriptParser(LanguageParserInterface):
    """
    JavaScript/TypeScript language parser that extracts APIs and identifies skillsets
    from JavaScript/TypeScript source files using regex patterns.
    """
    
    def __init__(self):
        """Initialize the JavaScript parser."""
        self.supported_extensions = {'.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'}
        self.framework_patterns = {
            'React': [
                r'import.*from [\'"]react[\'"]',
                r'React\.',
                r'useState',
                r'useEffect',
                r'Component',
                r'JSX\.',
                r'<[A-Z]\w*',  # JSX components
            ],
            'Vue': [
                r'import.*from [\'"]vue[\'"]',
                r'Vue\.',
                r'@Component',
                r'v-if',
                r'v-for',
            ],
            'Angular': [
                r'@angular/',
                r'@Component',
                r'@Injectable',
                r'@NgModule',
                r'Observable',
            ],
            'Express': [
                r'import.*express',
                r'require\([\'"]express[\'"]',
                r'app\.(get|post|put|delete)',
                r'router\.',
            ],
            'Node.js': [
                r'require\(',
                r'module\.exports',
                r'process\.',
                r'__dirname',
                r'__filename',
            ],
            'TypeScript': [
                r'interface\s+\w+',
                r'type\s+\w+\s*=',
                r':\s*\w+(\[\])?',
                r'as\s+\w+',
                r'implements\s+\w+',
            ],
            'Jest': [
                r'describe\(',
                r'it\(',
                r'test\(',
                r'expect\(',
                r'jest\.',
            ],
            'Webpack': [
                r'webpack',
                r'module\.exports\s*=\s*{',
                r'entry:',
                r'output:',
            ],
            'GraphQL': [
                r'graphql',
                r'gql`',
                r'Query',
                r'Mutation',
                r'resolver',
            ],
            'Redux': [
                r'redux',
                r'useSelector',
                r'useDispatch',
                r'createStore',
                r'reducer',
            ],
            'Next.js': [
                r'next/',
                r'getStaticProps',
                r'getServerSideProps',
                r'useRouter',
            ],
            'Lodash': [
                r'lodash',
                r'_\.',
                r'import.*_.*from',
            ],
            'Axios': [
                r'axios',
                r'\.get\(',
                r'\.post\(',
                r'\.put\(',
                r'\.delete\(',
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
        Parse JavaScript/TypeScript file and extract APIs and skillsets.
        
        Args:
            file_content: Raw content of the file
            file_path: Path to the file being analyzed
            
        Returns:
            AnalysisFragment with extracted APIs and skillsets
        """
        apis = self._extract_apis(file_content, file_path)
        skillsets = self._identify_skillsets(file_content, file_path)
        
        return AnalysisFragment(
            file_extension=Path(file_path).suffix,
            apis=apis,
            skillsets=skillsets,
            source_file=file_path
        )
    
    def _extract_apis(self, content: str, file_path: str) -> List[ApiInfo]:
        """Extract function and class definitions from JavaScript/TypeScript code."""
        apis = []
        lines = content.split('\n')
        
        # Pattern for function declarations
        function_patterns = [
            r'^(\s*)function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(',  # function declarations
            r'^(\s*)const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>', # arrow functions
            r'^(\s*)(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(',  # exported functions
            r'^(\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:\s*(?:async\s+)?\([^)]*\)\s*=>', # method definitions
            r'^(\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)\s*{', # method definitions
        ]
        
        # Pattern for class declarations
        class_pattern = r'^(\s*)(?:export\s+)?class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)'
        
        # Pattern for interface/type declarations (TypeScript)
        interface_patterns = [
            r'^(\s*)(?:export\s+)?interface\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
            r'^(\s*)(?:export\s+)?type\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=',
        ]
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('//') or line_stripped.startswith('/*'):
                continue
            
            # Check for functions
            for pattern in function_patterns:
                match = re.search(pattern, line)
                if match:
                    func_name = match.group(2)
                    description = self._generate_function_description(func_name, line, lines, i)
                    end_line = self._find_function_end_line(lines, i-1)
                    
                    apis.append(ApiInfo(
                        name=func_name,
                        semantic_description=description,
                        source_file=file_path,
                        start_line=i,
                        end_line=end_line
                    ))
                    break
            
            # Check for classes
            match = re.search(class_pattern, line)
            if match:
                class_name = match.group(2)
                description = self._generate_class_description(class_name, line)
                end_line = self._find_class_end_line(lines, i-1)
                
                apis.append(ApiInfo(
                    name=f"class {class_name}",
                    semantic_description=description,
                    source_file=file_path,
                    start_line=i,
                    end_line=end_line
                ))
            
            # Check for interfaces/types (TypeScript)
            for pattern in interface_patterns:
                match = re.search(pattern, line)
                if match:
                    type_name = match.group(2)
                    description = f"Type definition for {type_name}"
                    end_line = self._find_type_end_line(lines, i-1)
                    
                    apis.append(ApiInfo(
                        name=f"type {type_name}",
                        semantic_description=description,
                        source_file=file_path,
                        start_line=i,
                        end_line=end_line
                    ))
                    break
        
        return apis
    
    def _generate_function_description(self, func_name: str, line: str, lines: List[str], line_num: int) -> str:
        """Generate a semantic description for a function."""
        # Check for JSDoc comment above the function
        if line_num > 1:
            prev_lines = lines[max(0, line_num-5):line_num-1]
            for prev_line in reversed(prev_lines):
                if '* ' in prev_line and not prev_line.strip().startswith('//'):
                    # Extract description from JSDoc
                    desc_match = re.search(r'\*\s*(.+)', prev_line)
                    if desc_match and not desc_match.group(1).startswith('@'):
                        return desc_match.group(1).strip()
        
        # Pattern-based descriptions
        if 'async' in line:
            return f"Async function that handles {func_name.replace('_', ' ').lower()}"
        elif func_name.startswith('get'):
            return f"Retrieves {func_name[3:].replace('_', ' ').lower()}"
        elif func_name.startswith('set'):
            return f"Sets {func_name[3:].replace('_', ' ').lower()}"
        elif func_name.startswith('create'):
            return f"Creates {func_name[6:].replace('_', ' ').lower()}"
        elif func_name.startswith('delete') or func_name.startswith('remove'):
            prefix_len = 6 if func_name.startswith('delete') else 6
            return f"Deletes {func_name[prefix_len:].replace('_', ' ').lower()}"
        elif func_name.startswith('update'):
            return f"Updates {func_name[6:].replace('_', ' ').lower()}"
        elif func_name.startswith('handle'):
            return f"Handles {func_name[6:].replace('_', ' ').lower()}"
        elif func_name.startswith('on'):
            return f"Event handler for {func_name[2:].replace('_', ' ').lower()}"
        elif func_name.endswith('Handler'):
            return f"Handler function for {func_name[:-7].replace('_', ' ').lower()}"
        elif func_name.endswith('Callback'):
            return f"Callback function for {func_name[:-8].replace('_', ' ').lower()}"
        
        return f"Function that handles {func_name.replace('_', ' ').lower()}"
    
    def _generate_class_description(self, class_name: str, line: str) -> str:
        """Generate a semantic description for a class."""
        if 'extends' in line:
            return f"Class extending functionality for {class_name.lower()}"
        elif class_name.endswith('Component'):
            return f"React component for {class_name[:-9].lower()}"
        elif class_name.endswith('Service'):
            return f"Service class providing business logic"
        elif class_name.endswith('Controller'):
            return f"Controller class handling requests"
        elif class_name.endswith('Model'):
            return f"Data model class for {class_name[:-5].lower()}"
        elif class_name.endswith('Manager'):
            return f"Manager class for handling operations"
        elif class_name.endswith('Helper') or class_name.endswith('Util'):
            return f"Utility class providing helper functions"
        
        return f"Class defining {class_name.lower()} functionality"
    
    def _find_function_end_line(self, lines: List[str], start_index: int) -> int:
        """Find the end line of a function by tracking braces."""
        brace_count = 0
        found_opening = False
        
        for i in range(start_index, len(lines)):
            line = lines[i]
            
            # Count braces
            for char in line:
                if char == '{':
                    brace_count += 1
                    found_opening = True
                elif char == '}':
                    brace_count -= 1
                    
                    # If we close all braces and found opening, we're done
                    if found_opening and brace_count == 0:
                        return i + 1
            
            # For arrow functions without braces, look for semicolon or return
            if not found_opening and ('=>' in line):
                # Simple arrow function without braces
                if line.rstrip().endswith(';') or line.rstrip().endswith(','):
                    return i + 1
        
        return start_index + 1  # Fallback
    
    def _find_class_end_line(self, lines: List[str], start_index: int) -> int:
        """Find the end line of a class by tracking braces."""
        return self._find_function_end_line(lines, start_index)  # Same logic
    
    def _find_type_end_line(self, lines: List[str], start_index: int) -> int:
        """Find the end line of a type/interface definition."""
        for i in range(start_index, len(lines)):
            line = lines[i].strip()
            if line.endswith(';') or (line.endswith('}') and '{' in lines[start_index]):
                return i + 1
        return start_index + 1
    
    def _identify_skillsets(self, file_content: str, file_path: str) -> List[str]:
        """Identify JavaScript/TypeScript frameworks and libraries used in the code."""
        skillsets = set()
        
        # Add base language skillset
        if file_path.endswith(('.ts', '.tsx')):
            skillsets.add('TypeScript')
        skillsets.add('JavaScript')
        
        # Check for framework patterns
        for framework, patterns in self.framework_patterns.items():
            for pattern in patterns:
                if re.search(pattern, file_content, re.MULTILINE | re.IGNORECASE):
                    skillsets.add(framework)
                    break
        
        return sorted(list(skillsets))
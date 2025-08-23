"""Summary generator for creating agents.md files."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List
from models.data_models import DirectoryAnalysis, AgentsMdContent, TocEntry


class SummaryGenerator:
    """
    Generates structured agents.md files from DirectoryAnalysis data.
    Handles Table of Contents calculation and proper markdown formatting.
    """
    
    def __init__(self):
        """Initialize the summary generator."""
        pass
        
    def generate_agents_md_content(self, analysis: DirectoryAnalysis, metadata: Dict[str, str]) -> AgentsMdContent:
        """
        Generate the structured content for an agents.md file.
        
        Args:
            analysis: The directory analysis data
            metadata: Version control metadata (commit_hash, etc.)
            
        Returns:
            AgentsMdContent object with structured data
        """
        # Generate summary strings for each section
        file_types_summary = self._generate_file_types_summary(analysis.file_types)
        skillsets_summary = self._generate_skillsets_summary(analysis.required_skillsets)
        apis_summary = self._generate_apis_summary(analysis.apis)
        
        # Calculate table of contents with line numbers
        toc_entries, toc_lines = self._calculate_table_of_contents(
            file_types_summary, skillsets_summary, apis_summary
        )
        
        return AgentsMdContent(
            toc_lines=toc_lines,
            table_of_contents=toc_entries,
            metadata=metadata,
            file_types_summary=file_types_summary,
            required_skillsets_summary=skillsets_summary,
            apis_summary=apis_summary
        )
        
    def serialize_to_markdown(self, content: AgentsMdContent) -> str:
        """
        Serialize the AgentsMdContent to a markdown string.
        
        Args:
            content: The structured content to serialize
            
        Returns:
            Complete markdown string for the agents.md file
        """
        lines = []
        
        # TOC header
        toc_end_line = 3 + content.toc_lines  # 3 for header lines + TOC content
        lines.append(f"TABLE-OF-CONTENTS: lines 3-{toc_end_line}")
        lines.append("")
        lines.append("[TOC]")
        
        # TOC entries
        for entry in content.table_of_contents:
            lines.append(f"- {entry.section_name}: {entry.start_line}-{entry.end_line}")
            
        lines.append("[/TOC]")
        lines.append("")
        
        # Metadata section
        lines.append("## Metadata")
        for key, value in content.metadata.items():
            lines.append(f"- {key}: {value}")
        lines.append("")
        
        # File Types section  
        lines.append("## File Types")
        if content.file_types_summary:
            lines.extend(content.file_types_summary.split('\n'))
        else:
            lines.append("No source files found.")
        lines.append("")
        
        # Required Skillsets section
        lines.append("## Required Skillsets")
        if content.required_skillsets_summary:
            lines.extend(content.required_skillsets_summary.split('\n'))
        else:
            lines.append("No specific skillsets identified.")
        lines.append("")
        
        # APIs section
        lines.append("## APIs")
        if content.apis_summary:
            lines.extend(content.apis_summary.split('\n'))
        else:
            lines.append("No APIs found.")
            
        return '\n'.join(lines)
        
    def _generate_file_types_summary(self, file_types: Dict[str, int]) -> str:
        """Generate a summary string for file types."""
        if not file_types:
            return ""
            
        lines = []
        for ext, count in sorted(file_types.items()):
            lines.append(f"- {ext}: {count}")
            
        return '\n'.join(lines)
        
    def _generate_skillsets_summary(self, skillsets: List[str]) -> str:
        """Generate a summary string for required skillsets."""
        if not skillsets:
            return ""
            
        lines = []
        for skillset in sorted(skillsets):
            lines.append(f"- {skillset}")
            
        return '\n'.join(lines)
        
    def _generate_apis_summary(self, apis: List) -> str:
        """Generate a summary string for APIs grouped by file."""
        if not apis:
            return ""
            
        # Group APIs by source file
        apis_by_file = {}
        for api in apis:
            if api.source_file not in apis_by_file:
                apis_by_file[api.source_file] = []
            apis_by_file[api.source_file].append(api)
            
        lines = []
        for source_file in sorted(apis_by_file.keys()):
            file_path = Path(source_file)
            lines.append(f"### `{file_path.name}`")
            
            for api in sorted(apis_by_file[source_file], key=lambda x: x.start_line):
                lines.append(f"- **{api.name}** (lines {api.start_line}-{api.end_line}): {api.semantic_description}")
                
            lines.append("")  # Extra space between files
            
        # Remove trailing empty line
        if lines and lines[-1] == "":
            lines.pop()
            
        return '\n'.join(lines)
        
    def _calculate_table_of_contents(self, file_types_summary: str, skillsets_summary: str, apis_summary: str) -> tuple[List[TocEntry], int]:
        """
        Calculate the table of contents with accurate line numbers.
        
        Returns:
            Tuple of (toc_entries_list, total_toc_lines)
        """
        # Start calculating from after the TOC header and [TOC] line
        # Line 1: TABLE-OF-CONTENTS: lines X-Y
        # Line 2: empty
        # Line 3: [TOC] 
        # Lines 4+: TOC entries
        # Line N: [/TOC]
        # Line N+1: empty
        # Content starts at line N+2
        
        toc_entries = []
        current_line = 1
        
        # Account for header lines: TABLE-OF-CONTENTS, empty line, [TOC]
        current_line += 3
        
        # We'll count TOC entries as we create them
        toc_entry_count = 4  # Metadata, File Types, Skillsets, APIs
        
        # Account for TOC entries themselves and [/TOC] and empty line
        current_line += toc_entry_count + 2  # +2 for [/TOC] and empty line
        
        # Now calculate each section
        
        # Metadata section (header + content + empty line)
        metadata_start = current_line
        metadata_lines = 1 + 2 + 1  # header + 2 metadata items + empty line
        metadata_end = current_line + metadata_lines - 1
        toc_entries.append(TocEntry(section_name="Metadata", start_line=metadata_start, end_line=metadata_end))
        current_line += metadata_lines
        
        # File Types section
        file_types_start = current_line
        file_types_content_lines = len(file_types_summary.split('\n')) if file_types_summary else 1
        file_types_lines = 1 + file_types_content_lines + 1  # header + content + empty line
        file_types_end = current_line + file_types_lines - 1
        toc_entries.append(TocEntry(section_name="File Types", start_line=file_types_start, end_line=file_types_end))
        current_line += file_types_lines
        
        # Skillsets section
        skillsets_start = current_line
        skillsets_content_lines = len(skillsets_summary.split('\n')) if skillsets_summary else 1
        skillsets_lines = 1 + skillsets_content_lines + 1  # header + content + empty line
        skillsets_end = current_line + skillsets_lines - 1
        toc_entries.append(TocEntry(section_name="Required Skillsets", start_line=skillsets_start, end_line=skillsets_end))
        current_line += skillsets_lines
        
        # APIs section (no trailing empty line for last section)
        apis_start = current_line
        apis_content_lines = len(apis_summary.split('\n')) if apis_summary else 1
        apis_lines = 1 + apis_content_lines  # header + content
        apis_end = current_line + apis_lines - 1
        toc_entries.append(TocEntry(section_name="APIs", start_line=apis_start, end_line=apis_end))
        
        # Total TOC lines is the entries count + [TOC] and [/TOC] lines
        total_toc_lines = toc_entry_count + 2  # +2 for [TOC] and [/TOC]
        
        return toc_entries, total_toc_lines
        
    def write_to_file(self, content: AgentsMdContent, output_path: Path) -> None:
        """
        Write the agents.md content to a file.
        
        Args:
            content: The structured content to write
            output_path: Path where to write the agents.md file
        """
        markdown_content = self.serialize_to_markdown(content)
        
        # Ensure the directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
    def create_metadata(self, commit_hash: str = "UNCOMMITTED") -> Dict[str, str]:
        """
        Create metadata dictionary with current timestamp and commit hash.
        
        Args:
            commit_hash: The commit hash, defaults to UNCOMMITTED
            
        Returns:
            Dictionary with metadata fields
        """
        return {
            'last_generated_utc': datetime.utcnow().isoformat() + 'Z',
            'commit_hash': commit_hash
        }
"""File reading and section parsing functionality."""

import wikitextparser as wtp
from typing import Dict, List
from .parsers.utils import clean_header
from .parsers.intel_cpulist_parser import parse as parse_cpulist
from .parsers.intel_wikitable_parser import parse as parse_wikitable
from .processors.intel_xeon_scalable import IntelXeonScalable

def is_cpulist_format(content: str) -> bool:
    """Detect if content uses cpulist template format."""
    return '{{cpulist' in content.lower()

def parse_sections(filename: str) -> Dict[str, Dict[str, List[IntelXeonScalable]]]:
    """Parse sections and their content from the file."""
    sections = {}
    
    with open(filename, 'r') as f:
        content = f.read()
        
    parsed = wtp.parse(content)
    
    # Find all sections
    for section in parsed.get_sections(level=3):
        section_name = section.title.strip()
        
        # Find the first table in the section
        tables = section.tables
        if not tables:
            continue
            
        table = tables[0]
        
        # Get headers
        headers = []
        seen_headers = set()
        
        # Headers are in the first row
        if table.data():
            header_row = table.data()[0]
            for cell in header_row:
                clean_h = clean_header(cell.strip())
                if clean_h and clean_h not in seen_headers:
                    headers.append(clean_h)
                    seen_headers.add(clean_h)
        
        # Parse CPU entries based on format
        section_content = str(section)
        if is_cpulist_format(section_content):
            cpu_entries = parse_cpulist(section_content)
        else:
            cpu_entries = parse_wikitable(section_content)
            
            # Update headers from table structure if using wikitable format
            if cpu_entries and not headers:
                # Get headers from first CPU's display fields
                cpu = cpu_entries[0]
                headers = [field for field in cpu._display_fields.keys() if cpu.get_display_value(field)]
        
        if cpu_entries:  # Only add sections with entries
            sections[section_name] = {
                'headers': headers,
                'entries': cpu_entries
            }
    
    return sections

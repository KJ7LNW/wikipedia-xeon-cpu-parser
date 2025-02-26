"""File reading and section parsing functionality."""

import wikitextparser as wtp
from typing import Dict, List
from .parsers.utils import clean_header
from .parsers.intel_cpulist_parser import parse
from .processors.intel_xeon_scalable import IntelXeonScalable

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
        
        # Parse all CPU entries in the section
        section_content = str(section)
        cpu_entries = parse(section_content)
        
        sections[section_name] = {
            'headers': headers,
            'entries': cpu_entries
        }
    
    return sections

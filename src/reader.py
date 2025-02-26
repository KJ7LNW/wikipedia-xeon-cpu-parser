"""File reading and section parsing functionality."""

import wikitextparser as wtp
from typing import Dict, List

from .parsers.base import clean_header
from .parsers.intel_cpulist_parser import parse_cpulist, map_fields_to_headers

def parse_sections(filename: str) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
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
        
        # Find all CPU entries
        cpu_entries = []
        templates = section.templates
        
        for template in templates:
            if template.name.strip() == 'cpulist':
                    parts = template.string.strip('{}').split('|')
                    if len(parts) >= 3:
                        platform = parts[1].strip()
                        subtype = parts[2].strip()
                        
                        # Parse cpulist template
                        fields = parse_cpulist(template.string)
                        
                        # Map fields to headers
                        if fields:
                            mapped_fields = map_fields_to_headers(fields, headers, platform, subtype)
                            cpu_entries.append(mapped_fields)
        
        sections[section_name] = {
            'headers': headers,
            'entries': cpu_entries
        }
    
    return sections

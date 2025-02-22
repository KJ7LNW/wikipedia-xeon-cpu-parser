#!/usr/bin/env python3

import re
from typing import Dict, List, Optional

def clean_header(header: str) -> Optional[str]:
    """Clean MediaWiki formatting from header text."""
    if (header.startswith('<!--') or 
        header.startswith('{{{') or 
        header.startswith('}}') or 
        'enable when needed' in header):
        return None
    
    # Handle special case for Release date
    if 'style="text-align:right;"' in header:
        return 'Release date'
    
    # Extract text from MediaWiki links [[text|display]] -> display
    header = re.sub(r'\[\[([^|]*)\|([^\]]*)\]\]', r'\2', header)
    # Extract text from remaining MediaWiki links [[text]] -> text
    header = re.sub(r'\[\[([^\]]*)\]\]', r'\1', header)
    
    # Remove HTML tags
    header = re.sub(r'<br\s*/>', ' ', header)
    
    # Remove MediaWiki template markers
    header = re.sub(r'\{\{!}}', '', header)
    
    # Remove style attributes
    header = re.sub(r'style="[^"]*"', '', header)
    
    # Clean up whitespace
    header = re.sub(r'\s+', ' ', header).strip()
    
    # Skip empty headers or template markers
    if not header or header.startswith('{{{') or header.startswith('}}'):
        return None
        
    return header

def parse_cpulist(cpulist: str) -> Dict[str, str]:
    """Parse a cpulist template into raw key-value pairs."""
    match = re.match(r'\{\{cpulist\|(.*?)\}\}', cpulist)
    if not match:
        return {}
    
    content = match.group(1)
    parts = content.split('|')
    
    # Process all parts after platform identifiers
    fields = {}
    for part in parts[2:]:  # Skip platform identifiers
        if '=' in part:
            key, value = part.split('=', 1)
            fields[key] = value
    
    return fields

def parse_sections(filename: str) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
    """Parse sections and their content from the file."""
    sections = {}
    
    with open(filename, 'r') as f:
        content = f.read()
        
        # Find all sections and their content
        section_matches = re.finditer(r'===\s*(.*?)\s*===\s*\n\s*{\|\s*class="wikitable sortable"\s*\n(.*?)(?=\n===|\Z)', content, re.DOTALL)
        
        for match in section_matches:
            section_name = match.group(1)
            section_content = match.group(2)
            
            # Get headers
            headers = []
            seen_headers = set()
            header_lines = re.finditer(r'!\s*((?:\[\[.*?\]\]|[^!\n])*)', section_content)
            
            for header_match in header_lines:
                header_text = header_match.group(1).strip()
                clean_h = clean_header(header_text)
                if clean_h and clean_h not in seen_headers:
                    headers.append(clean_h)
                    seen_headers.add(clean_h)
            
            # Find all CPU entries
            cpu_entries = []
            cpulist_matches = re.finditer(r'\{\{cpulist\|.*?\}\}', section_content)
            
            for cpu_match in cpulist_matches:
                cpulist = cpu_match.group(0)
                fields = parse_cpulist(cpulist)
                
                # Create entry with all headers initialized to empty strings
                entry = {header: '' for header in headers}
                
                # Map raw fields to entry
                for key, value in fields.items():
                    entry[key] = value
                
                cpu_entries.append(entry)
            
            sections[section_name] = {
                'headers': headers,
                'entries': cpu_entries
            }
    
    return sections

def main():
    sections = parse_sections('data.txt')
    for section_name, section_data in sections.items():
        print(f"\n=== {section_name} ===")
        headers = section_data['headers']
        entries = section_data['entries']
        
        # Print headers
        print("\nHeaders:")
        for i, header in enumerate(headers, 1):
            print(f"{i}. {header}")
        
        # Print first CPU entry as example
        if entries:
            print("\nExample CPU Entry (raw fields):")
            for key, value in entries[0].items():
                if value:
                    print(f"{key}: {value}")

if __name__ == '__main__':
    main()

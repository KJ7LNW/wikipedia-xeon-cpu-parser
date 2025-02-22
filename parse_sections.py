#!/usr/bin/env python3

import re

def clean_header(header):
    # Skip comment lines, template markers, and enable/disable notes
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

def parse_sections(filename):
    sections = {}
    
    with open(filename, 'r') as f:
        content = f.read()
        
        # Find all sections and their content
        section_matches = re.finditer(r'===\s*(.*?)\s*===\s*\n\s*{\|\s*class="wikitable sortable"\s*\n(.*?)\n\|-', content, re.DOTALL)
        
        for match in section_matches:
            section_name = match.group(1)
            header_content = match.group(2)
            
            # Find all headers (lines starting with !)
            headers = []
            seen_headers = set()  # Track unique headers
            header_lines = re.finditer(r'!\s*((?:\[\[.*?\]\]|[^!\n])*)', header_content)
            
            for header_match in header_lines:
                header_text = header_match.group(1).strip()
                clean_h = clean_header(header_text)
                if clean_h and clean_h not in seen_headers:
                    headers.append(clean_h)
                    seen_headers.add(clean_h)
            
            sections[section_name] = headers
    
    return sections

def main():
    sections = parse_sections('data.txt')
    print("Sections and their headers:")
    for section, headers in sections.items():
        print(f"\n=== {section} ===")
        for i, header in enumerate(headers, 1):
            print(f"{i}. {header}")

if __name__ == '__main__':
    main()

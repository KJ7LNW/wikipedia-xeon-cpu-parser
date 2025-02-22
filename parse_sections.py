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

def process_cpulist_fields(platform: str, subtype: str, fields: Dict[str, str]) -> Dict[str, str]:
    """Process cpulist fields according to template rules."""
    result = {}
    
    # Copy original fields
    for key, value in fields.items():
        result[key] = value
    
    # Platform specific defaults and calculations
    if platform == 'lake-e' and subtype == 'skylake_e':
        # L2 cache calculation
        if 'cores' in fields and 'l2' not in fields:
            cores = int(fields['cores'])
            result['l2'] = f"{cores} × 1 MB"
        
        # Socket defaults
        if 'sock' in fields:
            sock = fields['sock']
            if sock.isdigit():
                result['sock'] = f"LGA {sock}"
        
        # Memory formatting
        if 'mem' in fields:
            mem = fields['mem']
            if not mem.startswith('6×'):
                result['mem'] = f"6× {mem}"
        
        # I/O bus formatting
        if 'upi' in fields:
            upi = fields['upi']
            if not 'GT/s' in upi:
                result['upi'] = f"{upi} GT/s UPI"
    
    # Common field formatting
    if 'cores' in fields and 'threads' in fields:
        result['cores_threads'] = f"{fields['cores']} ({fields['threads']})"
    
    if 'part1' in fields or 'part2' in fields:
        parts = []
        if fields.get('part1'):
            parts.append(fields['part1'])
        if fields.get('part2'):
            parts.append(fields['part2'])
        if parts:
            result['parts'] = ', '.join(parts)
    
    # Calculate base frequency from multiplier (FSB is always 100 MHz)
    if 'mult' in fields:
        try:
            mult = float(fields['mult'])
            freq = (100 * mult) / 1000  # Convert to GHz
            result['freq'] = f"{freq:.1f} GHz"
        except ValueError:
            raise ValueError("Invalid multiplier value")
    else:
        raise ValueError("Missing multiplier for frequency calculation")
    
    return result

def parse_cpulist(cpulist: str) -> Dict[str, str]:
    """Parse a cpulist template into processed fields."""
    # Extract everything between {{ and }}
    match = re.match(r'\{\{cpulist\|(.*?)\}\}', cpulist, re.DOTALL)
    if not match:
        return {}
    
    content = match.group(1)
    parts = re.split(r'(?<!\\)\|', content)
    
    # Extract platform identifiers
    platform = parts[0].strip()
    subtype = parts[1].strip() if len(parts) > 1 else ''
    
    # Process key-value pairs
    fields = {}
    for part in parts[2:]:
        if '=' in part:
            key, value = part.split('=', 1)
            key = key.strip()
            value = value.strip()
            if value:  # Only store non-empty values
                fields[key] = value
    
    # Process fields according to template rules
    return process_cpulist_fields(platform, subtype, fields)

def map_fields_to_headers(fields: Dict[str, str], headers: List[str]) -> Dict[str, str]:
    """Map processed fields to table headers."""
    result = {header: '' for header in headers}
    
    # Direct field mappings
    field_to_header = {
        'model': 'Model number',
        'sspec1': 'sSpec number',
        'cores_threads': 'Cores (threads)',
        'freq': 'Frequency',
        'turbo': 'Turbo Boost all-core/2.0)',
        'l2': 'L2 cache',
        'l3': 'L3 cache',
        'tdp': 'TDP',
        'sock': 'Socket',
        'upi': 'I/O bus',
        'mem': 'Memory',
        'date': 'Release date',
        'parts': 'Part number(s)',
        'price': 'Release price (USD)'
    }
    
    # Map fields to headers
    for field, header in field_to_header.items():
        if field in fields and header in result:
            value = fields[field]
            # Add units where needed
            if field == 'tdp' and not value.endswith('W'):
                value = f"{value} W"
            elif field == 'l3' and not value.endswith('MB'):
                value = f"{value} MB"
            result[header] = value
    
    return result

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
                mapped_fields = map_fields_to_headers(fields, headers)
                cpu_entries.append(mapped_fields)
            
            sections[section_name] = {
                'headers': headers,
                'entries': cpu_entries
            }
    
    return sections

def parse_args():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description='Parse and filter CPU data')
    parser.add_argument('-f', '--min-base-ghz', type=float, help='Minimum base frequency in GHz')
    parser.add_argument('-w', '--min-tdp', type=int, help='Minimum TDP in watts')
    parser.add_argument('-W', '--max-tdp', type=int, help='Maximum TDP in watts')
    parser.add_argument('-c', '--min-cores', type=int, help='Minimum number of cores')
    parser.add_argument('--show-all', action='store_true', help='Show all fields (default: show only key fields)')
    return parser.parse_args()

def filter_entries(entries: List[Dict[str, str]], args) -> List[Dict[str, str]]:
    """Filter CPU entries based on criteria."""
    filtered = []
    for entry in entries:
        include = True
        
        # Check minimum cores
        if args.min_cores is not None:
            cores_str = entry.get('Cores (threads)', '')
            if cores_str:
                cores = int(cores_str.split()[0])
                if cores < args.min_cores:
                    include = False
        
        # Check TDP range
        if include and (args.min_tdp is not None or args.max_tdp is not None):
            tdp_str = entry.get('TDP', '')
            if tdp_str:
                tdp = int(tdp_str.split()[0])
                if args.min_tdp is not None and tdp < args.min_tdp:
                    include = False
                if args.max_tdp is not None and tdp > args.max_tdp:
                    include = False
        
        # Check minimum base frequency
        if args.min_base_ghz is not None and include:
            freq_str = entry.get('Frequency', '')
            if freq_str:
                try:
                    freq = float(freq_str.split()[0])
                    if freq < args.min_base_ghz:
                        include = False
                except (ValueError, IndexError):
                    include = False
        
        if include:
            filtered.append(entry)
    
    return filtered

def main():
    args = parse_args()
    sections = parse_sections('data.txt')
    
    # Define default fields to show
    default_fields = [
        'Model number',
        'Cores (threads)',
        'Frequency',
        'Turbo Boost all-core/2.0)',
        'L2 cache',
        'L3 cache',
        'TDP'
    ]
    
    for section_name, section_data in sections.items():
        print(f"\n=== {section_name} ===")
        headers = section_data['headers']
        entries = section_data['entries']
        
        # Apply filters
        filtered_entries = filter_entries(entries, args)
        
        # Print matching entries
        print(f"\nMatching Entries ({len(filtered_entries)}):")
        for entry in filtered_entries:
            print("\nCPU Entry:")
            # Show all fields or just default fields
            display_fields = headers if args.show_all else default_fields
            for header in display_fields:
                value = entry.get(header, '')
                if value:
                    print(f"{header}: {value}")

if __name__ == '__main__':
    main()

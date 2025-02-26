#!/usr/bin/env python3

import re
import wikitextparser as wtp
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

def get_l2_per_core(platform: str, subtype: str) -> float:
    """Get L2 cache size per core in MB based on platform/subtype."""
    mappings = {
        ('lake-e', 'skylake_e'): 1.0,    # 1 MB per core
        ('lake-e', 'cascadelake_e'): 1.0,
        ('lake', 'skylake'): 1.0,
        ('lake', 'cascadelake'): 1.0,
        ('lake', 'cooperlake'): 1.0,
        ('lake-sp', 'icelake'): 1.25,    # 1.25 MB per core
        ('lake-d', 'icelake'): 1.25,
        ('lake-sp', 'sapphirerapids'): 2.0,  # 2 MB per core
        ('lake-sp', 'emeraldrapids'): 2.0,
    }
    return mappings.get((platform, subtype), 1.0)  # Default to 1 MB if unknown

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
            l2_size = get_l2_per_core(platform, subtype)
            result['l2'] = f"{cores} × {l2_size} MB"
        
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
            pass
    
    return result

def parse_cpulist(template: str) -> Dict[str, str]:
    """Parse a cpulist template into processed fields."""
    parsed = wtp.parse(template)
    if not parsed.templates:
        return {}
    
    template = parsed.templates[0]
    parts = template.string.strip('{}').split('|')
    if parts[0].strip() != 'cpulist':
        return {}
    
    if len(parts) < 3:
        return {}
    
    platform = parts[1].strip()
    subtype = parts[2].strip()
    
    # Process key-value pairs
    fields = {}
    for part in parts[3:]:
        if '=' in part:
            key, value = part.split('=', 1)
            key = key.strip()
            value = value.strip()
            if value:  # Only store non-empty values
                fields[key] = value
    
    # Process fields according to template rules
    return process_cpulist_fields(platform, subtype, fields)

def map_fields_to_headers(fields: Dict[str, str], headers: List[str], platform: str, subtype: str) -> Dict[str, str]:
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
    
    # Calculate total cache
    try:
        cores = int(fields.get('cores', '0'))
        l2_size = get_l2_per_core(platform, subtype)
        l2_total = cores * l2_size
        l3_value = float(fields.get('l3', '0'))
        result['Total Cache'] = f"{l2_total + l3_value:.2f} MB"
    except (ValueError, TypeError):
        result['Total Cache'] = '-'
    
    return result

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
                        
                        # Build fields dict from template arguments
                        fields = {}
                        for part in parts[3:]:
                            if '=' in part:
                                key, value = part.split('=', 1)
                                key = key.strip()
                                value = value.strip()
                                if value:
                                    fields[key] = value
                    
                    # Process fields and map to headers
                    processed_fields = process_cpulist_fields(platform, subtype, fields)
                    mapped_fields = map_fields_to_headers(processed_fields, headers, platform, subtype)
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
    parser.add_argument('-s', '--sort', default='Frequency', help='Sort by field name')
    parser.add_argument('-t', '--markdown-table', action='store_true', help='Output as markdown table')
    parser.add_argument('-i', '--include', action='append', help='Always include entries matching substring (can be specified multiple times)')
    parser.add_argument('--show-all', action='store_true', help='Show all fields (default: show only key fields)')
    parser.add_argument('datafile', help='Input data file containing Wikipedia markup')
    return parser.parse_args()

def filter_entries(entries: List[Dict[str, str]], args) -> List[Dict[str, str]]:
    """Filter CPU entries based on criteria."""
    filtered = []
    for entry in entries:
        # Check if entry matches any include patterns
        is_included = False
        if args.include:
            model = entry.get('Model number', '')
            for pattern in args.include:
                if pattern.lower() in model.lower():
                    is_included = True
                    # Mark included entries in bold
                    entry['Model number'] = f"**{model}**"
                    break
        
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
        
        if include or is_included:
            filtered.append(entry)
    
    return filtered

def sort_entries(entries: List[Dict[str, str]], sort_field: str) -> List[Dict[str, str]]:
    """Sort entries by the specified field."""
    def get_sort_key(entry):
        if sort_field == 'corehz':
            # Sort by base frequency × cores
            try:
                freq = float(entry.get('Frequency', '0 GHz').split()[0])
                cores = int(entry.get('Cores (threads)', '0').split()[0])
                return freq * cores
            except (ValueError, IndexError):
                return 0
        elif sort_field == 'corehz-all':
            # Sort by all-core boost × cores
            try:
                turbo = entry.get('Turbo Boost all-core/2.0)', '')
                all_core = float(turbo.split('/')[0])
                cores = int(entry.get('Cores (threads)', '0').split()[0])
                return all_core * cores
            except (ValueError, IndexError):
                return 0
        elif sort_field == 'Frequency':
            # Extract numeric value from frequency string (e.g. "3.2 GHz" -> 3.2)
            try:
                return float(entry.get(sort_field, '0 GHz').split()[0])
            except (ValueError, IndexError):
                return 0
        elif sort_field == 'Cores (threads)':
            # Extract core count (e.g. "24 (48)" -> 24)
            try:
                return int(entry.get(sort_field, '0').split()[0])
            except (ValueError, IndexError):
                return 0
        elif sort_field == 'TDP':
            # Extract TDP value (e.g. "165 W" -> 165)
            try:
                return int(entry.get(sort_field, '0 W').split()[0])
            except (ValueError, IndexError):
                return 0
        return entry.get(sort_field, '')
    
    return sorted(entries, key=get_sort_key, reverse=True)

def print_markdown_table(entries: List[Dict[str, str]], fields: List[str], sort_field: str):
    """Print entries in markdown table format."""
    # Add GHz-cores/GHz-all-cores column if sorting by corehz/corehz-all
    display_fields = list(fields)
    if sort_field == 'corehz':
        display_fields.append('GHz-cores')
    elif sort_field == 'corehz-all':
        display_fields.append('GHz-all-cores')
    
    # Print header row
    print('|', ' | '.join(display_fields), '|', sep='')
    # Print separator row
    print('|', ' | '.join(['---' for _ in display_fields]), '|', sep='')
    # Print data rows
    for entry in entries:
        row = []
        for field in display_fields:
            if field in ('GHz-cores', 'GHz-all-cores'):
                try:
                    cores = int(entry.get('Cores (threads)', '0').split()[0])
                    if sort_field == 'corehz':
                        freq = float(entry.get('Frequency', '0 GHz').split()[0])
                        row.append(f"{freq * cores:.1f}")
                    else:  # corehz-all
                        turbo = entry.get('Turbo Boost all-core/2.0)', '')
                        if turbo and '/' in turbo and not turbo.startswith('?'):
                            all_core = float(turbo.split('/')[0])
                            row.append(f"{all_core * cores:.1f}")
                        else:
                            row.append('-')
                except (ValueError, IndexError):
                    row.append('-')
            else:
                value = entry.get(field, '')
                row.append(value if value else '-')
        print('|', ' | '.join(row), '|', sep='')

def main():
    args = parse_args()
    sections = parse_sections(args.datafile)
    
    # Define default fields to show
    default_fields = [
        'Model number',
        'Cores (threads)',
        'Frequency',
        'Turbo Boost all-core/2.0)',
        'L2 cache',
        'L3 cache',
        'Total Cache',
        'TDP'
    ]
    
    for section_name, section_data in sections.items():
        print(f"\n=== {section_name} ===")
        headers = section_data['headers']
        entries = section_data['entries']
        
        # Apply filters
        filtered_entries = filter_entries(entries, args)
        
        # Sort entries
        filtered_entries = sort_entries(filtered_entries, args.sort)
        
        # Get display fields
        display_fields = headers if args.show_all else default_fields
        
        # Print matching entries
        print(f"\nMatching Entries ({len(filtered_entries)}):")
        
        if args.markdown_table:
            print_markdown_table(filtered_entries, display_fields, args.sort)
        else:
            for entry in filtered_entries:
                print("\nCPU Entry:")
                for header in display_fields:
                    value = entry.get(header, '')
                    if value:
                        print(f"{header}: {value}")

if __name__ == '__main__':
    main()

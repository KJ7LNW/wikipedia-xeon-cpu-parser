"""Parser for Intel CPU list format."""

import wikitextparser as wtp
from typing import Dict, List

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
    
    # Field formatting rules
    format_rules = {
        'l2': lambda f: f"{int(f['cores'])} × {get_l2_per_core(platform, subtype)} MB" if 'cores' in f and 'l2' not in f else f.get('l2'),
        'sock': lambda f: f"LGA {f['sock']}" if 'sock' in f and f['sock'].isdigit() else f.get('sock'),
        'mem': lambda f: f"6× {f['mem']}" if 'mem' in f and not f['mem'].startswith('6×') else f.get('mem'),
        'upi': lambda f: f"{f['upi']} GT/s UPI" if 'upi' in f and 'GT/s' not in f['upi'] else f.get('upi'),
        'cores_threads': lambda f: f"{f['cores']} ({f['threads']})" if 'cores' in f and 'threads' in f else None,
        'parts': lambda f: ', '.join(filter(None, [f.get('part1'), f.get('part2')])) if any(f.get(k) for k in ['part1', 'part2']) else None,
        'freq': lambda f: f"{(float(f['mult']) * 100 / 1000):.1f} GHz" if 'mult' in f else None
    }

    # Apply formatting rules
    for field, rule in format_rules.items():
        try:
            value = rule(fields)
            if value is not None:
                result[field] = value
        except (ValueError, KeyError):
            continue
    
    return result

def map_fields_to_headers(fields: Dict[str, str], headers: List[str], platform: str, subtype: str) -> Dict[str, str]:
    """Map processed fields to table headers."""
    result = {header: '' for header in headers}
    
    # Header mappings with unit formatting
    header_mappings = {
        'model': ('Model number', lambda v: v),
        'sspec1': ('sSpec number', lambda v: v),
        'cores_threads': ('Cores (threads)', lambda v: v),
        'freq': ('Frequency', lambda v: v),
        'turbo': ('Turbo Boost all-core/2.0)', lambda v: v),
        'l2': ('L2 cache', lambda v: v),
        'l3': ('L3 cache', lambda v: f"{v} MB" if not v.endswith('MB') else v),
        'tdp': ('TDP', lambda v: f"{v} W" if not v.endswith('W') else v),
        'sock': ('Socket', lambda v: v),
        'upi': ('I/O bus', lambda v: v),
        'mem': ('Memory', lambda v: v),
        'date': ('Release date', lambda v: v),
        'parts': ('Part number(s)', lambda v: v),
        'price': ('Release price (USD)', lambda v: v)
    }
    
    # Map fields to headers with unit formatting
    for field, (header, format_func) in header_mappings.items():
        if field in fields and header in result:
            result[header] = format_func(fields[field])
    
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

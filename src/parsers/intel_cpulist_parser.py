"""Parser for Intel CPU list format."""

import wikitextparser as wtp
from typing import Dict, List
from ..processors.intel_xeon_scalable import IntelXeonScalable

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

def process_fields_to_cpu(fields: Dict[str, str], platform: str, subtype: str) -> Dict[str, str]:
    """Process fields into CPU class format."""
    result = {}
    
    # Process core/thread info
    if 'cores' in fields and 'threads' in fields:
        result['cores_count'] = int(fields['cores'])
        result['cores_threads'] = int(fields['threads'])
    
    # Process frequencies
    if 'freq' in fields:
        try:
            result['frequency_base_ghz'] = float(fields['freq'].split()[0])
        except (ValueError, IndexError):
            pass
            
    if 'turbo' in fields:
        try:
            turbo = fields['turbo'].split('/')
            if len(turbo) == 2:
                all_core = None
                single_core = None
                
                # Parse all-core turbo
                if not turbo[0].startswith('?'):
                    try:
                        all_core = float(turbo[0])
                    except (ValueError, IndexError):
                        pass
                
                # Parse single-core turbo
                try:
                    single_core = float(turbo[1].split()[0])
                except (ValueError, IndexError):
                    pass
                
                # Store values separately
                if all_core is not None:
                    result['frequency_turbo_all_ghz'] = all_core
                if single_core is not None:
                    result['frequency_turbo_single_ghz'] = single_core
        except (ValueError, IndexError):
            pass
    
    # Process cache
    if 'l3' in fields:
        try:
            l3 = fields['l3'].split()[0]
            result['cache_l3_mb'] = float(l3)
        except (ValueError, IndexError):
            pass
    
    # Process memory
    if 'mem' in fields:
        result['memory_type'] = fields['mem']
    
    # Process TDP
    if 'tdp' in fields:
        try:
            tdp = fields['tdp'].split()[0]
            result['tdp_w'] = int(tdp)
        except (ValueError, IndexError):
            pass
    
    # Process model info
    if 'model' in fields:
        result['model_number'] = fields['model']
    if 'date' in fields:
        result['model_launch'] = fields['date']
    if 'price' in fields:
        try:
            price = fields['price'].replace('$', '').replace(',', '')
            result['model_price_usd'] = float(price)
        except (ValueError, AttributeError):
            pass
    
    # Process Intel-specific fields
    if 'sspec1' in fields:
        result['intel_spec'] = fields['sspec1']
    if 'parts' in fields:
        result['intel_part'] = fields['parts']
    if 'sock' in fields:
        result['intel_socket'] = fields['sock']
    if 'upi' in fields:
        result['intel_upi_links'] = fields['upi']
    
    return result

def parse_cpulist(template: str) -> IntelXeonScalable:
    """Parse a cpulist template into a CPU object."""
    parsed = wtp.parse(template)
    if not parsed.templates:
        return IntelXeonScalable()
    
    template = parsed.templates[0]
    parts = template.string.strip('{}').split('|')
    if parts[0].strip() != 'cpulist':
        return IntelXeonScalable()
    
    if len(parts) < 3:
        return IntelXeonScalable()
    
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
    processed = process_cpulist_fields(platform, subtype, fields)
    
    # Convert to CPU class format
    cpu_fields = process_fields_to_cpu(processed, platform, subtype)
    
    # Create CPU object
    return IntelXeonScalable(**cpu_fields)

def parse(file_content: str) -> List[IntelXeonScalable]:
    """Parse file content into a list of CPU objects."""
    parsed = wtp.parse(file_content)
    cpus = []
    
    for template in parsed.templates:
        if template.name.strip() == 'cpulist':
            cpu = parse_cpulist(str(template))
            cpus.append(cpu)
    
    return cpus

"""Base processor functionality."""

from typing import Dict, List
from argparse import Namespace

def filter_entries(entries: List[Dict[str, str]], args: Namespace) -> List[Dict[str, str]]:
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

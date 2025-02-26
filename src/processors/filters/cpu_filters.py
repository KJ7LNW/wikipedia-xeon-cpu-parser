"""CPU filtering and sorting functions."""

from typing import List
from argparse import Namespace
from ..intel_xeon_scalable import IntelXeonScalable

def filter_entries(entries: List[IntelXeonScalable], args: Namespace) -> List[IntelXeonScalable]:
    """Filter CPU entries based on criteria."""
    filtered = []
    for entry in entries:
        # Check if entry matches any include patterns
        is_included = False
        if args.include:
            model = entry.model_number or ''
            for pattern in args.include:
                if pattern.lower() in model.lower():
                    is_included = True
                    entry.model_number = f"**{model}**"
                    break
        
        include = True
        
        # Check minimum cores
        if args.min_cores is not None and entry.cores_count is not None:
            if entry.cores_count < args.min_cores:
                include = False
        
        # Check TDP range
        if include and entry.tdp_w is not None:
            if args.min_tdp is not None and entry.tdp_w < args.min_tdp:
                include = False
            if args.max_tdp is not None and entry.tdp_w > args.max_tdp:
                include = False
        
        # Check minimum base frequency
        if args.min_base_ghz is not None and include:
            if entry.frequency_base_ghz is not None:
                if entry.frequency_base_ghz < args.min_base_ghz:
                    include = False
        
        if include or is_included:
            filtered.append(entry)
    
    return filtered

def sort_entries(entries: List[IntelXeonScalable], sort_field: str) -> List[IntelXeonScalable]:
    """Sort entries by the specified field."""
    def get_sort_key(entry):
        if sort_field == 'corehz':
            return entry.corehz
        elif sort_field == 'corehz-all':
            return entry.corehz_all
        elif sort_field == 'Frequency':
            return entry.frequency_base_ghz or 0
        elif sort_field == 'Cores (threads)':
            return entry.cores_count or 0
        elif sort_field == 'TDP':
            return entry.tdp_w or 0
        return entry.model_number or ''
    
    return sorted(entries, key=get_sort_key, reverse=True)

"""Output formatting functionality."""

from typing import List
from .processors.intel_xeon_scalable import IntelXeonScalable

def print_markdown_table(entries: List[IntelXeonScalable], fields: List[str], sort_field: str):
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
            if field == 'GHz-cores':
                row.append(f"{entry.corehz:.1f}" if entry.corehz > 0 else '-')
            elif field == 'GHz-all-cores':
                row.append(f"{entry.corehz_all:.1f}" if entry.corehz_all > 0 else '-')
            else:
                value = entry.get_display_value(field)
                row.append(str(value) if value is not None else '-')
        print('|', ' | '.join(row), '|', sep='')

"""Output formatting functionality."""

from typing import Dict, List

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

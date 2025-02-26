#!/usr/bin/env python3

import argparse
from src.reader import parse_sections
from src.processors.filters.cpu_filters import filter_entries, sort_entries
from src.io import print_markdown_table

def parse_args():
    """Parse command line arguments."""
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
                    value = entry.get_display_value(header)
                    if value is not None:
                        print(f"{header}: {value}")

if __name__ == '__main__':
    main()

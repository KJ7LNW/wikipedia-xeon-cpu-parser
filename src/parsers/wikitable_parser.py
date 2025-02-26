"""Generic parser for MediaWiki tables."""

import re
import json
import wikitextparser as wtp
from typing import Dict, List, Any

class TableStructure:
    """Represents a parsed MediaWiki table structure."""
    def __init__(self):
        self.headers: Dict[str, Dict[str, Any]] = {}  # Header structure with types and subheaders
        self.rows: List[Dict[str, Any]] = []     # List of row dictionaries

    def add_header(self, name: str, header_type: str = "simple", subheaders: List[str] = None):
        """Add a header definition."""
        self.headers[name] = {
            "type": header_type,
            "subheaders": subheaders if subheaders else []
        }
    
    def add_row(self, row_data: Dict[str, Any]):
        """Add a row of data."""
        self.rows.append(row_data)

def clean_text(text: str) -> str:
    """Clean up wiki markup from text."""
    if not text:
        return ""
    
    # Remove table markup attributes first
    text = re.sub(r'^[!\|]|\|$', '', text)  # Remove leading ! or | and trailing |
    text = re.sub(r'rowspan="[^"]+"', '', text)  # Remove rowspan
    text = re.sub(r'colspan="[^"]+"', '', text)  # Remove colspan
    text = re.sub(r'style="[^"]+"', '', text)  # Remove style
    
    # Extract text from wiki links and remove quotes
    text = re.sub(r'\[\[([^]|]+\|)?([^]]+)\]\]', r'\2', text)  # [[link|text]] -> text
    text = re.sub(r'\{\{([^}|]+\|)?([^}]+)\}\}', r'\2', text)  # {{template|text}} -> text
    text = re.sub(r'\[https://.*?\'\'(.*?)\'\'\]', r'\1', text)  # [https://...''text''] -> text
    text = re.sub(r'\[https?://[^\s\]]+\s+([^\]]+)\]', r'\1', text)  # [http://... text] -> text
    text = text.replace("''", '')  # Remove remaining '' quotes
    
    # Handle line breaks and special spaces
    text = re.sub(r'<br\s*/?>', ' ', text)  # Convert <br/> to space
    text = text.replace('\xa0', ' ')  # Replace non-breaking spaces
    text = text.replace('&nbsp;', ' ')  # Replace HTML non-breaking spaces
    
    # Clean up remaining markup and whitespace
    text = re.sub(r'\s*\|\s*', ' ', text)  # Convert remaining pipes to spaces
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)  # Collapse multiple spaces
    
    return text

def parse_table(table: wtp.Table) -> TableStructure:
    """Parse a MediaWiki table into a structured format."""
    table_struct = TableStructure()
    
    # Get table data with spans handled by wikitextparser
    cells = table.cells(span=True)
    if len(cells) < 2:  # Need at least headers and one data row
        return table_struct
    
    # Count header rows by looking for '!' markers
    header_rows = 0
    for row in cells:
        if any('!' in cell.string for cell in row):
            header_rows += 1
        else:
            break
    
    if header_rows == 0:
        return table_struct
    
    # Build header paths and mapping
    header_paths = {}  # Maps column index to header path
    for col_idx in range(len(cells[0])):
        path = []
        for row_idx in range(header_rows):
            if col_idx >= len(cells[row_idx]):
                continue
            cell = cells[row_idx][col_idx]
            # Skip headers with colspan equal to or greater than table width
            if 'colspan="' in cell.string:
                colspan = int(re.search(r'colspan="(\d+)"', cell.string).group(1))
                if colspan >= len(cells[0]):
                    continue
            
            text = clean_text(cell.string)
            if text and text != "-":
                # Don't add duplicate headers (from rowspan)
                if not path or text != path[-1]:
                    path.append(text)
        if path:
            header_paths[col_idx] = path
            # Add to header structure with cleaned and lowercased names
            main_header = clean_text(path[0]).lower()
            if len(path) > 1:
                table_struct.add_header(main_header, "compound", [clean_text(h).lower() for h in path[1:]])
            else:
                table_struct.add_header(main_header)
    
    # Process data rows
    for row in cells[header_rows:]:
        # Skip section header rows (typically have colspan spanning whole table)
        if len(row) == 1:
            continue
            
        # Skip rows with colspan equal to or greater than table width
        has_full_colspan = False
        for cell in row:
            if 'colspan="' in cell.string:
                colspan = int(re.search(r'colspan="(\d+)"', cell.string).group(1))
                if colspan >= len(cells[0]):
                    has_full_colspan = True
                    break
        if has_full_colspan:
            continue
            
        row_data = {}
        for col_idx, cell in enumerate(row):
            if col_idx not in header_paths:
                continue
            
            content = clean_text(cell.string)
            if not content or content == "-":
                continue
            
            # Skip section headers that start with !
            if content.startswith('!'):
                continue
                
            # Navigate the header path to build nested structure with cleaned and lowercased names
            path = [clean_text(h).lower() for h in header_paths[col_idx]]
            current = row_data
            for i, header in enumerate(path[:-1]):
                if header not in current:
                    current[header] = {}
                current = current[header]
            current[path[-1]] = content
        
        # Skip empty rows
        if row_data:
            table_struct.add_row(row_data)
    
    return table_struct

def parse_wikitable(text: str, debug: bool = False) -> List[TableStructure]:
    """Parse all tables in a MediaWiki text."""
    parsed = wtp.parse(text)
    tables = []
    
    for table in parsed.tables:
        table_struct = parse_table(table)
        tables.append(table_struct)
        if debug:
            print("\n=== Table Structure ===")
            print("Headers:")
            print(json.dumps(table_struct.headers, indent=2))
            print("\nRows:")
            print(json.dumps(table_struct.rows, indent=2))
    
    return tables

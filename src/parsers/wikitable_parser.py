"""Generic parser for MediaWiki tables."""

import re
import wikitextparser as wtp
from typing import Dict, List, Optional, Any, Tuple

class TableStructure:
    """Represents a parsed MediaWiki table structure."""
    def __init__(self):
        self.headers = {}  # Header structure with types and subheaders
        self.rows = []     # List of row dictionaries
    
    def add_header(self, name: str, header_type: str = "simple", subheaders: List[str] = None):
        """Add a header definition."""
        self.headers[name] = {
            "type": header_type,
            "subheaders": subheaders if subheaders else []
        }
    
    def add_row(self, row_data: Dict[str, Any]):
        """Add a row of data."""
        self.rows.append(row_data)

def parse_cell_attributes(cell: str) -> Tuple[str, int, int]:
    """Extract cell content and rowspan/colspan attributes."""
    content = cell.strip()
    rowspan = 1
    colspan = 1
    
    # Extract attributes if present
    if 'rowspan=' in cell:
        try:
            rowspan = int(cell.split('rowspan=')[1].split('"')[1].strip())
        except (IndexError, ValueError):
            pass
            
    if 'colspan=' in cell:
        try:
            colspan = int(cell.split('colspan=')[1].split('"')[1].strip())
        except (IndexError, ValueError):
            pass
    
    # Extract content after last |
    if '|' in cell:
        content = cell.split('|')[-1].strip()
    
    # Clean up <br /> tags
    content = content.replace('<br />', ' ').replace('<br/>', ' ')
    
    return content, rowspan, colspan

def split_table_cells(line: str, separator: str = '|') -> List[str]:
    """Split a table line into cells."""
    cells = []
    if not line:
        return cells
        
    # Remove leading separator
    if line.startswith(separator):
        line = line[len(separator):]
    
    # Handle both | and || separators
    parts = []
    current = ""
    in_quotes = False
    i = 0
    
    while i < len(line):
        if line[i] == '"':
            in_quotes = not in_quotes
        elif not in_quotes and i < len(line) - 1 and line[i:i+2] == separator * 2:
            parts.append(current)
            current = ""
            i += 1
        else:
            current += line[i]
        i += 1
    
    parts.append(current)
    return [p.strip() for p in parts if p.strip()]

def clean_text(text: str) -> str:
    """Clean up wiki markup from text."""
    text = text.replace('<br />', ' ').replace('<br/>', ' ')
    text = re.sub(r'\[\[([^]|]+\|)?([^]]+)\]\]', r'\2', text)  # [[link|text]] -> text
    text = re.sub(r'\{\{([^}|]+\|)?([^}]+)\}\}', r'\2', text)  # {{template|text}} -> text
    text = re.sub(r'\[https?://[^ ]+ ([^\]]+)\]', r'\1', text)  # [http://... text] -> text
    return text.strip()

def parse_table(table: wtp.Table) -> TableStructure:
    """Parse a MediaWiki table into a structured format."""
    table_struct = TableStructure()
    data = table.data()
    
    if len(data) < 3:  # Need headers, subheaders, and at least one data row
        return table_struct
        
    # First row contains main headers
    headers = [clean_text(h) for h in data[0]]
    # Second row contains subheaders or repeats headers
    subheaders = [clean_text(h) for h in data[1]]
    
    # Process headers
    header_map = {}  # Map column index to header name
    for i, header in enumerate(headers):
        if i >= len(subheaders):
            continue
            
        # Handle special case for Turbo Boost columns
        if header == "Turbo Boost" and i + 1 < len(headers) and headers[i + 1] == "Turbo Boost":
            table_struct.add_header(header, "compound", ["All core", "Single core"])
            header_map[i] = (header, "All core")
            header_map[i + 1] = (header, "Single core")
            continue
        elif i > 0 and headers[i - 1] == "Turbo Boost" and header == "Turbo Boost":
            continue
            
        # Handle other headers
        if header == subheaders[i] or not subheaders[i]:
            table_struct.add_header(header)
            header_map[i] = (header, None)
        else:
            table_struct.add_header(header, "compound", [subheaders[i]])
            header_map[i] = (header, subheaders[i])
    
    # Skip section headers and separator rows
    start_row = 2
    while start_row < len(data):
        row = data[start_row]
        # Skip if all cells are identical or if row is a separator (all cells are '-')
        if len(set(row)) == 1 or all(all(c == '-' for c in cell.strip()) for cell in row):
            start_row += 1
        else:
            break
    
    # Process data rows
    for row in data[start_row:]:
        row_data = {}
        for i, cell in enumerate(row):
            if i not in header_map:
                continue
                
            header, subheader = header_map[i]
            cell = clean_text(cell)
            
            if cell and not all(c == '-' for c in cell):  # Skip empty/separator cells
                if subheader:
                    if header not in row_data:
                        row_data[header] = {}
                    row_data[header][subheader] = cell
                else:
                    row_data[header] = cell
        
        # Skip section headers and empty rows
        if row_data and not all(v == row_data.get(next(iter(row_data))) for v in row_data.values()):
            table_struct.add_row(row_data)
    
    return table_struct

def parse_wikitable(text: str) -> List[TableStructure]:
    """Parse all tables in a MediaWiki text."""
    parsed = wtp.parse(text)
    tables = []
    
    for table in parsed.tables:
        table_struct = parse_table(table)
        tables.append(table_struct)
    
    return tables

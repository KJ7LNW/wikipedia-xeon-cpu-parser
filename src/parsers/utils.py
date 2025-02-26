"""Parser utility functions."""

def clean_header(header: str) -> str:
    """Clean and standardize header text."""
    if not header:
        return ''
    return header.strip()

"""Parser for Intel CPU MediaWiki table format."""

from typing import List, Dict, Any, Optional
from .wikitable_parser import parse_wikitable
from ..processors.intel_xeon_scalable import IntelXeonScalable

def parse_row_to_cpu(row: Dict[str, Any]) -> IntelXeonScalable:
    """Convert a table row to a CPU object."""
    cpu_fields = {}
    
    # Model number
    if "Model number" in row:
        cpu_fields["model_number"] = row["Model number"]
    
    # Cores/Threads
    if "Cores (threads)" in row:
        try:
            cores = int(row["Cores (threads)"].split()[0])
            threads = int(row["Cores (threads)"].split('(')[1].split(')')[0])
            cpu_fields["cores_count"] = cores
            cpu_fields["cores_threads"] = threads
        except (ValueError, IndexError):
            pass
    
    # Base frequency
    if "Base clock" in row:
        try:
            freq = float(row["Base clock"].split()[0])
            cpu_fields["frequency_base_ghz"] = freq
        except (ValueError, IndexError):
            pass
    
    # Turbo frequencies
    if "Turbo Boost" in row and isinstance(row["Turbo Boost"], dict):
        turbo = row["Turbo Boost"]
        try:
            if "All core" in turbo:
                freq = float(turbo["All core"].split()[0])
                cpu_fields["frequency_turbo_all_ghz"] = freq
            if "Single core" in turbo:
                freq = float(turbo["Single core"].split()[0])
                cpu_fields["frequency_turbo_single_ghz"] = freq
        except (ValueError, IndexError):
            pass
    
    # L3 Cache
    if "Smart cache" in row:
        try:
            cache = float(row["Smart cache"].split()[0])
            cpu_fields["cache_l3_mb"] = cache
        except (ValueError, IndexError):
            pass
    
    # TDP
    if "TDP" in row:
        try:
            if isinstance(row["TDP"], dict):
                # Handle base and turbo TDP
                if "Base" in row["TDP"]:
                    cpu_fields["tdp_w"] = int(row["TDP"]["Base"].split()[0])
                if "Turbo" in row["TDP"]:
                    cpu_fields["tdp_boost_w"] = int(row["TDP"]["Turbo"].split()[0])
            else:
                cpu_fields["tdp_w"] = int(row["TDP"].split()[0])
        except (ValueError, IndexError, AttributeError):
            pass
    
    # Memory
    if "Registered DDR5 w. ECC support" in row:
        cpu_fields["memory_type"] = row["Registered DDR5 w. ECC support"]
    
    # Price
    if "Release MSRP (USD)" in row:
        try:
            price = float(row["Release MSRP (USD)"].replace('$', '').replace(',', ''))
            cpu_fields["model_price_usd"] = price
        except (ValueError, AttributeError):
            pass
    
    # Intel-specific fields
    if "Maximum scalability" in row:
        cpu_fields["intel_max_sockets"] = row["Maximum scalability"]
    if "UPI links" in row:
        cpu_fields["intel_upi_links"] = row["UPI links"]
    
    return IntelXeonScalable(**cpu_fields)

def parse(content: str) -> List[IntelXeonScalable]:
    """Parse MediaWiki content into CPU objects."""
    tables = parse_wikitable(content)
    cpus = []
    
    for table in tables:
        for row in table.rows:
            cpu = parse_row_to_cpu(row)
            cpus.append(cpu)
    
    return cpus

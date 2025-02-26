"""Parser for Intel CPU MediaWiki table format."""

from typing import List, Dict, Any, Optional
from .wikitable_parser import parse_wikitable
from ..processors.intel_xeon_scalable import IntelXeonScalable

def parse_row_to_cpu(row: Dict[str, Any]) -> IntelXeonScalable:
    """Convert a table row to a CPU object."""
    cpu_fields = {}
    
    # Model number/Model - handle nested structure
    model = None
    if "Model number" in row:
        if isinstance(row["Model number"], dict):
            # Get first non-empty value from nested dict
            for v in row["Model number"].values():
                if v and v != "-" and not v.startswith("!"):
                    model = v
                    break
        else:
            model = row["Model number"]
    elif "Model" in row:
        if isinstance(row["Model"], dict):
            # Get first non-empty value from nested dict
            for v in row["Model"].values():
                if v and v != "-" and not v.startswith("!"):
                    model = v
                    break
        else:
            model = row["Model"]
    
    if model:
        cpu_fields["model_number"] = model
    else:
        # Skip rows without valid model numbers
        return None
    
    # Cores/Threads - handle nested structure
    cores_threads = None
    if "Cores (threads)" in row:
        if isinstance(row["Cores (threads)"], dict):
            # Get first non-empty value from nested dict
            for v in row["Cores (threads)"].values():
                if v and v != "-":
                    cores_threads = v
                    break
        else:
            cores_threads = row["Cores (threads)"]
    
    if cores_threads:
        try:
            cores = int(cores_threads.split()[0])
            threads = int(cores_threads.split('(')[1].split(')')[0])
            cpu_fields["cores_count"] = cores
            cpu_fields["cores_threads"] = threads
        except (ValueError, IndexError, AttributeError):
            pass
    
    # Base frequency - handle nested structure
    base_freq = None
    if "Base clock" in row:
        if isinstance(row["Base clock"], dict):
            # Get first non-empty value from nested dict
            for v in row["Base clock"].values():
                if v and v != "-":
                    base_freq = v
                    break
        else:
            base_freq = row["Base clock"]
    elif "Frequency" in row:
        if isinstance(row["Frequency"], dict):
            for v in row["Frequency"].values():
                if v and v != "-":
                    base_freq = v
                    break
        else:
            base_freq = row["Frequency"]
    elif "Clock rate (GHz)" in row and isinstance(row["Clock rate (GHz)"], dict):
        if "Base" in row["Clock rate (GHz)"]:
            base = row["Clock rate (GHz)"]["Base"]
            if isinstance(base, dict):
                for v in base.values():
                    if v and v != "-":
                        base_freq = v + " GHz"  # Add GHz since it's not in the value
                        break
            else:
                base_freq = base + " GHz"
    
    if base_freq:
        try:
            freq = float(base_freq.split()[0])
            cpu_fields["frequency_base_ghz"] = freq
        except (ValueError, IndexError, AttributeError):
            pass
    
    # Turbo frequencies - handle nested structure
    def extract_freq(value):
        if isinstance(value, dict):
            for v in value.values():
                if v and v != "-" and v != "?":
                    return float(str(v).split()[0])
        elif value and value != "-" and value != "?":
            return float(str(value).split()[0])
        return None

    try:
        if "Turbo Boost" in row:
            if isinstance(row["Turbo Boost"], dict):
                turbo = row["Turbo Boost"]
                # Handle nested All core/Single core format
                if "All core" in turbo:
                    freq = extract_freq(turbo["All core"])
                    if freq:
                        cpu_fields["frequency_turbo_all_ghz"] = freq
                if "Single core" in turbo:
                    freq = extract_freq(turbo["Single core"])
                    if freq:
                        cpu_fields["frequency_turbo_single_ghz"] = freq
                # Handle nested 2.0/3.0 format
                if "2.0" in turbo:
                    freq = extract_freq(turbo["2.0"])
                    if freq:
                        cpu_fields["frequency_turbo_all_ghz"] = freq
                if "3.0" in turbo:
                    freq = extract_freq(turbo["3.0"])
                    if freq:
                        cpu_fields["frequency_turbo_single_ghz"] = freq
        elif "Clock rate (GHz)" in row and isinstance(row["Clock rate (GHz)"], dict):
            if "Turbo Boost" in row["Clock rate (GHz)"]:
                turbo = row["Clock rate (GHz)"]["Turbo Boost"]
                if "2.0" in turbo:
                    freq = extract_freq(turbo["2.0"])
                    if freq:
                        cpu_fields["frequency_turbo_all_ghz"] = freq
                if "3.0" in turbo:
                    freq = extract_freq(turbo["3.0"])
                    if freq:
                        cpu_fields["frequency_turbo_single_ghz"] = freq
    except (ValueError, IndexError, AttributeError):
        pass
    
    # L2 Cache
    if "L2 cache" in row:
        try:
            if row["L2 cache"] != "-":
                # Handle format like "56 × 1.0 MB"
                parts = row["L2 cache"].split('×')
                if len(parts) == 2:
                    count = int(parts[0].strip())
                    size = float(parts[1].split()[0].strip())
                    cpu_fields["cache_l2_mb"] = count * size
        except (ValueError, IndexError):
            pass
    
    # L3 Cache - handle nested structure
    cache_size = None
    if "L3 cache" in row:
        if isinstance(row["L3 cache"], dict):
            for v in row["L3 cache"].values():
                if v and v != "-":
                    cache_size = v
                    break
        else:
            cache_size = row["L3 cache"]
    elif "Smart cache" in row:
        if isinstance(row["Smart cache"], dict):
            for v in row["Smart cache"].values():
                if v and v != "-":
                    cache_size = v
                    break
        else:
            cache_size = row["Smart cache"]
    
    if cache_size:
        try:
            cache = float(cache_size.split()[0])
            cpu_fields["cache_l3_mb"] = cache
        except (ValueError, IndexError, AttributeError):
            pass
    
    # TDP - handle both formats
    if "TDP" in row:
        try:
            if isinstance(row["TDP"], dict):
                # Handle base and turbo TDP
                if "Base" in row["TDP"] and row["TDP"]["Base"] != "-":
                    cpu_fields["tdp_w"] = int(row["TDP"]["Base"].split()[0])
                if "Turbo" in row["TDP"] and row["TDP"]["Turbo"] != "-":
                    cpu_fields["tdp_boost_w"] = int(row["TDP"]["Turbo"].split()[0])
            elif row["TDP"] != "-":
                # Handle "base/boost W" format
                if "/" in row["TDP"]:
                    base, boost = row["TDP"].split("/")
                    cpu_fields["tdp_w"] = int(base.strip())
                    cpu_fields["tdp_boost_w"] = int(boost.split()[0].strip())
                else:
                    cpu_fields["tdp_w"] = int(row["TDP"].split()[0])
        except (ValueError, IndexError, AttributeError):
            pass
    
    # Memory - handle nested structure
    if "Registered DDR5 w. ECC support" in row:
        if isinstance(row["Registered DDR5 w. ECC support"], dict):
            for v in row["Registered DDR5 w. ECC support"].values():
                if v and v != "-":
                    cpu_fields["memory_type"] = v
                    break
        else:
            cpu_fields["memory_type"] = row["Registered DDR5 w. ECC support"]
    
    # Price - handle nested structure
    if "Release MSRP (USD)" in row:
        price_str = None
        if isinstance(row["Release MSRP (USD)"], dict):
            for v in row["Release MSRP (USD)"].values():
                if v and v != "-":
                    price_str = v
                    break
        else:
            price_str = row["Release MSRP (USD)"]
        
        if price_str:
            try:
                price = float(price_str.replace('$', '').replace(',', ''))
                cpu_fields["model_price_usd"] = price
            except (ValueError, AttributeError):
                pass
    
    # Intel-specific fields - handle nested structure
    if "Maximum scalability" in row:
        if isinstance(row["Maximum scalability"], dict):
            for v in row["Maximum scalability"].values():
                if v and v != "-":
                    cpu_fields["intel_max_sockets"] = v
                    break
        else:
            cpu_fields["intel_max_sockets"] = row["Maximum scalability"]
    
    if "UPI links" in row:
        if isinstance(row["UPI links"], dict):
            for v in row["UPI links"].values():
                if v and v != "-":
                    cpu_fields["intel_upi_links"] = v
                    break
        else:
            cpu_fields["intel_upi_links"] = row["UPI links"]
    
    return IntelXeonScalable(**cpu_fields)

def parse(content: str, debug: bool = False) -> List[IntelXeonScalable]:
    """Parse MediaWiki content into CPU objects."""
    tables = parse_wikitable(content, debug)
    cpus = []
    
    for table in tables:
        for row in table.rows:
            cpu = parse_row_to_cpu(row)
            if cpu:  # Only add CPUs with valid model numbers
                cpus.append(cpu)
    
    return cpus

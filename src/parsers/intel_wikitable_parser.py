"""Parser for Intel CPU MediaWiki table format."""

from typing import List, Dict, Any, Optional
from .wikitable_parser import parse_wikitable
from ..processors.intel_xeon_scalable import IntelXeonScalable

def parse_row_to_cpu(row: Dict[str, Any]) -> IntelXeonScalable:
    """Convert a table row to a CPU object."""
    cpu_fields = {}
    
    # Model number/Model - handle nested structure
    model = None
    if "model number" in row:
        if isinstance(row["model number"], dict):
            # Get first non-empty value from nested dict
            for v in row["model number"].values():
                if v and v != "-" and not v.startswith("!"):
                    model = v
                    break
        else:
            model = row["model number"]
    elif "model" in row:
        if isinstance(row["model"], dict):
            # Get first non-empty value from nested dict
            for v in row["model"].values():
                if v and v != "-" and not v.startswith("!"):
                    model = v
                    break
        else:
            model = row["model"]
    
    if model:
        cpu_fields["model_number"] = model
    else:
        # Skip rows without valid model numbers
        return None
    
    # Cores/Threads - handle nested structure
    cores_threads = None
    if "cores (threads)" in row:
        if isinstance(row["cores (threads)"], dict):
            # Get first non-empty value from nested dict
            for v in row["cores (threads)"].values():
                if v and v != "-":
                    cores_threads = v
                    break
        else:
            cores_threads = row["cores (threads)"]
    
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
    if "base clock" in row:
        base_freq = row["base clock"]
    elif "frequency" in row:
        if isinstance(row["frequency"], dict):
            for v in row["frequency"].values():
                if v and v != "-":
                    base_freq = v
                    break
        else:
            base_freq = row["frequency"]
    elif "clock rate (ghz)" in row:
        if isinstance(row["clock rate (ghz)"], dict):
            if "base" in row["clock rate (ghz)"]:
                base = row["clock rate (ghz)"]["base"]
                if isinstance(base, dict):
                    for v in base.values():
                       if v and v != "-":
                            base_freq = v + " GHz"  # Add GHz since it's not in the value
                            break
                else:
                    base_freq = base + " GHz"
    
    if base_freq and base_freq != "-":
        try:
            # Handle case where GHz is not included
            if not base_freq.lower().endswith('ghz'):
                base_freq += " GHz"
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
        # Handle new turbo boost columns
        if "all core turbo boost" in row:
            freq = extract_freq(row["all core turbo boost"])
            if freq:
                cpu_fields["frequency_turbo_all_ghz"] = freq
        if "max turbo boost" in row:
            freq = extract_freq(row["max turbo boost"])
            if freq:
                cpu_fields["frequency_turbo_single_ghz"] = freq
        # Handle legacy Turbo Boost format
        elif "turbo boost" in row:
            if isinstance(row["turbo boost"], dict):
                turbo = row["turbo boost"]
                # Handle nested All core/Single core format
                if "all core" in turbo:
                    freq = extract_freq(turbo["all core"])
                    if freq:
                        cpu_fields["frequency_turbo_all_ghz"] = freq
                if "single core" in turbo:
                    freq = extract_freq(turbo["single core"])
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
        elif "clock rate (ghz)" in row and isinstance(row["clock rate (ghz)"], dict):
            if "turbo boost" in row["clock rate (ghz)"]:
                turbo = row["clock rate (ghz)"]["turbo boost"]
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
    if "l2 cache" in row:
        try:
            if row["l2 cache"] != "-":
                # Handle format like "56 × 1.0 MB"
                parts = row["l2 cache"].split('×')
                if len(parts) == 2:
                    count = int(parts[0].strip())
                    size = float(parts[1].split()[0].strip())
                    cpu_fields["cache_l2_mb"] = count * size
        except (ValueError, IndexError):
            pass
    
    # L3 Cache - handle nested structure
    cache_size = None
    if "l3 cache" in row:
        if isinstance(row["l3 cache"], dict):
            for v in row["l3 cache"].values():
                if v and v != "-":
                    cache_size = v
                    break
        else:
            cache_size = row["l3 cache"]
    elif "smart cache" in row:
        if isinstance(row["smart cache"], dict):
            for v in row["smart cache"].values():
                if v and v != "-":
                    cache_size = v
                    break
        else:
            cache_size = row["smart cache"]
    
    if cache_size:
        try:
            cache = float(cache_size.split()[0])
            cpu_fields["cache_l3_mb"] = cache
        except (ValueError, IndexError, AttributeError):
            pass
    
    # TDP - handle both formats
    if "tdp" in row:
        try:
            if isinstance(row["tdp"], dict):
                # Handle base and turbo TDP
                if "base" in row["tdp"] and row["tdp"]["base"] != "-":
                    cpu_fields["tdp_w"] = int(row["tdp"]["base"].split()[0])
                if "turbo" in row["tdp"] and row["tdp"]["turbo"] != "-":
                    cpu_fields["tdp_boost_w"] = int(row["tdp"]["turbo"].split()[0])
            elif row["tdp"] != "-":
                # Handle "base/boost W" format
                if "/" in row["tdp"]:
                    base, boost = row["tdp"].split("/")
                    cpu_fields["tdp_w"] = int(base.strip())
                    cpu_fields["tdp_boost_w"] = int(boost.split()[0].strip())
                else:
                    # Handle simple format like "385 W"
                    tdp_str = row["tdp"]
                    if tdp_str.endswith(" W"):
                        tdp_str = tdp_str[:-2]  # Remove " W"
                    cpu_fields["tdp_w"] = int(tdp_str)
        except (ValueError, IndexError, AttributeError):
            pass
    
    # Memory - handle nested structure
    if "registered ddr5 w. ecc support" in row:
        if isinstance(row["registered ddr5 w. ecc support"], dict):
            for v in row["registered ddr5 w. ecc support"].values():
                if v and v != "-":
                    cpu_fields["memory_type"] = v
                    break
        else:
            cpu_fields["memory_type"] = row["registered ddr5 w. ecc support"]
    
    # Price - handle nested structure
    if "release msrp (usd)" in row:
        price_str = None
        if isinstance(row["release msrp (usd)"], dict):
            for v in row["release msrp (usd)"].values():
                if v and v != "-":
                    price_str = v
                    break
        else:
            price_str = row["release msrp (usd)"]
        
        if price_str:
            try:
                price = float(price_str.replace('$', '').replace(',', ''))
                cpu_fields["model_price_usd"] = price
            except (ValueError, AttributeError):
                pass
    
    # Intel-specific fields - handle nested structure
    if "maximum scalability" in row:
        if isinstance(row["maximum scalability"], dict):
            for v in row["maximum scalability"].values():
                if v and v != "-":
                    cpu_fields["intel_max_sockets"] = v
                    break
        else:
            cpu_fields["intel_max_sockets"] = row["maximum scalability"]
    
    if "upi links" in row:
        if isinstance(row["upi links"], dict):
            for v in row["upi links"].values():
                if v and v != "-":
                    cpu_fields["intel_upi_links"] = v
                    break
        else:
            cpu_fields["intel_upi_links"] = row["upi links"]
    
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

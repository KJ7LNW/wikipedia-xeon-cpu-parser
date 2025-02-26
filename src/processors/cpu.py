"""Base CPU class."""

from typing import Dict

class CPU:
    """Generic CPU class with common fields."""
    
    # Display field names
    _display_fields = {
        'Model number': 'model_number',
        'Cores (threads)': lambda self: f"{self.cores_count} ({self.cores_threads})" if self.cores_count and self.cores_threads else None,
        'Frequency': lambda self: f"{self.frequency_base_ghz} GHz" if self.frequency_base_ghz else None,
        'Turbo Boost all-core/2.0)': lambda self: (
            f"{self.frequency_turbo_all_ghz if self.frequency_turbo_all_ghz is not None else '?'}/"
            f"{self.frequency_turbo_single_ghz if self.frequency_turbo_single_ghz is not None else '?'} GHz"
            if self.frequency_turbo_all_ghz is not None or self.frequency_turbo_single_ghz is not None
            else None
        ),
        'L2 cache': lambda self: f"{self.cores_count} × 1.0 MB" if self.cores_count else None,
        'L3 cache': lambda self: f"{self.cache_l3_mb:g} MB" if self.cache_l3_mb else None,
        'Total Cache': lambda self: f"{(self.cache_l3_mb + self.cores_count):.2f} MB" if self.cache_l3_mb and self.cores_count else None,
        'TDP': lambda self: f"{self.tdp_w} W" if self.tdp_w else None
    }
    
    def __init__(self, **kwargs):
        """Initialize CPU with field values."""
        # Initialize all fields to None
        self.model_number = None
        self.cores_count = None
        self.cores_threads = None
        self.frequency_base_ghz = None
        self.frequency_turbo_all_ghz = None
        self.frequency_turbo_single_ghz = None
        self.cache_l3_mb = None
        self.memory_type = None
        self.memory_speed_mt_s = None
        self.tdp_w = None
        self.model_launch = None
        self.model_price_usd = None
        
        # Set provided values
        for field, value in kwargs.items():
            if hasattr(self, field):
                setattr(self, field, value)
    
    def get_display_value(self, field: str) -> str:
        """Get formatted display value for a field."""
        if field not in self._display_fields:
            return None
            
        field_spec = self._display_fields[field]
        if callable(field_spec):
            return field_spec(self)
        else:
            return getattr(self, field_spec, None)
    
    @property
    def corehz(self) -> float:
        """Calculate frequency × cores metric."""
        if self.frequency_base_ghz is None or self.cores_count is None:
            return 0.0
        return self.frequency_base_ghz * self.cores_count
    
    @property
    def corehz_all(self) -> float:
        """Calculate all-core turbo × cores metric."""
        if self.frequency_turbo_all_ghz is None or self.cores_count is None:
            return 0.0
        return self.frequency_turbo_all_ghz * self.cores_count

"""Intel Xeon Scalable processor class."""

from .cpu import CPU

class IntelXeonScalable(CPU):
    """Intel Xeon Scalable processor."""
    
    # Intel Xeon specific fields
    _specific_field_mappings = {
        # Identification
        'intel_spec': 'sSpec',
        'intel_part': 'Part Number',
        
        # Interconnect
        'intel_upi_links': 'UPI Links',
        'intel_socket': 'Socket',
        'intel_io_bus': 'I/O Bus',
        
        # Scalability  
        'intel_max_sockets': 'Maximum Sockets'
    }
    
    def __init__(self, **kwargs):
        """Initialize Xeon with field values."""
        super().__init__(**kwargs)
        
        # Initialize Intel-specific fields
        for field in self._specific_field_mappings:
            setattr(self, field, None)
        
        # Set provided values
        for field, value in kwargs.items():
            if hasattr(self, field):
                setattr(self, field, value)

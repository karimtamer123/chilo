import re
from typing import Dict, Any, Optional, Tuple

def parse_dimensions(dimensions_str: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Parse dimensions string like "152.0 L 89.0 W 89.0 H (in)" 
    Returns (length, width, height) in inches.
    """
    if not dimensions_str or not isinstance(dimensions_str, str):
        return None, None, None
    
    # Pattern to match: number L number W number H (in)
    pattern = r'([0-9.]+)\s*L\s*([0-9.]+)\s*W\s*([0-9.]+)\s*H'
    match = re.search(pattern, dimensions_str)
    
    if match:
        try:
            length = float(match.group(1))
            width = float(match.group(2))
            height = float(match.group(3))
            return length, width, height
        except ValueError:
            pass
    
    return None, None, None

def parse_pressure_drop(psi_ftwg_str: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parse pressure drop string like "3.4/7.7" 
    Returns (psi, ftwg) as floats.
    """
    if not psi_ftwg_str or not isinstance(psi_ftwg_str, str):
        return None, None
    
    # Split by "/" and extract numbers
    parts = psi_ftwg_str.split('/')
    if len(parts) == 2:
        try:
            psi = float(parts[0].strip())
            ftwg = float(parts[1].strip())
            return psi, ftwg
        except ValueError:
            pass
    
    return None, None

def safe_float(value: Any) -> Optional[float]:
    """Safely convert value to float, returning None for empty/invalid values."""
    if value is None or value == '' or value == 'N/A':
        return None
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def safe_int(value: Any) -> Optional[int]:
    """Safely convert value to int, returning None for empty/invalid values."""
    if value is None or value == '' or value == 'N/A':
        return None
    
    try:
        return int(float(value))  # Convert to float first to handle "123.0"
    except (ValueError, TypeError):
        return None

def normalize_header(header: str) -> str:
    """
    Normalize header text for matching.
    - Convert to lowercase
    - Strip whitespace
    - Remove text in parentheses
    - Replace common variations
    """
    if not header:
        return ""
    
    # Convert to lowercase and strip
    normalized = header.lower().strip()
    
    # Remove text in parentheses
    normalized = re.sub(r'\([^)]*\)', '', normalized)
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    # Common variations
    variations = {
        'energy efficiency (kw/ton)': 'energy efficiency',
        'energy efficiency': 'efficiency_kw_per_ton',
        'efficiency': 'efficiency_kw_per_ton',
        'iplv (kw/ton)': 'iplv_kw_per_ton',
        'iplv': 'iplv_kw_per_ton',
        'usgpm': 'waterflow_usgpm',
        'waterflow': 'waterflow_usgpm',
        'u. kw': 'unit_kw',
        'c. kw': 'compressor_kw',
        'f. kw': 'fan_kw',
        'psi/ft.w.g': 'pressure_drop',
        'mca': 'mca_amps',
        'dimensions': 'dimensions'
    }
    
    return variations.get(normalized, normalized)

def convert_eer_to_kw_per_ton(eer: float) -> float:
    """Convert EER to kW/ton using the formula: kW/ton = 3.51685 / EER"""
    return 3.51685 / eer

def clean_model_name(model: str) -> str:
    """Clean and normalize model name."""
    if not model:
        return ""
    return str(model).strip()

def extract_manufacturer_from_model(model: str) -> Optional[str]:
    """
    Try to extract manufacturer from model name.
    This is a simple heuristic - can be enhanced based on known patterns.
    """
    if not model:
        return None
    
    # Common manufacturer prefixes
    prefixes = {
        'ACHX': 'Dunham Bush',
        'AVX': 'Dunham Bush',
        'CH': 'Carrier',
        'TRA': 'Trane',
        'RT': 'Trane',
        'YORK': 'York',
        'YV': 'York',
        'MC': 'McQuay',
        'MCH': 'McQuay'
    }
    
    model_upper = model.upper()
    for prefix, manufacturer in prefixes.items():
        if model_upper.startswith(prefix):
            return manufacturer
    
    return None

def extract_model_prefix(model: str) -> Optional[str]:
    """
    Extract the base model prefix from a full model name.
    For example: "ACHX-B 90S" -> "ACHX-B"
    """
    if not model:
        return None
    
    # Split by spaces and take the first part (before any numbers)
    # This handles patterns like "ACHX-B 90S", "ACHX-B 120T", etc.
    parts = model.strip().split()
    if not parts:
        return None
    
    # If the first part contains a dash or is a clear prefix, use it
    first_part = parts[0]
    
    # Check if first part looks like a prefix (contains letters/dashes, no numbers)
    if any(c.isalpha() or c == '-' for c in first_part):
        return first_part
    
    # Otherwise, try to extract prefix before first number
    import re
    match = re.match(r'^([A-Za-z\-]+)', model)
    if match:
        return match.group(1)
    
    return first_part

def validate_chiller_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clean chiller data.
    Returns cleaned data with validation errors noted.
    """
    cleaned = {}
    errors = []
    
    # Required fields
    if not data.get('model'):
        errors.append("Model is required")
    
    # Clean and validate numeric fields
    numeric_fields = {
        'capacity_tons': 'Capacity (tons)',
        'efficiency_kw_per_ton': 'Energy efficiency',
        'iplv_kw_per_ton': 'IPLV',
        'waterflow_usgpm': 'Waterflow',
        'unit_kw': 'Unit kW',
        'compressor_kw': 'Compressor kW',
        'fan_kw': 'Fan kW',
        'mca_amps': 'MCA',
        'ambient_f': 'Ambient',
        'ewt_c': 'EWT',
        'lwt_c': 'LWT'
    }
    
    for field, display_name in numeric_fields.items():
        value = safe_float(data.get(field))
        if value is not None:
            cleaned[field] = value
        elif field in ['capacity_tons', 'efficiency_kw_per_ton']:
            errors.append(f"{display_name} is required")
    
    # Clean text fields
    text_fields = ['model', 'manufacturer', 'refrigerant', 'notes', 'folder_name', 'model_prefix']
    for field in text_fields:
        value = data.get(field)
        if value:
            cleaned[field] = str(value).strip()
    
    # Parse special fields
    if 'dimensions' in data:
        length, width, height = parse_dimensions(data['dimensions'])
        if length is not None:
            cleaned['length_in'] = length
        if width is not None:
            cleaned['width_in'] = width
        if height is not None:
            cleaned['height_in'] = height
    
    if 'pressure_drop' in data:
        psi, ftwg = parse_pressure_drop(data['pressure_drop'])
        if psi is not None:
            cleaned['pressure_drop_psi'] = psi
        if ftwg is not None:
            cleaned['pressure_drop_ftwg'] = ftwg
    
    # Extract manufacturer if not provided
    if not cleaned.get('manufacturer') and cleaned.get('model'):
        manufacturer = extract_manufacturer_from_model(cleaned['model'])
        if manufacturer:
            cleaned['manufacturer'] = manufacturer
    
    # Store any unmapped fields in extras_json
    mapped_fields = set(cleaned.keys()) | {'dimensions', 'pressure_drop'}
    extras = {k: v for k, v in data.items() if k not in mapped_fields and v is not None}
    if extras:
        cleaned['extras_json'] = extras
    
    return cleaned, errors

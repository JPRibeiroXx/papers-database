"""
Unique name generation logic for papers database.

This module implements flexible unique_name generation with multiple naming schemes:
- Sequential numbering with category and project codes
- Year-based naming with meaningful project identifiers
- Hierarchical naming based on relates_to and project_id

The relates_to and project_id fields link to lookup tables:
- relates_to: BRNG (Braining), FE35 (Fellowship i3S), PHHD (PhD), OTER (Other)
- project_id: SYEL (Systematic Review + ML), CANG (Cardiac Bioprinting), etc.
"""

from typing import Dict, Any, Optional
from enum import Enum


class NamingScheme(Enum):
    """Available naming schemes for unique IDs."""
    SEQUENTIAL = "sequential"  # 0001-PRAI-BRNG-SYEL
    YEAR_BASED = "year_based"  # 2023-PRAI-BRNG-SYEL  
    HIERARCHICAL = "hierarchical"  # BRNG-SYEL-001-PRAI
    PROJECT_FIRST = "project_first"  # SYEL-BRNG-2023-PRAI
    SIMPLE = "simple"  # BRNG-SYEL-001


def unique_name_from_row(row: Dict[str, Any], record_number: Optional[int] = None, scheme: NamingScheme = NamingScheme.SEQUENTIAL) -> str:
    """
    Generate a unique name from a row of data using the specified naming scheme.
    
    Args:
        row: Dictionary containing paper data
        record_number: Sequential record number (1, 2, 3, etc.)
        scheme: Naming scheme to use
            
    Returns:
        String with unique identifier or empty string if required fields missing
    """
    # Extract fields
    title = _safe_str(row.get('title', ''))
    relates_to = _safe_str(row.get('relates_to', ''))  # BRNG, FE35, PHHD, OTER
    project_id = _safe_str(row.get('project_id', ''))  # SYEL, CANG, IBON, etc.
    year = row.get('year', '')
    
    # Check if required fields are present
    if not all([title, relates_to, project_id]):
        return ""
    
    # Generate title tag: first 2 + last 2 letters, uppercase
    title_tag = _generate_title_tag(title)
    if not title_tag:
        return ""
    
    # Format year
    year_str = ""
    if year:
        try:
            year_str = str(int(year))
        except (ValueError, TypeError):
            year_str = ""
    
    # Format record number as 3-digit string for most schemes
    number_str = f"{record_number:03d}" if record_number else "001"
    number_str_4 = f"{record_number:04d}" if record_number else "0001"
    
    # Generate unique name based on scheme
    if scheme == NamingScheme.SEQUENTIAL:
        # Original Excel format: 0001-PRAI-BRNG-SYEL
        return f"{number_str_4}-{title_tag}-{relates_to}-{project_id}"
        
    elif scheme == NamingScheme.YEAR_BASED:
        # Year first: 2023-PRAI-BRNG-SYEL
        if not year_str:
            return ""
        return f"{year_str}-{title_tag}-{relates_to}-{project_id}"
        
    elif scheme == NamingScheme.HIERARCHICAL:
        # Category > Project > Number > Title: BRNG-SYEL-001-PRAI
        return f"{relates_to}-{project_id}-{number_str}-{title_tag}"
        
    elif scheme == NamingScheme.PROJECT_FIRST:
        # Project > Category > Year > Title: SYEL-BRNG-2023-PRAI
        if not year_str:
            return f"{project_id}-{relates_to}-{number_str_4}-{title_tag}"
        return f"{project_id}-{relates_to}-{year_str}-{title_tag}"
        
    elif scheme == NamingScheme.SIMPLE:
        # Simple: BRNG-SYEL-001 (no title)
        return f"{relates_to}-{project_id}-{number_str}"
    
    else:
        # Default to sequential
        return f"{number_str_4}-{title_tag}-{relates_to}-{project_id}"


def _safe_str(value: Any) -> str:
    """Convert value to string, handling None and NaN."""
    if value is None:
        return ""
    if hasattr(value, 'isna') and value.isna():
        return ""
    return str(value).strip()


def _generate_title_tag(title: str) -> str:
    """
    Generate title tag from first 2 and last 2 letters.
    
    Args:
        title: Title string
        
    Returns:
        4-character uppercase string, or empty if title too short
    """
    if not title:
        return ""
    
    # Remove non-alphabetic characters and get letters only
    letters = ''.join(c for c in title if c.isalpha())
    
    if len(letters) < 2:
        return ""
    elif len(letters) == 2:
        # If only 2 letters, repeat them
        return (letters * 2).upper()
    elif len(letters) == 3:
        # If 3 letters, use first 2 + last 1 + last 1
        return (letters[:2] + letters[-1] * 2).upper()
    else:
        # Normal case: first 2 + last 2
        return (letters[:2] + letters[-2:]).upper()


def _clean_component(component: str) -> str:
    """
    Clean component for use in unique name.
    
    Args:
        component: Raw component string
        
    Returns:
        Cleaned string suitable for unique name
    """
    if not component:
        return ""
    
    # Remove whitespace and common problematic characters
    cleaned = component.strip()
    
    # Remove or replace characters that might cause issues
    # Keep alphanumeric and basic punctuation
    cleaned = ''.join(c for c in cleaned if c.isalnum() or c in '.-_')
    
    # Limit length to prevent overly long unique names
    if len(cleaned) > 20:
        cleaned = cleaned[:20]
    
    return cleaned.upper()


def _clean_component_short(component: str) -> str:
    """
    Clean component for use in unique name, keeping it very short.
    
    Args:
        component: Raw component string
        
    Returns:
        Short cleaned string (max 8 chars)
    """
    if not component:
        return ""
    
    # Remove whitespace and common problematic characters
    cleaned = component.strip()
    
    # Keep only alphanumeric characters
    cleaned = ''.join(c for c in cleaned if c.isalnum())
    
    # Limit to 8 characters max
    if len(cleaned) > 8:
        cleaned = cleaned[:8]
    
    return cleaned.upper()


def validate_unique_name(unique_name: str) -> bool:
    """
    Validate that a unique name follows the expected format.
    
    Args:
        unique_name: The unique name to validate
        
    Returns:
        True if valid format, False otherwise
    """
    if not unique_name:
        return False
    
    parts = unique_name.split('-')
    if len(parts) != 5:
        return False
    
    year_part, title_part, authors_part, journal_part, doi_part = parts
    
    # Check year is 4 digits
    if not (year_part.isdigit() and len(year_part) == 4):
        return False
    
    # Check title part is 4 uppercase letters
    if not (title_part.isalpha() and len(title_part) == 4 and title_part.isupper()):
        return False
    
    # Other parts should be non-empty
    if not all([authors_part, journal_part, doi_part]):
        return False
    
    return True


def preview_naming_schemes(row: Dict[str, Any], record_number: int = 1) -> Dict[str, str]:
    """
    Preview all available naming schemes for a given row.
    
    Args:
        row: Dictionary containing paper data
        record_number: Sequential record number
        
    Returns:
        Dictionary mapping scheme names to generated unique names
    """
    schemes = {}
    for scheme in NamingScheme:
        try:
            unique_name = unique_name_from_row(row, record_number, scheme)
            schemes[scheme.value] = unique_name
        except Exception as e:
            schemes[scheme.value] = f"Error: {e}"
    
    return schemes


def get_scheme_description(scheme: NamingScheme) -> str:
    """Get human-readable description of a naming scheme."""
    descriptions = {
        NamingScheme.SEQUENTIAL: "Sequential numbering (0001-PRAI-BRNG-SYEL) - matches original Excel format",
        NamingScheme.YEAR_BASED: "Year-based (2023-PRAI-BRNG-SYEL) - chronological organization",
        NamingScheme.HIERARCHICAL: "Hierarchical (BRNG-SYEL-001-PRAI) - category first, then project",
        NamingScheme.PROJECT_FIRST: "Project-focused (SYEL-BRNG-2023-PRAI) - project first, then category",
        NamingScheme.SIMPLE: "Simple (BRNG-SYEL-001) - minimal identifier without title"
    }
    return descriptions.get(scheme, "Unknown scheme")


def suggest_best_scheme(data_sample: list) -> NamingScheme:
    """
    Suggest the best naming scheme based on data characteristics.
    
    Args:
        data_sample: List of sample records
        
    Returns:
        Recommended naming scheme
    """
    # Analyze data characteristics
    has_years = any(row.get('year') for row in data_sample)
    unique_projects = len(set(row.get('project_id', '') for row in data_sample))
    unique_categories = len(set(row.get('relates_to', '') for row in data_sample))
    
    # Make recommendations based on data
    if unique_projects > unique_categories * 2:
        # Many projects per category - project-first makes sense
        return NamingScheme.PROJECT_FIRST
    elif has_years and len(data_sample) > 50:
        # Large dataset with years - chronological might be useful
        return NamingScheme.YEAR_BASED
    elif unique_categories > 1 and unique_projects > 1:
        # Good mix of categories and projects - hierarchical works well
        return NamingScheme.HIERARCHICAL
    else:
        # Default to sequential for consistency
        return NamingScheme.SEQUENTIAL


# For testing and development
if __name__ == "__main__":
    # Test cases
    test_cases = [
        {
            'title': 'Predicting recovery following stroke',
            'authors': 'BRNG',
            'journal': 'SYEL', 
            'doi': '45502',
            'year': 2023
        },
        {
            'title': 'AI',  # Very short title
            'authors': 'Smith',
            'journal': 'Nature',
            'doi': '10.1234',
            'year': 2024
        },
        {
            'title': '',  # Missing title
            'authors': 'Smith',
            'journal': 'Nature', 
            'doi': '10.1234',
            'year': 2024
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        result = unique_name_from_row(test_case)
        print(f"Test case {i+1}: {result}")
        if result:
            print(f"  Valid: {validate_unique_name(result)}")
        print()

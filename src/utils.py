"""
Utility functions for the Patient Report Generator.
Contains helper functions for filename handling, coordinate conversion, and other utilities.
"""

import re


def slugify_filename(s: str, fallback: str = "report") -> str:
    """
    Convert a string to a safe filename by removing special characters.
    
    Args:
        s: Input string to convert
        fallback: Default name if conversion fails
        
    Returns:
        Safe filename string
    """
    if not isinstance(s, str) or not s.strip():
        return fallback
    s = s.strip().replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9_\-]", "", s)
    return s or fallback


def to_pdf_y(y_from_top: float, page_height: float) -> float:
    """
    Convert top-left (editor) coordinates to bottom-left (ReportLab) coordinates.
    
    Args:
        y_from_top: Y coordinate from top of page
        page_height: Total page height
        
    Returns:
        Y coordinate from bottom of page
    """
    return max(0, min(page_height, page_height - y_from_top))

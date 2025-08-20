"""
Template coordinate management for the Patient Report Generator.
Contains default field positions and coordinate calculation functions.
"""


def mosabbir_default_coords(page_width: float, page_height: float) -> dict:
    """
    Default field positions for the MOSABBIR template.
    Ratios were measured from the reference image (564x793), then
    converted to points by multiplying by the actual PDF page size.

    Coordinates are TOP-LEFT origin (editor space / PDF points).
    
    Args:
        page_width: PDF page width in points
        page_height: PDF page height in points
        
    Returns:
        Dictionary mapping field names to (x, y) coordinates in points
    """
    ratios = {
        # field_name: (x_ratio, y_ratio)
        "bed_id":            (0.390070922, 0.119798235),
        "name":              (0.407801418, 0.233291299),
        "age":               (0.407801418, 0.271122320),
        "gender":            (0.407801418, 0.308953342),
        "attendees":         (0.407801418, 0.346784363),
        "image":             (0.664893617, 0.208070618),  # TOP-LEFT of photo box
        "date_of_diagnosis": (0.425531915, 0.706179067),
        "cancer_type":       (0.425531915, 0.744010088),
        "cancer_stage":      (0.425531915, 0.781841110),
        "cancer_grade":      (0.425531915, 0.819672131),
    }
    
    return {
        k: (int(round(rx * page_width)), int(round(ry * page_height)))
        for k, (rx, ry) in ratios.items()
    }


def get_field_display_names() -> dict:
    """
    Get human-readable display names for field types.
    
    Returns:
        Dictionary mapping field names to display names
    """
    return {
        'bed_id': "Bed ID",
        'name': "Name", 
        'age': "Age", 
        'gender': "Gender",
        'attendees': "Attendees", 
        'date_of_diagnosis': "Date of Diagnosis",
        'cancer_type': "Cancer Type", 
        'cancer_stage': "Cancer Stage",
        'cancer_grade': "Cancer Grade", 
        'image': "Patient Image"
    }

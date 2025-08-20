"""
PDF report generation functionality.
Handles the creation of patient reports from templates and data.
"""

import os
import datetime
from io import BytesIO
from PIL import Image
from reportlab.pdfgen import canvas as rl_canvas
try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    # Fallback for older versions
    import PyPDF2
    PdfReader = PyPDF2.PdfFileReader
    PdfWriter = PyPDF2.PdfFileWriter

from .utils import slugify_filename, to_pdf_y


class ReportGenerator:
    """Handles PDF report generation from templates and patient data."""
    
    def __init__(self, template_path: str, field_coordinates: dict):
        """
        Initialize the report generator.
        
        Args:
            template_path: Path to the PDF template file
            field_coordinates: Dictionary mapping field names to (x, y) coordinates
        """
        self.template_path = template_path
        self.field_coordinates = field_coordinates

    def create_patient_report(self, patient_data, csv_dir: str, bed_id: int, output_dir: str = "reports"):
        """
        Create a PDF report for a single patient.
        
        Args:
            patient_data: Pandas Series containing patient information
            csv_dir: Directory containing the CSV file (for relative image paths)
            bed_id: Bed ID number for the patient
            output_dir: Directory to save the generated report
            
        Returns:
            Path to the generated report file
        """
        base_name = slugify_filename(str(patient_data.get('name', '')))
        output_path = os.path.join(output_dir, f"{base_name}_report.pdf")

        # Template & page size in points
        template_reader = PdfReader(self.template_path)
        template_page = template_reader.pages[0]
        page_width = float(template_page.mediabox.width)
        page_height = float(template_page.mediabox.height)

        # Create overlay at exact page size
        packet = BytesIO()
        can = rl_canvas.Canvas(packet, pagesize=(page_width, page_height))
        can.setFont("Helvetica", 12)

        # Draw text fields
        self._draw_text_fields(can, patient_data, bed_id, page_width, page_height)
        
        # Draw patient image
        self._draw_patient_image(can, patient_data, csv_dir, page_width, page_height)
        
        # Add timestamp
        self._add_timestamp(can, page_width)
        
        can.save()

        # Merge overlay with template
        packet.seek(0)
        overlay = PdfReader(packet).pages[0]
        base_page = template_page
        base_page.merge_page(overlay)
        
        writer = PdfWriter()
        writer.add_page(base_page)
        
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
            
        return output_path

    def _draw_text_fields(self, canvas, patient_data, bed_id: int, page_width: float, page_height: float):
        """Draw text fields on the canvas."""
        def draw_text(key, txt):
            if key in self.field_coordinates:
                x_top, y_top = self.field_coordinates[key]  # points, top-left
                x = max(0, min(page_width, float(x_top)))
                y = to_pdf_y(float(y_top), page_height)
                canvas.drawString(x, y, str(txt))

        # Draw all text fields
        draw_text('bed_id', f"{bed_id:02d}")
        draw_text('name', patient_data.get('name', ''))
        draw_text('age', patient_data.get('age', ''))
        draw_text('gender', patient_data.get('gender', ''))
        draw_text('attendees', patient_data.get('attendees', ''))
        draw_text('date_of_diagnosis', patient_data.get('date_of_diagnosis', ''))
        draw_text('cancer_type', patient_data.get('cancer_type', ''))
        draw_text('cancer_stage', patient_data.get('cancer_stage', ''))
        draw_text('cancer_grade', patient_data.get('cancer_grade', ''))

    def _draw_patient_image(self, canvas, patient_data, csv_dir: str, page_width: float, page_height: float):
        """Draw the patient image on the canvas."""
        if 'image' not in self.field_coordinates:
            return
            
        img_x_top, img_y_top = self.field_coordinates['image']
        img_x = max(0, min(page_width, float(img_x_top)))
        img_y = to_pdf_y(float(img_y_top), page_height)
        
        rel = str(patient_data.get('image_path', '')).strip()
        if not rel:
            self._draw_image_placeholder(canvas, img_x, img_y, "No image path")
            return
            
        img_path = os.path.normpath(os.path.join(csv_dir, rel))
        if not os.path.exists(img_path):
            self._draw_image_placeholder(canvas, img_x, img_y, "Image not found")
            return
            
        try:
            # Get image dimensions
            with Image.open(img_path) as im:
                iw, ih = im.size
                
            # Calculate size (max ~1.8 inches)
            max_side = 1.8 * 72.0  # Convert to points
            if iw >= ih:
                new_w, new_h = max_side, (ih / iw) * max_side
            else:
                new_h, new_w = max_side, (iw / ih) * max_side
                
            # Draw image
            canvas.drawImage(img_path, img_x, img_y - new_h,
                            width=new_w, height=new_h,
                            preserveAspectRatio=True, mask='auto')
                            
        except Exception as e:
            self._draw_image_placeholder(canvas, img_x, img_y, f"Image Error: {e}")

    def _draw_image_placeholder(self, canvas, x: float, y: float, message: str):
        """Draw a placeholder when image cannot be loaded."""
        canvas.setFont("Helvetica", 9)
        canvas.drawString(x, y, message)
        canvas.setFont("Helvetica", 12)

    def _add_timestamp(self, canvas, page_width: float):
        """Add a timestamp to the bottom of the page."""
        canvas.setFont("Helvetica", 8)
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        canvas.drawRightString(page_width - 20, 15, f"Generated: {stamp}")

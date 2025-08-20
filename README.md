# Automated Report Generation System

A professional Python application for generating patient reports from PDF templates and CSV data.

## Project Structure

The application has been refactored into a modular structure for better maintainability and readability:

```
Patient_bed/
├── main.py                 # Main entry point
├── src/                    # Source code package
│   ├── __init__.py        # Package initialization
│   ├── app.py             # Main application class
│   ├── utils.py           # Utility functions
│   ├── template_coords.py # Template coordinate management
│   ├── draggable_field.py # Draggable field implementation
│   ├── template_editor.py # Template field editor
│   └── report_generator.py # PDF report generation
├── requirements.txt        # Python dependencies
├── reports/               # Generated reports output
├── images/                # Patient images
└── patient data.csv       # Sample patient data
```

## Features

- **Template Management**: Load PDF templates and position form fields visually
- **Field Positioning**: Drag-and-drop interface for precise field placement
- **CSV Integration**: Import patient data from CSV files
- **Image Support**: Automatically include patient images in reports
- **Batch Processing**: Generate multiple reports at once
- **Professional UI**: Clean, intuitive interface with status updates

## Installation

1. **Clone or download** the project files
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Optional**: Install additional preview backends:
   - **PyMuPDF** (recommended): `pip install PyMuPDF`
   - **pdf2image**: `pip install pdf2image` + Poppler binaries

## Usage

### 1. Run the Application
```bash
python main.py
```

### 2. Select PDF Template
- Click "Browse Template" to select your PDF template
- The application will automatically apply default field positions
- Click "Position Fields" to fine-tune field placement

### 3. Load Patient Data
- Click "Browse CSV" to select your patient data file
- Ensure CSV contains required columns:
  - `name`, `age`, `gender`, `attendees`
  - `date_of_diagnosis`, `cancer_type`, `cancer_stage`, `cancer_grade`
  - `image_path` (relative path to patient images)

### 4. Generate Reports
- Click "Generate All Reports" to create PDF reports
- Reports are saved in the `reports/` folder

## CSV Format

Your CSV file should have the following structure:

```csv
name,age,gender,attendees,date_of_diagnosis,cancer_type,cancer_stage,cancer_grade,image_path
```

## Template Editor

The template editor provides:
- **Visual Field Positioning**: Drag red markers to position fields
- **Zoom Controls**: Adjust zoom level for precise positioning
- **Real-time Coordinates**: See exact PDF coordinates as you move fields
- **Template Preview**: View actual template (requires PyMuPDF or pdf2image)

## Dependencies

- **Core**: tkinter, pandas, PIL (Pillow), reportlab, PyPDF2
- **Optional**: PyMuPDF (recommended), pdf2image + Poppler



### Template Preview Issues
- Install PyMuPDF: `pip install PyMuPDF`
- Or install pdf2image + Poppler binaries
- The application will work with placeholder previews

### PDF Generation Errors
- Ensure template PDF is not corrupted
- Check field coordinates are within page bounds
- Verify CSV data format matches requirements

### Image Issues
- Ensure image paths in CSV are relative to CSV file location
- Supported formats: JPG, PNG, BMP, TIFF
- Images are automatically resized to fit template


"""
Template field editor for positioning form fields on PDF templates.
Provides a visual interface for adjusting field coordinates.
"""

import tkinter as tk
from tkinter import messagebox
import os
from PIL import Image, ImageTk
try:
    from PyPDF2 import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        # Fallback for older versions
        import PyPDF2
        PdfReader = PyPDF2.PdfFileReader

from .draggable_field import DraggableField
from .template_coords import mosabbir_default_coords, get_field_display_names

# ----- Optional preview backends -----
try:
    from pdf2image import convert_from_path as pdf2img_convert
    PDF2IMAGE_AVAILABLE = True
except Exception:
    PDF2IMAGE_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except Exception:
    PYMUPDF_AVAILABLE = False


class TemplateFieldEditor(tk.Toplevel):
    """Template field editor window for positioning form fields."""
    
    def __init__(self, parent, template_path):
        """
        Initialize the template field editor.
        
        Args:
            parent: Parent window
            template_path: Path to the PDF template file
        """
        super().__init__(parent)
        self.title("Template Field Editor")
        self.geometry("1000x1000")

        self.template_path = template_path
        self.field_coordinates = {}
        self.draggable_fields = {}

        self._base_image = None   # PIL image of page (rasterized)
        self._tk_image = None
        self.template_image_id = None

        # Read exact PDF page size (points)
        self.page_width, self.page_height = self._read_template_size()

        self.create_widgets()
        self.load_template_preview()
        self.initialize_field_coordinates()
    
    def _read_template_size(self):
        """Read the exact PDF page size in points."""
        try:
            r = PdfReader(self.template_path)
            page = r.pages[0]
            return float(page.mediabox.width), float(page.mediabox.height)
        except Exception:
            return 612.0, 792.0  # Letter fallback

    def create_widgets(self):
        """Create the user interface widgets."""
        main = tk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left: canvas
        left = tk.Frame(main, relief=tk.SUNKEN, borderwidth=2)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        cwrap = tk.Frame(left)
        cwrap.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(cwrap, bg="white")
        vbar = tk.Scrollbar(cwrap, orient=tk.VERTICAL, command=self.canvas.yview)
        hbar = tk.Scrollbar(cwrap, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        cwrap.grid_rowconfigure(0, weight=1)
        cwrap.grid_columnconfigure(0, weight=1)

        # Right: controls
        right = tk.Frame(main, width=360)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)

        # Template information
        info = tk.LabelFrame(right, text="Template Information", padx=10, pady=10)
        info.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(info, text=f"File: {os.path.basename(self.template_path)}",
                 wraplength=300).pack(anchor="w")
        self.status_label = tk.Label(info, text="Loading template...", fg="blue")
        self.status_label.pack(anchor="w", pady=(5, 0))
        self.method_label = tk.Label(info, text="", fg="green", wraplength=300)
        self.method_label.pack(anchor="w", pady=(2, 0))

        # Field information
        field_box = tk.LabelFrame(right, text="Draggable Fields", padx=10, pady=10)
        field_box.pack(fill=tk.X, padx=10, pady=10)
        self.field_list = tk.Text(field_box, height=10, width=30)
        self.field_list.pack(fill=tk.BOTH, expand=True)
        self.field_list.insert(
            tk.END,
            "Bed ID – Red cross\nName – Red cross\nAge – Red cross\nGender – Red cross\n"
            "Attendees – Red cross\nDate of Diagnosis – Red cross\nCancer Type – Red cross\n"
            "Cancer Stage – Red cross\nCancer Grade – Red cross\nPatient Image – Red rectangle\n\n"
            "Drag red markers; they turn blue while dragging."
        )
        self.field_list.config(state=tk.DISABLED)

        # Zoom controls
        zoom_frame = tk.LabelFrame(right, text="Zoom", padx=10, pady=10)
        zoom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Default to 0.5×
        self.zoom_var = tk.DoubleVar(value=0.5)
        zoom_scale = tk.Scale(
            zoom_frame,
            from_=0.3, to=3.0, resolution=0.1, orient=tk.HORIZONTAL,
            variable=self.zoom_var, command=self.on_zoom_change
        )
        zoom_scale.pack(fill=tk.X)
        
        # Show the correct initial value
        self.zoom_label = tk.Label(zoom_frame, text=f"Zoom: {int(self.zoom_var.get()*100)}%")
        self.zoom_label.pack()

        # Coordinates display
        coords_frame = tk.LabelFrame(right, text="Current Coordinates (PDF points)", padx=10, pady=10)
        coords_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.coords_text = tk.Text(coords_frame, height=12, width=30)
        self.coords_text.pack(fill=tk.BOTH, expand=True)

        # Buttons
        btns = tk.Frame(right)
        btns.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(btns, text="Save Coordinates", command=self.save_coordinates,
                  bg="#4CAF50", fg="white").pack(fill=tk.X, pady=3)
        tk.Button(btns, text="Reset to Default", command=self.reset_coordinates).pack(fill=tk.X, pady=3)
        tk.Button(btns, text="Reload Template", command=self.reload_template).pack(fill=tk.X, pady=3)
        tk.Button(btns, text="Close", command=self.destroy).pack(fill=tk.X, pady=3)

        # Initialize zoom after widget creation
        self.after(0, lambda: self.on_zoom_change(str(self.zoom_var.get())))

    def _current_display_size(self):
        """Get current display size based on zoom level."""
        z = float(self.zoom_var.get())
        if self._base_image is not None:
            w_img, h_img = self._base_image.size
            return int(w_img * z), int(h_img * z)
        return int(self.page_width * z), int(self.page_height * z)

    def get_scales(self):
        """Get pixels per point (x,y) at current zoom."""
        disp_w, disp_h = self._current_display_size()
        sx = (disp_w / self.page_width) if self.page_width else 1.0
        sy = (disp_h / self.page_height) if self.page_height else 1.0
        return sx, sy

    def load_template_preview(self):
        """Load and display the template preview."""
        self.canvas.delete("all")
        self.status_label.config(text="Loading template...", fg="blue")
        self.method_label.config(text="")
        self.update()

        pil_img = None

        # A) PyMuPDF (preferred – no external binaries)
        if PYMUPDF_AVAILABLE:
            try:
                self.status_label.config(text="Trying PyMuPDF...", fg="blue")
                self.update()
                doc = fitz.open(self.template_path)
                page = doc[0]
                mat = fitz.Matrix(2.0, 2.0)  # ~144 dpi
                pix = page.get_pixmap(matrix=mat)
                mode = "RGBA" if pix.alpha else "RGB"
                pil_img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                self.method_label.config(text="Method: PyMuPDF")
            except Exception:
                pil_img = None

        # B) pdf2image
        if pil_img is None and PDF2IMAGE_AVAILABLE:
            try:
                self.status_label.config(text="Trying pdf2image...", fg="blue")
                self.update()
                poppler_path = os.environ.get("POPPLER_PATH", None)  # optional on Windows
                imgs = pdf2img_convert(self.template_path, first_page=1, last_page=1, dpi=150,
                                       poppler_path=poppler_path)
                if imgs:
                    pil_img = imgs[0]
                    self.method_label.config(text="Method: pdf2image")
            except Exception:
                pil_img = None

        if pil_img is not None:
            self._base_image = pil_img
            self._redraw_template_image()
            self.status_label.config(text="Template loaded successfully!", fg="green")
        else:
            self.create_placeholder_template()
            self.status_label.config(
                text="Using placeholder (install PyMuPDF or pdf2image+Poppler for actual preview)",
                fg="orange"
            )

        # Rebuild fields at the final scale
        for f in self.draggable_fields.values():
            f.update_zoom_or_scale()

    def _redraw_template_image(self):
        """Redraw the template image at current zoom level."""
        if self._base_image is None:
            return
        z = float(self.zoom_var.get())
        w, h = self._base_image.size
        scaled = self._base_image.resize((max(1, int(w * z)), max(1, int(h * z))), Image.LANCZOS)
        self._tk_image = ImageTk.PhotoImage(scaled)
        if self.template_image_id:
            self.canvas.delete(self.template_image_id)
        self.template_image_id = self.canvas.create_image(0, 0, anchor="nw",
                                                          image=self._tk_image, tags="template")
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def create_placeholder_template(self):
        """Create a placeholder template when preview is not available."""
        z = float(self.zoom_var.get())
        w, h = int(self.page_width * z), int(self.page_height * z)
        self.canvas.create_rectangle(0, 0, w, h, outline="black", width=2, tags="template")
        self.canvas.create_text(w // 2, 20, text="Template Preview (Placeholder)",
                                font=("Arial", 12, "bold"), tags="template")
        self.canvas.create_text(w // 2, 40, text="Install PyMuPDF or pdf2image+Poppler for actual preview.",
                                font=("Arial", 10), tags="template")
        self.canvas.configure(scrollregion=(0, 0, w, h))

    def reload_template(self):
        """Reload the template preview."""
        self.load_template_preview()

    def initialize_field_coordinates(self):
        """Initialize field coordinates with MOSABBIR defaults."""
        self.field_coordinates = mosabbir_default_coords(self.page_width, self.page_height)
        self.create_draggable_fields()
        self.update_coordinates_display()

    def create_draggable_fields(self):
        """Create draggable field objects on the canvas."""
        field_names = get_field_display_names()
        self.canvas.delete("draggable")
        self.draggable_fields.clear()
        for fname, (x, y) in self.field_coordinates.items():
            self.draggable_fields[fname] = DraggableField(
                self.canvas, fname, field_names[fname], x, y,
                self.zoom_var, self.get_scales, self.page_width, self.page_height,
                on_move=self.update_coordinates_display
            )

    def on_zoom_change(self, value):
        """Handle zoom level changes."""
        zl = float(value)
        self.zoom_label.config(text=f"Zoom: {int(zl * 100)}%")
        if self._base_image is not None:
            self._redraw_template_image()
        else:
            self.create_placeholder_template()
        for f in self.draggable_fields.values():
            f.update_zoom_or_scale()
        self.update_coordinates_display()

    def update_coordinates_display(self):
        """Update the coordinates display text."""
        self.coords_text.config(state=tk.NORMAL)
        self.coords_text.delete(1.0, tk.END)
        for fname, field in self.draggable_fields.items():
            x, y = field.get_coordinates()  # PDF points (top-left)
            self.coords_text.insert(tk.END, f"{field.display_name}: ({x}, {y})\n")
            self.field_coordinates[fname] = (x, y)
        self.coords_text.config(state=tk.DISABLED)

    def save_coordinates(self):
        """Save the current field coordinates."""
        for fname, field in self.draggable_fields.items():
            self.field_coordinates[fname] = field.get_coordinates()
        self.saved = True
        messagebox.showinfo("Saved", "Coordinates saved successfully!")
        self.destroy()

    def reset_coordinates(self):
        """Reset coordinates to MOSABBIR defaults."""
        self.initialize_field_coordinates()
        messagebox.showinfo("Info", "Coordinates reset to MOSABBIR defaults.")

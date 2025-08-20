"""
Main application module for the Patient Report Generator.
Contains the main application window and user interface.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import os

from .template_editor import TemplateFieldEditor
from .report_generator import ReportGenerator
from .template_coords import mosabbir_default_coords, get_field_display_names


class SimplePatientReportGenerator:
    """Main application class for the Patient Report Generator."""
    
    def __init__(self, root):
        """
        Initialize the main application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Patient Report Generator")
        self.root.geometry("640x540")

        self.csv_path = None
        self.template_path = None
        
        # Default field coordinates (will be updated when template is selected)
        self.field_coordinates = {
            'bed_id': (182, 74),
            'name': (197, 170),
            'age': (197, 207),
            'gender': (197, 244),
            'attendees': (197, 289),
            'date_of_diagnosis': (317, 581),
            'cancer_type': (317, 618),
            'cancer_stage': (317, 653),
            'cancer_grade': (317, 683),
            'image': (386, 150)
        }

        # Create reports directory if it doesn't exist
        if not os.path.exists("reports"):
            os.makedirs("reports")

        self.create_widgets()

    def create_widgets(self):
        """Create the main user interface widgets."""
        tk.Label(self.root, text="Patient Report Generator",
                 font=("Arial", 18, "bold")).pack(pady=12)

        content = tk.Frame(self.root)
        content.pack(fill=tk.BOTH, expand=True, padx=20)

        # Template selection
        self._create_template_section(content)
        
        # CSV selection
        self._create_csv_section(content)
        
        # Coordinates display
        self._create_coordinates_section(content)
        
        # Generate button
        self._create_generate_section(content)
        
        # Status bar
        self._create_status_bar()

    def _create_template_section(self, parent):
        """Create the template selection section."""
        t_frame = tk.LabelFrame(parent, text="1. Select PDF Template", padx=10, pady=10)
        t_frame.pack(pady=8, fill="x")
        
        t_row = tk.Frame(t_frame)
        t_row.pack(fill="x")
        
        tk.Button(t_row, text="Browse Template", command=self.select_template, 
                  width=18, height=2, bg="#2196F3", fg="white", 
                  font=("Arial", 10, "bold")).pack(side="left", padx=8)
        
        self.template_label = tk.Label(t_row, text="No template selected",
                                       wraplength=320, justify="left")
        self.template_label.pack(side="left", padx=8)
        
        self.edit_template_button = tk.Button(t_row, text="Position Fields", 
                                             command=self.edit_template,
                                             width=15, height=2, bg="#FF9800", fg="white",
                                             font=("Arial", 10, "bold"), state=tk.DISABLED)
        self.edit_template_button.pack(side="right", padx=8)

    def _create_csv_section(self, parent):
        """Create the CSV selection section."""
        c_frame = tk.LabelFrame(parent, text="2. Select Patient Data CSV", padx=10, pady=10)
        c_frame.pack(pady=8, fill="x")
        
        c_row = tk.Frame(c_frame)
        c_row.pack(fill="x")
        
        tk.Button(c_row, text="Browse CSV", command=self.select_csv, 
                  width=18, height=2, bg="#2196F3", fg="white", 
                  font=("Arial", 10, "bold")).pack(side="left", padx=8)
        
        self.csv_label = tk.Label(c_row, text="No CSV file selected", 
                                  wraplength=320, justify="left")
        self.csv_label.pack(side="left", padx=8)

    def _create_coordinates_section(self, parent):
        """Create the coordinates display section."""
        coords_frame = tk.LabelFrame(parent, text="3. Current Field Positions (PDF points)",
                                     padx=10, pady=10)
        coords_frame.pack(pady=8, fill="both", expand=True)
        
        coords_container = tk.Frame(coords_frame)
        coords_container.pack(fill=tk.BOTH, expand=True)
        
        self.coords_text = tk.Text(coords_container, height=7, wrap=tk.WORD, font=("Arial", 9))
        coords_scroll = tk.Scrollbar(coords_container, command=self.coords_text.yview)
        self.coords_text.config(yscrollcommand=coords_scroll.set)
        
        self.coords_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        coords_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.update_coordinates_display()

    def _create_generate_section(self, parent):
        """Create the report generation section."""
        gen_frame = tk.LabelFrame(parent, text="4. Generate Reports", padx=10, pady=10)
        gen_frame.pack(pady=8, fill="x")
        
        tk.Button(gen_frame, text="Generate All Reports", command=self.generate_reports,
                  bg="#4CAF50", fg="white", font=("Arial", 14, "bold"),
                  width=24, height=2).pack(pady=6)

    def _create_status_bar(self):
        """Create the status bar at the bottom."""
        sbar = tk.Frame(self.root)
        sbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar(value="Ready – select template and CSV")
        tk.Label(sbar, textvariable=self.status_var, bd=1, relief=tk.SUNKEN,
                 anchor=tk.W, height=2).pack(fill=tk.X)

    def update_coordinates_display(self):
        """Update the coordinates display text."""
        self.coords_text.config(state=tk.NORMAL)
        self.coords_text.delete(1.0, tk.END)
        
        labels = get_field_display_names()
        
        self.coords_text.insert(tk.END, "Field positions (PDF points, top-left):\n\n")
        for k, (x, y) in self.field_coordinates.items():
            self.coords_text.insert(tk.END, f"{labels[k]}: ({int(x)}, {int(y)})\n")
        self.coords_text.insert(tk.END, "\nClick 'Position Fields' to adjust if needed.")
        self.coords_text.config(state=tk.DISABLED)

    def select_template(self):
        """Handle template file selection."""
        path = filedialog.askopenfilename(title="Select PDF Template",
                                          filetypes=[("PDF files", "*.pdf"),
                                                     ("All files", "*.*")])
        if path:
            self.template_path = path
            self.template_label.config(text=f"Selected: {os.path.basename(path)}")
            self.edit_template_button.config(state=tk.NORMAL)
            self.status_var.set(f"Template loaded: {os.path.basename(path)}")

            # Read real page size and immediately apply MOSABBIR defaults
            try:
                try:
                    from PyPDF2 import PdfReader
                except ImportError:
                    import PyPDF2
                    PdfReader = PyPDF2.PdfFileReader
                    
                r = PdfReader(self.template_path)
                p = r.pages[0]
                w, h = float(p.mediabox.width), float(p.mediabox.height)
                self.field_coordinates = mosabbir_default_coords(w, h)
                self.update_coordinates_display()
            except Exception:
                # keep previous coordinates if something goes wrong
                pass

    def select_csv(self):
        """Handle CSV file selection."""
        path = filedialog.askopenfilename(title="Select CSV File",
                                          filetypes=[("CSV files", "*.csv"),
                                                     ("All files", "*.*")])
        if path:
            try:
                df = pd.read_csv(path)
                required = ['name', 'age', 'gender', 'attendees', 'date_of_diagnosis',
                            'cancer_type', 'cancer_stage', 'cancer_grade', 'image_path']
                missing = [c for c in required if c not in df.columns]
                if missing:
                    messagebox.showerror("CSV Error",
                                         "Missing required columns:\n" +
                                         ", ".join(missing) +
                                         "\n\nRequired:\n" + ", ".join(required))
                    return
                self.csv_path = path
                self.csv_label.config(text=f"Selected: {os.path.basename(path)} ({len(df)} patients)")
                self.status_var.set(f"CSV loaded: {os.path.basename(path)} – {len(df)} rows")
            except Exception as e:
                messagebox.showerror("CSV Error", f"Error reading CSV:\n{e}")

    def edit_template(self):
        """Open the template field editor."""
        if not self.template_path:
            messagebox.showerror("Error", "Please select a template first")
            return
        editor = TemplateFieldEditor(self.root, self.template_path)
        self.root.wait_window(editor)
        if getattr(editor, 'saved', False):
            self.field_coordinates = editor.field_coordinates
            self.update_coordinates_display()
            self.status_var.set("Template field positions updated")

    def generate_reports(self):
        """Generate reports for all patients in the CSV."""
        if not self.csv_path:
            messagebox.showerror("Error", "Please select a CSV file")
            return
        if not self.template_path:
            messagebox.showerror("Error", "Please select a PDF template")
            return
            
        try:
            self.status_var.set("Reading CSV…")
            self.root.update()
            
            df = pd.read_csv(self.csv_path).fillna("")
            csv_dir = os.path.dirname(self.csv_path)

            # Create report generator
            generator = ReportGenerator(self.template_path, self.field_coordinates)

            ok, total = 0, len(df)
            for i, row in df.iterrows():
                try:
                    who = str(row.get('name', '')).strip() or f"Patient_{i+1}"
                    self.status_var.set(f"Generating report {i+1}/{total}: {who}")
                    self.root.update()
                    
                    generator.create_patient_report(row, csv_dir, bed_id=i + 1)
                    ok += 1
                except Exception as e:
                    messagebox.showwarning("Warning", f"Error for {row.get('name','Unknown')}: {e}")

            if ok == total:
                messagebox.showinfo("Success", f"Generated all {ok} reports.\nSee the 'reports' folder.")
            else:
                messagebox.showwarning("Partial Success", f"Generated {ok}/{total} reports.\nSee the 'reports' folder.")
            self.status_var.set(f"Done – {ok}/{total} generated")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.status_var.set("Error during report generation")

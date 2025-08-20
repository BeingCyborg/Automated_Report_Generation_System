"""
Draggable field implementation for the template editor.
Handles visual representation and interaction of form fields on the canvas.
"""

import tkinter as tk


class DraggableField:
    """
    Stores x,y in PDF POINTS (top-left origin).
    Converts to/from canvas pixels via scales provided by editor.
    """
    
    def __init__(self, canvas: tk.Canvas, field_name, display_name, x, y,
                 zoom_var, get_scales, page_width, page_height, on_move=None):
        """
        Initialize a draggable field.
        
        Args:
            canvas: Tkinter canvas to draw on
            field_name: Internal field identifier
            display_name: Human-readable field name
            x: X coordinate in PDF points (top-left)
            y: Y coordinate in PDF points (top-left)
            zoom_var: Tkinter variable for zoom level
            get_scales: Function returning (scale_x, scale_y) = px per point
            page_width: PDF page width in points
            page_height: PDF page height in points
            on_move: Callback function when field is moved
        """
        self.canvas = canvas
        self.field_name = field_name
        self.display_name = display_name
        self.x = float(x)  # PDF points (top-left)
        self.y = float(y)  # PDF points (top-left)
        self.zoom_var = zoom_var
        self.get_scales = get_scales  # returns (scale_x, scale_y) = px per point
        self.page_width = float(page_width)
        self.page_height = float(page_height)
        self.on_move = on_move

        self.drag_data = {"x": 0, "y": 0}
        self.rect_item = None
        self.h_line = None
        self.v_line = None
        self.label_item = None

        self.create_visual_elements()
        self.tag_bind()

    def _pt_to_px(self, x_pt, y_pt):
        """Convert PDF points to canvas pixels."""
        sx, sy = self.get_scales()
        return x_pt * sx, y_pt * sy

    def _px_to_pt_delta(self, dx_px, dy_px):
        """Convert pixel delta to PDF point delta."""
        sx, sy = self.get_scales()
        sx = sx if sx else 1.0
        sy = sy if sy else 1.0
        return dx_px / sx, dy_px / sy

    def create_visual_elements(self):
        """Create the visual representation of the field on the canvas."""
        self.canvas.delete(self.field_name)
        dx, dy = self._pt_to_px(self.x, self.y)

        if self.field_name == 'image':
            # Image field: red rectangle
            size_px = 80 * float(self.zoom_var.get())
            self.rect_item = self.canvas.create_rectangle(
                dx, dy, dx + size_px, dy + size_px,
                outline="red", width=3, fill="",
                tags=("draggable", self.field_name)
            )
        else:
            # Text field: red cross
            size_px = 12 * float(self.zoom_var.get())
            self.h_line = self.canvas.create_line(
                dx - size_px, dy, dx + size_px, dy,
                fill="red", width=3, tags=("draggable", self.field_name)
            )
            self.v_line = self.canvas.create_line(
                dx, dy - size_px, dx, dy + size_px,
                fill="red", width=3, tags=("draggable", self.field_name)
            )

        # Field label
        self.label_item = self.canvas.create_text(
            dx, dy - 20 * float(self.zoom_var.get()),
            text=self.display_name, fill="red",
            font=("Arial", int(10 * float(self.zoom_var.get())), "bold"),
            tags=("draggable", self.field_name)
        )

    def tag_bind(self):
        """Bind mouse events to the field elements."""
        for item in self.canvas.find_withtag(self.field_name):
            self.canvas.tag_bind(item, "<ButtonPress-1>", self.on_press)
            self.canvas.tag_bind(item, "<B1-Motion>", self.on_drag)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self.on_release)

    def on_press(self, event):
        """Handle mouse button press."""
        self.drag_data["x"], self.drag_data["y"] = event.x, event.y
        self._highlight(True)

    def on_drag(self, event):
        """Handle mouse drag motion."""
        dx_px, dy_px = event.x - self.drag_data["x"], event.y - self.drag_data["y"]
        dx_pt, dy_pt = self._px_to_pt_delta(dx_px, dy_px)
        
        # Update PDF coordinates with bounds checking
        self.x = min(max(0.0, self.x + dx_pt), self.page_width)
        self.y = min(max(0.0, self.y + dy_pt), self.page_height)
        
        self.drag_data["x"], self.drag_data["y"] = event.x, event.y
        self.canvas.move(self.field_name, dx_px, dy_px)
        
        if callable(self.on_move):
            self.on_move()

    def on_release(self, _):
        """Handle mouse button release."""
        self._highlight(False)
        if callable(self.on_move):
            self.on_move()

    def _highlight(self, active: bool):
        """Highlight the field when active."""
        color = "blue" if active else "red"
        for item in self.canvas.find_withtag(self.field_name):
            itype = self.canvas.type(item)
            if itype in ("text", "line"):
                self.canvas.itemconfig(item, fill=color)
            else:
                self.canvas.itemconfig(item, outline=color)

    def update_zoom_or_scale(self):
        """Update field display when zoom or scale changes."""
        self.create_visual_elements()
        self.tag_bind()

    def get_coordinates(self):
        """Get current coordinates in PDF points."""
        return int(round(self.x)), int(round(self.y))

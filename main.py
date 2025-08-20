#!/usr/bin/env python3


import tkinter as tk
from src.app import SimplePatientReportGenerator


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = SimplePatientReportGenerator(root)
    root.mainloop()


if __name__ == "__main__":
    main()

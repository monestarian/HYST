# file_utils.py
import os
from PySide6.QtWidgets import QFileDialog

def open_image_files(parent_window):
    # Define the file filters you want to allow
    file_filter = "TIFF Files (*.tif *.tiff);;ENVI Headers (*.hdr);;All Files (*)"
    
    # QFileDialog.getOpenFileNames returns a tuple: (file_paths, selected_filter)
    file_paths, _ = QFileDialog.getOpenFileNames(
        parent_window,                        # <--- We use parent_window instead of self
        "Open File",                          # Dialog Title
        os.getcwd(),                          # Starting Directory
        file_filter                           # File Filters
    )
    
    # Check if a file was actually selected (the user didn't hit cancel)
    if file_paths:
        print(f"File selected successfully: {file_paths}")
        # Loop through the list of selected files
        for path in file_paths:
            print(path)

    return file_paths
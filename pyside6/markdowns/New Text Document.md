# Hyperspectral Tool Development Notes

This document contains architectural notes and code snippets for building a PySide6-based Hyperspectral image processing tool, specifically focusing on handling `.tif` files, managing file dialogs, and building nested menus.

---

## Part 1: Requirements for Opening `.tif` Files

Opening a `.tif` (Tagged Image File Format) file depends on the complexity of the data inside it, as TIFF acts more like a container than a strict image format.

### 1. The Right Software or Library
* **Standard images (RGB/Grayscale):** Python libraries like `Pillow (PIL)` or `OpenCV`.
* **Scientific/Multidimensional Data (e.g., Hyperspectral):** Specialized libraries like `tifffile` are required to handle multi-page and complex scientific TIFF arrays (e.g., 200+ bands).
* **Spatial Data (GeoTIFFs):** GIS Python libraries like `rasterio` and `GDAL` are required to interpret both the image array and the spatial metadata.

### 2. Embedded Metadata (Tags)
The software relies on the **Image File Directory (IFD)** to construct the image. Key tags include:
* **ImageWidth & ImageLength:** Dimensions in pixels.
* **SamplesPerPixel (Bands):** Determines if it's Grayscale (1), RGB (3), or a multi-band array.
* **BitsPerSample:** Standard images are usually 8-bit or 16-bit; scientific data often uses 32-bit floating-point arrays.
* **PlanarConfiguration:** Defines whether pixel data is stored continuously (RGBRGB) or by band (RRR... GGG...).

### 3. Geospatial Information (For GeoTIFFs)
* **Coordinate Reference System (CRS):** Defines the map projection (e.g., WGS 84).
* **Affine Transform (Bounding Box):** Maps pixel coordinates to actual geographic coordinates.

---

## Part 2: PySide6 GUI Implementation

The following is the combined PySide6 implementation for the main application window. It includes:
1. Dynamic window sizing based on screen resolution.
2. An **Open File Dialog** configured to look for `.tif`, `.tiff`, and `.hdr` files.
3. **Nested Submenus** (e.g., "Export As..." under "File", and "Statistics" under "Basic Tools").

### Complete `main.py` Code

```python
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtCore import QSettings

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Create a settings object (Organization Name, Application Name)
        self.settings = QSettings("MyDevStudio", "SpatialApp")
        
        # Set up the main window properties
        self.setWindowTitle("Hyperspectral Tool")
        
        # Restore the previous geometry if it exists
        if self.settings.contains("window_geometry"):
            self.restoreGeometry(self.settings.value("window_geometry"))
        else:
            # Fallback size for the very first time they open the app
            screen_geometry = self.screen().availableGeometry()

            # Calculate 80% of the screen's width and height
            window_width = int(screen_geometry.width() * 0.62)
            window_height = int(screen_geometry.height() * 0.05)
    
            # Apply the size
            self.resize(window_width, window_height)
            
        # Initialize the menu bar
        self.create_menu_bar()
        
    def closeEvent(self, event):
        self.settings.setValue("window_geometry", self.saveGeometry())
        super().closeEvent(event)

    def create_menu_bar(self):
        # Create the main menu bar attached to the window
        menu_bar = self.menuBar()

        # The list of menus requested
        menu_categories = [
            "&File", "&Basic Tools", "&Classification", "&Transform",
            "F&ilter", "&Spectral", "&Map", "&Vector", "T&opographic",
            "&Radar", "&Window", "&Help"
        ]

        # Loop through the list to generate the top-level menus
        for category in menu_categories:
            menu = menu_bar.addMenu(category)
            clean_name = category.replace("&", "") 
            
            if clean_name == "File":
                open_image_file_action = menu.addAction("Open Image File...")
                open_image_file_action.triggered.connect(self.open_image_file)
                
                open_vector_file_action = menu.addAction("Open Vector File")
                menu.addSeparator()
                save_action = menu.addAction("Save")
                
                # --- SUBMENU: EXPORT ---
                export_submenu = menu.addMenu("Export As...") 
                export_submenu.addAction("ENVI Standard")     
                export_submenu.addAction("GeoTIFF")
                export_submenu.addAction("JPEG / PNG")
                # -----------------------
                
                change_output_directory_action = menu.addAction("Change Output Directory")
                menu.addSeparator()
                close_all_files_action = menu.addAction("Close All Files")
                menu.addSeparator()
                exit_action = menu.addAction("Exit")
                exit_action.triggered.connect(self.close) 
                
            if clean_name == "Basic Tools":
                Resize_Data_action = menu.addAction("Resize Data (Spatial/Spectral)")
                Subset_Data_via_ROIs_action = menu.addAction("Subset Data via ROIs")
                Rotate_Flip_Data_action = menu.addAction("Rotate/Flip Data")
                Layer_Stacking_action = menu.addAction("Layer Stacking")
                menu.addSeparator()
                Convert_Data_action = menu.addAction("Convert Data (BSQ, BIL, BIP)")
                Stretch_Data_action = menu.addAction("Stretch Data")
                menu.addSeparator()
                
                # --- SUBMENU: STATISTICS ---
                stats_submenu = menu.addMenu("Statistics") 
                stats_submenu.addAction("Compute New Statistics")
                stats_submenu.addAction("View Existing Statistics")
                
                spatial_stats_submenu = menu.addMenu("Spatial Statistics") 
                spatial_stats_submenu.addAction("Texture Filters")
                spatial_stats_submenu.addAction("Co-occurrence Measures")
                # ---------------------------
                
                Measurement_Tool_action = menu.addAction("Measurement Tool")
                menu.addSeparator()
                Band_Math_action = menu.addAction("Band Math")
                Spectral_Math_action = menu.addAction("Spectral Math")
                Segmentation_Image_action = menu.addAction("Segmentation Image")

            if clean_name == "Transform":
                Imaging_Sharpening_action = menu.addAction("Imaging Sharpening")
                menu.addSeparator()
                Band_Ratios_action = menu.addAction("Band Ratios")
                Principal_Components_action = menu.addAction("Principal Components")
                MNF_Rotation_action = menu.addAction("MNF Rotation")
                Color_Transforms_action = menu.addAction("Color Transforms")
                menu.addSeparator()
                Decorrelation_Stretch_action = menu.addAction("Decorrelation Stretch")
                Photographic_Stretch_action = menu.addAction("Photographic Stretch")
                Saturation_Stretch_action = menu.addAction("Saturation Stretch")
                Synthetic_Color_Image_action = menu.addAction("Synthetic Color Image")

            if clean_name == "Window":
                Window_Finder_action = menu.addAction("Window Finder")
                menu.addSeparator()
                Start_New_Display_Window_action = menu.addAction("Start New Display Window")
                menu.addSeparator()
                Available_Files_List_action = menu.addAction("Available Files List")
                Available_Bands_List_action = menu.addAction("Available Bands List")
                menu.addSeparator()
                Mouse_Button_Description_action = menu.addAction("Mouse Button Description")
                Display_Information_action = menu.addAction("Display Information")
                Cursor_Location_Value_action = menu.addAction("Cursor Location/Value")
                Point_Colection_action = menu.addAction("Point Colection")
                menu.addSeparator()
                Maximize_Open_Displays_action = menu.addAction("Maximize Open Displays")
                Link_Displays_action = menu.addAction("Link Displays")
                menu.addSeparator()
                Close_Display_Windows_action = menu.addAction("Close Display Windows")
                Close_All_Plot_Windows_action = menu.addAction("Close All Plot Windows")

            if clean_name == "Help":
                Start_Help_Section_action = menu.addAction("Start Help Section")
                Mouse_Button_Description_action = menu.addAction("Mouse Button Description")
                About_Hyperspectral_Tool_action = menu.addAction("About Hyperspectral Tool")

    def open_image_file(self):
        # Open a file dialog targeting standard formats and hyperspectral data
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Hyperspectral Image",
            "",
            "TIFF Files (*.tif *.tiff);;ENVI Headers (*.hdr);;All Files (*)"
        )
        
        if file_path:
            print(f"File selected successfully: {file_path}")
            # Implementation for loading the file data (e.g., via rasterio or tifffile) goes here


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
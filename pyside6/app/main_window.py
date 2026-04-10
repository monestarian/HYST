import sys
import os
#from PySide6 import QtWidgets
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QFileDialog, QLabel
from PySide6.QtCore import QSettings
import open
import opentif
#import file_utils

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.active_image_files=[]
        # Create a settings object (Organization Name, Application Name)
        self.settings = QSettings("MyDevStudio", "SpatialApp")
        
        # Set up the main window properties
        self.setWindowTitle("Hyperspectral Tool")
        #self.setGeometry(100, 100, 800, 600) # (x, y, width, height)
        
        # Restore the previous geometry if it exists
        if self.settings.contains("window_geometry"):
            self.restoreGeometry(self.settings.value("window_geometry"))
        else:
            # Fallback size for the very first time they open the app
            # self.resize(1024, 768)
            # Get the geometry of the primary screen
            screen_geometry = self.screen().availableGeometry()

            # Calculate 80% of the screen's width and height
            window_width = int(screen_geometry.width() * 0.62)
            window_height = int(screen_geometry.height() * 0.05)
    
            # Apply the size
            self.resize(window_width, window_height)
            
        # Initialize the menu bar
        self.create_menu_bar()
    
    def catch_open_actions(self):
        # 1. Run the external file and CATCH the returned list in a temporary variable
        new_files = open.open_image_files(self)
        
        # 2. Check if the user actually selected something (didn't hit cancel)
        if new_files:
            # 3. Store the new files in our permanent class variable
            self.active_image_files = new_files
            
            # Print it out to prove the Main Window remembers it!
            print(f"SUCCESS: The Main Window has stored {len(self.active_image_files)} files in memory!")
            print(f"Current stored files: {self.active_image_files}")

    def closeEvent(self, event):
        self.settings.setValue("window_geometry", self.saveGeometry())
        super().closeEvent(event)

    def create_menu_bar(self):
        # Create the main menu bar attached to the window
        menu_bar = self.menuBar()

        # The list of menus you requested
        menu_categories = [
            "&File", "&Basic Tools", "&Classification", "&Transform",
            "F&ilter", "&Spectral", "&Map", "&Vector", "T&opographic",
            "&Radar", "&Window", "&Help"
        ]

        # Loop through the list to generate the top-level menus
        for category in menu_categories:
            menu = menu_bar.addMenu(category)
            
            # --- Adding Drop-Down Options (Actions) ---
            clean_name = category.replace("&", "") # Removing the ampersand for the action name
            def dunempty(a):
                pass
            a=True        
            if clean_name == "File":
                open_image_file_action = menu.addAction("Open Image File BLANK")
                #open_image_file_action.triggered.connect(open.open_image_files(self))#Pyside6 by default returns a False whenever a button is clicked, so if lambda is not inserted or some empty function, the open image file function receives the false and stops
                open_image_file_action.triggered.connect(lambda: self.catch_open_actions()) #we need to pass self in this function because we need to tell it which is the main window which needs to be locked until the task in this window is complete.
                
                clear_open_list_action = menu.addAction("Clear \"Open Image File List\"")
                #clear_open_list_action.triggered.connect(lambda: )

                menu.addSeparator()

                open_external_file = menu.addMenu("Open External File")  # Use addMenu here
                open_avrisng_file = open_external_file.addMenu("AVRIS-NG")  
                open_prisma_file = open_external_file.addMenu("PRISMA")
                open_eo1_file = open_external_file.addMenu("EO1-Hyperion")
                open_prisma_file = open_external_file.addMenu("Prisma")
                open_enmap_file = open_external_file.addMenu("EnMap")
                open_l2_file = open_enmap_file.addAction(".tif file")
                open_l2_file.triggered.connect(lambda: self.openl2())    
                menu.addSeparator()
                open_generic_format = menu.addMenu("Open Generic File Formats")
                open_envi_file_action = open_generic_format.addAction("ENVI Standard")     # Add actions to the submenu
                open_tif_file = open_generic_format.addAction("GeoTIFF")
                open_he5_file = open_generic_format.addAction("HE5")
                open_jpgpng_file = open_generic_format.addAction("JPEG/PNG")
                menu.addSeparator()
                save_action = menu.addAction("Save BLANK")
                change_output_directory_action = menu.addAction("Change Output Directory BLANK")
                menu.addSeparator()
                close_all_files_action = menu.addAction("Close All Files BLANK")
                menu.addSeparator()
                exit_action = menu.addAction("Exit BLANK")
                exit_action.triggered.connect(self.close)# Connect the exit action to actually close the app
                

            if clean_name == "Basic Tools":
                # The menu gets specific examples
                Resize_Data_action = menu.addAction("Resize Data (Spatial/Spectral) BLANK")
                Subset_Data_via_ROIs_action = menu.addAction("Subset Data via ROIs BLANK")
                Rotate_Flip_Data_action = menu.addAction("Rotate/Flip Data BLANK")
                Layer_Stacking_action = menu.addAction("Layer Stacking BLANK")
                menu.addSeparator()
                Convert_Data_action = menu.addAction("Convert Data (BSQ, BIL, BIP) BLANK")
                Stretch_Data_action = menu.addAction("Stretch Data BLANK")
                menu.addSeparator()
                Statistics_action = menu.addAction("Statistics BLANK")
                Spatial_Statistics_action = menu.addAction("Spatial Statistics BLANK")
                Measurement_Tool_action = menu.addAction("Measurement Tool BLANK")
                menu.addSeparator()
                Band_Math_action = menu.addAction("Band Math BLANK")
                Spectral_Math_action = menu.addAction("Spectral Math BLANK")
                Segmentation_Image_action = menu.addAction("Segmentation Image BLANK")


                #menu.addSeparator() # Adds a visual divider line
                #exit_action = menu.addAction("Exit")
                
                # Connect the exit action to actually close the app
                #exit_action.triggered.connect(self.close)
            
            if clean_name == "Tools":
                # The menu gets specific examples
                open_action = menu.addAction(" BLANK")
                save_action = menu.addAction(" BLANK")
                #menu.addSeparator() # Adds a visual divider line
                #exit_action = menu.addAction("Exit")
                
                # Connect the exit action to actually close the app
                #exit_action.triggered.connect(self.close)
            
            if clean_name == "Classification":
                # The menu gets specific examples
                open_action = menu.addAction(" BLANK")
                save_action = menu.addAction(" BLANK")
                #menu.addSeparator() # Adds a visual divider line
                #exit_action = menu.addAction("Exit")
                
                # Connect the exit action to actually close the app
                #exit_action.triggered.connect(self.close)
            
            if clean_name == "Transform":
                # The menu gets specific examples
                Imaging_Sharpening_action = menu.addAction("Imaging Sharpening BLANK")
                menu.addSeparator()
                Band_Ratios_action = menu.addAction("Band Ratios BLANK")
                Principal_Components_action = menu.addAction("Principal Components BLANK")
                MNF_Rotation_action = menu.addAction("MNF Rotation BLANK")
                Color_Transforms_action = menu.addAction("Color Transforms BLANK")
                menu.addSeparator()
                Decorrelation_Stretch_action = menu.addAction("Decorrelation Stretch BLANK")
                Photographic_Stretch_action = menu.addAction("Photographic Stretch BLANK")
                Saturation_Stretch_action = menu.addAction("Saturation Stretch BLANK")
                Synthetic_Color_Image_action = menu.addAction("Synthetic Color Image BLANK")
                #menu.addSeparator() # Adds a visual divider line
                #exit_action = menu.addAction("Exit")
                
                # Connect the exit action to actually close the app
                #exit_action.triggered.connect(self.close)
            
            if clean_name == "Filter":
                # The menu gets specific examples
                open_action = menu.addAction(" BLANK")
                save_action = menu.addAction(" BLANK")
                #menu.addSeparator() # Adds a visual divider line
                #exit_action = menu.addAction("Exit")
                
                # Connect the exit action to actually close the app
                #exit_action.triggered.connect(self.close)
            
            if clean_name == "Spectral":
                # The menu gets specific examples
                open_action = menu.addAction(" BLANK")
                save_action = menu.addAction(" BLANK")
                #menu.addSeparator() # Adds a visual divider line
                #exit_action = menu.addAction("Exit")
                
                # Connect the exit action to actually close the app
                #exit_action.triggered.connect(self.close)
            
            if clean_name == "Map":
                # The menu gets specific examples
                open_action = menu.addAction(" BLANK")
                save_action = menu.addAction(" BLANK")
                #menu.addSeparator() # Adds a visual divider line
                #exit_action = menu.addAction("Exit")
                
                # Connect the exit action to actually close the app
                #exit_action.triggered.connect(self.close)

            #menu-bar items blank for now:        
            if clean_name == "Vector":
                # The menu gets specific examples
                open_action = menu.addAction(" BLANK")
                save_action = menu.addAction(" BLANK")
                #menu.addSeparator() # Adds a visual divider line
                #exit_action = menu.addAction("Exit")
                
                # Connect the exit action to actually close the app
                #exit_action.triggered.connect(self.close)
            
            if clean_name == "Topographic":
                # The menu gets specific examples
                open_action = menu.addAction(" BLANK")
                save_action = menu.addAction(" BLANK")
                #menu.addSeparator() # Adds a visual divider line
                #exit_action = menu.addAction("Exit")
                
                # Connect the exit action to actually close the app
                #exit_action.triggered.connect(self.close)
            
            if clean_name == "Radar":
                # The menu gets specific examples
                open_action = menu.addAction(" BLANK")
                save_action = menu.addAction(" BLANK")
                #menu.addSeparator() # Adds a visual divider line
                #exit_action = menu.addAction("Exit")
                
                # Connect the exit action to actually close the app
                #exit_action.triggered.connect(self.close)'''
            
            if clean_name == "Window":
                # The menu gets specific examples
                Window_Finder_action = menu.addAction("Window Finder BLANK")
                menu.addSeparator()
                Start_New_Display_Window_action = menu.addAction("Start New Display Window BLANK")
                menu.addSeparator()
                Available_Files_List_action = menu.addAction("Available Files List BLANK")
                Available_Bands_List_action = menu.addAction("Available Bands List BLANK")
                menu.addSeparator()
                Mouse_Button_Description_action = menu.addAction("Mouse Button Description BLANK")
                Display_Information_action = menu.addAction("Display Information BLANK")
                Cursor_Location_Value_action = menu.addAction("Cursor Location/Value BLANK")
                Point_Colection_action = menu.addAction("Point Colection BLANK")
                menu.addSeparator()
                Maximize_Open_Displays_action = menu.addAction("Maximize Open Displays BLANK")
                Link_Displays_action = menu.addAction("Link Displays BLANK")
                menu.addSeparator()
                Close_Display_Windows_action = menu.addAction("Close Display Windows BLANK")
                Close_All_Plot_Windows_action = menu.addAction("Close All Plot Windows BLANK")
                #menu.addSeparator() # Adds a visual divider line
                #exit_action = menu.addAction("Exit")
                
                # Connect the exit action to actually close the app
                #exit_action.triggered.connect(self.close)
            
            if clean_name == "Help":
                # The menu gets specific examples
                Start_Help_Section_action = menu.addAction("Start Help Section BLANK")
                Mouse_Button_Description_action = menu.addAction("Mouse Button Description BLANK")
                About_Hyperspectral_Tool_action = menu.addAction("About Hyperspectral Tool BLANK")
                #menu.addSeparator() # Adds a visual divider line
                #exit_action = menu.addAction("Exit")
                
                # Connect the exit action to actually close the app
                #exit_action.triggered.connect(self.close)
            
            
            
            '''else:
                # Generic placeholders for the rest of the menus
                menu.addAction(f"{clean_name} Option 1 BLANK")
                menu.addAction(f"{clean_name} Option 2 BLANK")'''
    '''def open_image_files(self):
        # Define the file filters you want to allow
        file_filter = "TIFF Files (*.tif *.tiff);;ENVI Headers (*.hdr);;All Files (*)"
        
        # QFileDialog.getOpenFileName returns a tuple: (file_path, selected_filter)
        # We use an underscore '_' for the second variable since we don't need it right now.
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,                                 # Parent
            "Open File",           # Dialog Title (Caption)
            os.getcwd(),                          # Starting Directory
            file_filter                           # File Filters
        )
        
        #debug method for file selector        
        # Check if a file was actually selected (the user didn't hit cancel)
        if file_paths:
            print(f"File selected successfully: {file_paths}")
            # Add your code here to actually load the file data (e.g., rasterio, tifffile, etc.)
            # Loop through the list of selected files
            for path in file_paths:
                print(path)
        
        
        return file_paths
'''
    

    # functions for open external files:

    #file
    
    #open external file

    #enmap
    def openl2(self):
        filepath = "sample.tif"

        self.viewer = opentif.TifViewerWindow(filepath, parent=self)  # <-- set parent
        self.viewer.show()
    
    '''
        if file_path:   
            # Instantiate the class you wrote, passing the file_path string
            self.active_viewer = TifViewerWindow(filepath=file_path)
            
            # Show the newly created window
            self.active_viewer.show()
    '''

if __name__ == "__main__":
    # Every PySide6 application requires exactly one QApplication instance
    app = QApplication(sys.argv)
    
    # Create and display the window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())
    
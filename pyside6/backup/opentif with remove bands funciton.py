import sys
import numpy as np
import rasterio
from rasterio.warp import transform  # ✅ ADDED
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                               QVBoxLayout, QFormLayout, QRadioButton, QSpinBox, 
                               QPushButton, QGroupBox, QMessageBox, QLabel, QComboBox, QInputDialog)
from PySide6.QtCore import Qt

# Imports for embedding Matplotlib in PySide6
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from tif_open_largegrapwindow import SpectralWindow                                             #open large graph window button function
from removebands import remove_bands as remove_bands_external

class TifViewerWindow(QMainWindow):
    
    def __init__(self, filepaths, parent=None):
        super().__init__(parent)

        self.filepaths = filepaths if isinstance(filepaths, list) else [filepaths]
        self.filepath = self.filepaths[0] if self.filepaths else None

        self.setWindowTitle(f"Hyperspectral Viewer - {self.filepath}")
        self.resize(1000, 700)

        self.create_menu_bar()
        
        self.load_file_metadata()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        self.canvas = FigureCanvas(Figure(figsize=(8, 6), layout='compressed'))
        self.ax = self.canvas.figure.subplots()
        self.ax.axis('off')
        main_layout.addWidget(self.canvas, stretch=3)
        
        controls_layout = QVBoxLayout()
        main_layout.addLayout(controls_layout, stretch=1)
        
        self.setup_control_panel(controls_layout)

        self.canvas.mpl_connect('button_press_event', self.on_image_click)

        self.spectral_mode = False

        self.spectral_window = None
        
        self.render_image()

    def create_menu_bar(self):
        menu_bar = self.menuBar()

        menu_categories = [
            "&Basic Tools", "&Transform", "&Edit"
        ]

        for category in menu_categories:
            menu = menu_bar.addMenu(category)
            clean_name = category.replace("&", "")

            def dunempty(a):
                pass
            a=True        

            if clean_name == "Basic Tools":
                menu.addAction("Resize Data (Spatial/Spectral) BLANK")                  #Changes the spatial resolution (pixel size) or subsets the spectral dimensions (reducing the number of bands).
                #menu.addAction("Subset Data via ROIs BLANK")                           #Crops a large geographic image into a smaller piece based on a user-drawn polygon or shapefile.
                menu.addAction("Rotate/Flip Data BLANK")                                #Rotates the image by degrees or mirrors it vertically/horizontally
                menu.addSeparator()                                                     
                menu.addAction("Stretch Data BLANK")                                    #Applies contrast enhancements (like linear 2% stretch, histogram equalization, or Gaussian stretches) to make features visible on a screen.
                menu.addSeparator()
                menu.addAction("Statistics BLANK")                                      #gives global band info (Min, Max, Mean, Standard Deviation)
                menu.addAction("Spatial Statistics BLANK")                              #analyzes local texture and variance using a moving window.
                #menu.addAction("Measurement Tool BLANK")
                menu.addSeparator()                                                     
                menu.addAction("Band Math BLANK")                                       #Allows you to perform mathematical operations between specific individual bands
                menu.addAction("Spectral Math BLANK")                                   #similar to Band Math, but operates on entire spectral profiles/signatures (the z-axis vector of a pixel) rather than just single bands.
                #menu.addAction("Segmentation Image BLANK")                              #Groups adjacent pixels with similar spectral or spatial characteristics into continuous objects (polygons).

            if clean_name == "Transform":
                menu.addAction("Band Ratios BLANK")                                     #Simply divides the pixel values of one band by the values of another.
                menu.addAction("Principal Components BLANK")                            #A mathematical transformation that reorganizes the data. It takes highly correlated bands and converts them into new, uncorrelated "components" (Component 1 contains the most variance, Component 2 the second most, etc.)
                menu.addAction("MNF Rotation BLANK")                                    #It is a two-step transformation designed specifically for hyperspectral data. It first isolates and models the noise in the data, and then applies a Principal Components Analysis (PCA) to the noise-whitened data.
                #menu.addAction("Color Transforms BLANK")                                #
                menu.addSeparator()
                menu.addAction("Decorrelation Stretch BLANK")                           #It exaggerates the color differences in an RGB image. It takes highly correlated bands, separates them in "color space", stretches them, and puts them back together.
                menu.addAction("Photographic Stretch BLANK")                            #Non-linear contrast stretches designed to make raw satellite imagery look more like a photograph taken by a traditional camera.
                #menu.addAction("Imaging Sharpening BLANK")                              #Fuses low-resolution color/spectral bands with a high-resolution, single-band (panchromatic) black-and-white image to create a high-resolution color image.
                #menu.addSeparator()                                     
                #menu.addAction("Saturation Stretch BLANK")                              #
                #menu.addAction("Synthetic Color Image BLANK")                           #Simulates a true-color image from non-visible bands, or creates a color image based on density slicing a single band.

            if clean_name == "Edit":
                remove_action = menu.addAction("Remove Bands")                          #remove bad bands manually by entering each band manually
                remove_action.triggered.connect(self.remove_bands)
                menu.addSeparator()

                filter_action = menu.addAction("Apply Filters")
                #filter_action.triggered.connect(self.filters)
    

    #functions
    # basic tools
    # transform
    # edit
    def remove_bands(self):
        if not self.filepath:
            return

        text, ok = QInputDialog.getText(self, "Remove Bands", 
                                       "Enter band indices to remove (comma separated):")
        if not ok or not text:
            return

        try:
            bands_to_remove = sorted([int(b.strip()) for b in text.split(",") if b.strip()])
            
            with rasterio.open(self.filepath) as src:
                data = src.read()
                profile = src.profile

            total_bands = data.shape[0]
            keep_indices = [i for i in range(total_bands) if (i+1) not in bands_to_remove]

            if not keep_indices:
                QMessageBox.warning(self, "Error", "Cannot remove all bands.")
                return

            new_data = data[keep_indices, :, :]

            save_path = self.filepath.replace(".tif", "_bands_removed.tif")

            profile.update(count=new_data.shape[0])

            with rasterio.open(save_path, 'w', **profile) as dst:
                dst.write(new_data)

            QMessageBox.information(self, "Success", f"Saved file:\n{save_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove bands:\n{e}")

    #ADDED METHOD (CRS Conversion)
    def convert_to_wgs84(self, src, x, y):
        try:
            lon_native, lat_native = rasterio.transform.xy(src.transform, y, x)
            lon, lat = transform(src.crs, "EPSG:4326", [lon_native], [lat_native])
            return lat[0], lon[0]
        except:
            return 0.0, 0.0

    #ADDED METHOD (Strict Formatting)
    def format_latlon(self, lat, lon):
        return f"Lat: {lat:.5f} | Lon: {lon:.5f}"

    def load_file_metadata(self):
        try:
            with rasterio.open(self.filepath) as src:
                self.max_bands = src.count
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {e}")
            self.max_bands = 1
    
    #The architect of right side panel
    def setup_control_panel(self, layout):
        
        layout.addWidget(QLabel("<b>Select File:</b>"))
        self.file_selector = QComboBox()
        self.file_selector.addItems(self.filepaths)
        self.file_selector.currentIndexChanged.connect(self.on_file_changed)
        layout.addWidget(self.file_selector)

        self.info_label = QLabel(f"<b>Total Bands Available:</b> {self.max_bands}")
        layout.addWidget(self.info_label)
        
        mode_group = QGroupBox("Visualization Mode")
        mode_layout = QVBoxLayout()
        
        self.radio_rgb = QRadioButton("RGB Composite")
        self.radio_rgb.setChecked(True)
        self.radio_rgb.toggled.connect(self.toggle_ui_mode)
        
        self.radio_gray = QRadioButton("Grayscale (Single Band)")
        
        mode_layout.addWidget(self.radio_rgb)
        mode_layout.addWidget(self.radio_gray)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        bands_group = QGroupBox("Band Selection")
        bands_layout = QFormLayout()
        
        def create_spinbox(default_val):
            sb = QSpinBox()
            sb.setMinimum(1)
            sb.setMaximum(self.max_bands)
            sb.setValue(min(default_val, self.max_bands))
            return sb

        self.spin_r = create_spinbox(45)
        self.spin_g = create_spinbox(29)
        self.spin_b = create_spinbox(15)
        
        self.label_r = QLabel("Red Band:")
        self.label_g = QLabel("Green Band:")
        self.label_b = QLabel("Blue Band:")
        
        bands_layout.addRow(self.label_r, self.spin_r)
        bands_layout.addRow(self.label_g, self.spin_g)
        bands_layout.addRow(self.label_b, self.spin_b)
        
        bands_group.setLayout(bands_layout)
        layout.addWidget(bands_group)
        
        self.btn_update = QPushButton("Update Image")
        self.btn_update.setMinimumHeight(40)
        self.btn_update.clicked.connect(self.render_image)
        layout.addWidget(self.btn_update)

        self.btn_spectral = QPushButton("View Spectral Signature")
        self.btn_spectral.setMinimumHeight(40)
        self.btn_spectral.setCheckable(True)
        self.btn_spectral.clicked.connect(self.toggle_spectral_mode)
        layout.addWidget(self.btn_spectral)

        self.btn_open_window = QPushButton("Open Large Graph Window")
        self.btn_open_window.setMinimumHeight(40)
        self.btn_open_window.clicked.connect(self.open_spectral_window)
        layout.addWidget(self.btn_open_window)

        self.spec_canvas = FigureCanvas(Figure(figsize=(3, 2)))
        self.ax_spec = self.spec_canvas.figure.subplots()
        self.ax_spec.set_title("Spectral Signature")
        self.ax_spec.set_xlabel("Band")
        self.ax_spec.set_ylabel("Intensity")
        self.ax_spec.grid(True)

        self.spec_canvas.setVisible(False)
        layout.addWidget(self.spec_canvas)
        
        layout.addStretch()

    #toggle spectral graph on and off
    def toggle_spectral_mode(self):
        self.spectral_mode = self.btn_spectral.isChecked()
        self.spec_canvas.setVisible(self.spectral_mode)

    def open_spectral_window(self):
        if self.spectral_window is None:
            self.spectral_window = SpectralWindow(self)
        self.spectral_window.show()

    def on_image_click(self, event):
        if not self.spectral_mode:
            return
        if event.xdata is None or event.ydata is None:
            return

        x, y = int(event.xdata), int(event.ydata)

        try:
            with rasterio.open(self.filepath) as src:
                spectrum = src.read()[:, y, x]

                # ✅ UPDATED: Convert + Format
                lat, lon = self.convert_to_wgs84(src, x, y)
                coord_text = self.format_latlon(lat, lon)

            self.ax_spec.clear()
            self.ax_spec.plot(spectrum)
            self.ax_spec.set_title(f"({x},{y})\n{coord_text}")
            self.ax_spec.set_xlabel("Band")
            self.ax_spec.set_ylabel("Intensity")
            self.ax_spec.grid(True)

            self.spec_canvas.draw()

            if self.spectral_window is not None:
                self.spectral_window.update_plot(
                    spectrum, x, y,
                    f"Lat: {lat:.5f}", f"Lon: {lon:.5f}",
                    self.filepath
                )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed:\n{e}")

    def on_file_changed(self, index):
        self.filepath = self.filepaths[index]

        self.load_file_metadata()

        self.info_label.setText(f"<b>Total Bands Available:</b> {self.max_bands}")
        self.setWindowTitle(f"Hyperspectral Viewer - {self.filepath}")

        self.spin_r.setMaximum(self.max_bands)
        self.spin_g.setMaximum(self.max_bands)
        self.spin_b.setMaximum(self.max_bands)

        self.render_image()

    def toggle_ui_mode(self):
        is_rgb = self.radio_rgb.isChecked()
        
        self.spin_g.setVisible(is_rgb)
        self.spin_b.setVisible(is_rgb)
        self.label_g.setVisible(is_rgb)
        self.label_b.setVisible(is_rgb)
        
        self.label_r.setText("Red Band:" if is_rgb else "Gray Band:")

    #draws the image onto the screen
    def render_image(self):
        try:
            with rasterio.open(self.filepath) as src:
                vmin_val = 110.0
                vmax_val = 2000.0
                
                self.ax.clear()
                self.ax.axis('off')
                
                if self.radio_rgb.isChecked():
                    r = src.read(self.spin_r.value())
                    g = src.read(self.spin_g.value())
                    b = src.read(self.spin_b.value())
                    
                    img = np.dstack((r, g, b))
                    img = np.clip(img, vmin_val, vmax_val)
                    img = (img - vmin_val) / (vmax_val - vmin_val)
                    
                    self.ax.imshow(img)
                else:
                    gray = src.read(self.spin_r.value())
                    gray = np.clip(gray, vmin_val, vmax_val)
                    gray = (gray - vmin_val) / (vmax_val - vmin_val)
                    
                    self.ax.imshow(gray, cmap='gray')
                
                self.canvas.draw()
                
        except Exception as e:
            QMessageBox.critical(self, "Rendering Error", f"Could not load bands:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    file_list = [
        "sample - Copy.tif", "sample - Copy_bands_removed.tif",
    ]
        
    viewer = TifViewerWindow(file_list)
    viewer.show()
    
    sys.exit(app.exec())

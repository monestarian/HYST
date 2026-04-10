import numpy as np
import rasterio
from rasterio.warp import transform
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                               QFormLayout, QGroupBox, QLineEdit, 
                               QPushButton, QLabel, QComboBox, QMessageBox)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


def wgs84_to_utm(lon, lat):
    """
    Convert WGS84 coordinates to UTM zone.
    Returns (zone_number, zone_letter, easting, northing)
    """
    from math import floor
    
    # Calculate UTM zone
    zone_number = floor((lon + 180) / 6) + 1
    
    # Determine hemisphere
    if lat >= 0:
        zone_letter = 'N'
    else:
        zone_letter = 'S'
    
    # EPSG code for UTM zone (northern hemisphere)
    epsg = 32600 + zone_number
    
    return epsg, zone_number, zone_letter


class SpectralWindow(QMainWindow):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.filepathforgraph = ""
        self.setWindowTitle("Spectral Signature Viewer")
        self.resize(600, 400)

        # Create central widget with layout to hold both controls and canvas
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Manual coordinate input section
        self.coord_group = QGroupBox("Manual Coordinate Input")
        coord_layout = QFormLayout()
        
        self.input_x = QLineEdit()
        self.input_x.setPlaceholderText("Enter X coordinate")
        self.input_y = QLineEdit()
        self.input_y.setPlaceholderText("Enter Y coordinate")
        
        self.input_epsg = QComboBox()
        self.input_epsg.setEditable(True)
        self.input_epsg.addItem("Native (Current)", "native")
        self.input_epsg.addItem("EPSG:4326 (WGS84)", "EPSG:4326")
        self.input_epsg.addItem("EPSG:32644 (UTM Zone 44N)", "EPSG:32644")
        self.input_epsg.addItem("EPSG:3857 (Web Mercator)", "EPSG:3857")
        
        self.output_crs_label = QLabel("Output CRS: Not loaded")
        
        self.converted_coords_label = QLabel("")
        self.converted_coords_label.setStyleSheet("color: blue; font-weight: bold;")
        
        self.btn_convert_coords = QPushButton("Convert WGS84 to UTM")
        self.btn_convert_coords.clicked.connect(self.convert_wgs84_to_utm)
        self.btn_convert_coords.setStyleSheet("background-color: #4CAF50; color: white;")
        
        self.btn_manual_plot = QPushButton("Plot from Coordinates")
        self.btn_manual_plot.clicked.connect(self.manual_plot_spectrum)
        
        coord_layout.addRow("X Coordinate:", self.input_x)
        coord_layout.addRow("Y Coordinate:", self.input_y)
        coord_layout.addRow("Input CRS:", self.input_epsg)
        coord_layout.addRow(self.output_crs_label)
        coord_layout.addRow(self.converted_coords_label)
        coord_layout.addRow(self.btn_convert_coords)
        coord_layout.addRow(self.btn_manual_plot)
        
        self.coord_group.setLayout(coord_layout)
        layout.addWidget(self.coord_group)
        
        # Canvas
        self.canvas = FigureCanvas(Figure())
        self.ax = self.canvas.figure.subplots()
        layout.addWidget(self.canvas)

    def convert_wgs84_to_utm(self):
        """Convert WGS84 coordinates to UTM and auto-fill the fields"""
        try:
            x_text = self.input_x.text().strip()
            y_text = self.input_y.text().strip()
            
            if not x_text or not y_text:
                QMessageBox.warning(self, "Warning", "Please enter both X and Y coordinates first")
                return
            
            lon = float(x_text)
            lat = float(y_text)
            
            # Validate WGS84 range
            if lon < -180 or lon > 180 or lat < -90 or lat > 90:
                QMessageBox.warning(self, "Warning", "Coordinates appear to be UTM (meters) not WGS84 (degrees)\n\nWGS84 range:\n  Longitude: -180 to 180\n  Latitude: -90 to 90")
                return
            
            # Calculate UTM zone
            utm_epsg, zone_number, zone_letter = wgs84_to_utm(lon, lat)
            
            # Transform WGS84 to UTM
            x_utm, y_utm = transform("EPSG:4326", f"EPSG:{utm_epsg}", [lon], [lat])
            x_utm, y_utm = x_utm[0], y_utm[0]
            
            # Update the input fields with UTM values
            self.input_x.setText(f"{x_utm:.2f}")
            self.input_y.setText(f"{y_utm:.2f}")
            
            # Select the corresponding UTM EPSG
            for i in range(self.input_epsg.count()):
                if str(utm_epsg) in self.input_epsg.itemText(i):
                    self.input_epsg.setCurrentIndex(i)
                    break
            else:
                # If UTM zone not in list, add it dynamically
                self.input_epsg.addItem(f"EPSG:{utm_epsg} (Auto-detected UTM Zone {zone_number}{zone_letter})", f"EPSG:{utm_epsg}")
                self.input_epsg.setCurrentIndex(self.input_epsg.count() - 1)
            
            # Update conversion label
            self.converted_coords_label.setText(f"Converted to UTM Zone {zone_number}{zone_letter}\nX: {x_utm:.2f}  Y: {y_utm:.2f}")
            
            QMessageBox.information(self, "Conversion Complete", 
                f"WGS84 ({lon:.5f}, {lat:.5f})\n\nConverted to:\nEPSG:{utm_epsg} - UTM Zone {zone_number}{zone_letter}\n\nX (Easting):  {x_utm:.2f}\nY (Northing): {y_utm:.2f}")
            
        except ValueError as e:
            QMessageBox.critical(self, "Error", f"Invalid coordinate value:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to convert coordinates:\n{e}")

    def manual_plot_spectrum(self):
        if not self.filepathforgraph:
            parent = self.parent()
            if parent and hasattr(parent, 'filepath'):
                self.filepathforgraph = parent.filepath
            else:
                QMessageBox.warning(self, "Warning", "No file loaded")
                return
        
        try:
            x_text = self.input_x.text().strip()
            y_text = self.input_y.text().strip()
            
            if not x_text or not y_text:
                QMessageBox.warning(self, "Warning", "Please enter both X and Y coordinates")
                return
            
            x_coord = float(x_text)
            y_coord = float(y_text)
            
            input_crs_data = self.input_epsg.currentData()
            if input_crs_data == "native":
                input_crs = None
            else:
                input_crs = input_crs_data
            
            with rasterio.open(self.filepathforgraph) as src:
                native_crs = src.crs.to_string()
                
                # Update output CRS label with current EPSG format
                epsg_code = src.crs.to_epsg()
                if epsg_code:
                    self.output_crs_label.setText(f"Output CRS: EPSG:{epsg_code}")
                else:
                    self.output_crs_label.setText(f"Output CRS: {native_crs}")
                
                # Transform coordinates if needed (input EPSG -> native EPSG)
                if input_crs and input_crs != native_crs:
                    x_native, y_native = transform(input_crs, native_crs, [x_coord], [y_coord])
                    x_native, y_native = x_native[0], y_native[0]
                else:
                    x_native, y_native = x_coord, y_coord
                
                # Convert native coordinates to pixel coordinates
                row, col = src.index(x_native, y_native)
                
                # Check bounds
                if row < 0 or row >= src.height or col < 0 or col >= src.width:
                    QMessageBox.warning(self, "Warning", 
                        f"Coordinates are outside the raster bounds\n\n"
                        f"Input: {x_coord}, {y_coord} ({input_crs})\n"
                        f"Converted: {x_native:.2f}, {y_native:.2f} ({native_crs})\n"
                        f"Pixel: col={col}, row={row}\n"
                        f"Image size: {src.width} x {src.height}")
                    return
                
                # Read spectrum at pixel coordinates
                spectrum = src.read()[:, row, col]
                
                # Get WGS84 coordinates for display using parent's method
                parent = self.parent()
                if parent and hasattr(parent, 'convert_to_wgs84'):
                    lat, lon = parent.convert_to_wgs84(src, col, row)
                else:
                    lat, lon = 0.0, 0.0
                
                # Update plot
                self.update_plot(spectrum, col, row, f"Lat: {lat:.5f}", f"Lon: {lon:.5f}", self.filepathforgraph)
                
                # Add native CRS coordinates to title to show output in current EPSG format
                native_coord_text = f"Native ({native_crs}): {x_native:.2f}, {y_native:.2f}"
                self.ax.set_title(f"({col},{row})\n{native_coord_text}\nLat: {lat:.5f} | Lon: {lon:.5f}")
                self.canvas.draw()
                
        except ValueError as e:
            QMessageBox.critical(self, "Error", f"Invalid coordinate value:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to plot from coordinates:\n{e}")

    def update_plot(self, spectrum, x, y, lat, lon, filepathforgraph):
        self.filepathforgraph = filepathforgraph
        self.ax.clear()
        self.ax.plot(spectrum)
        self.setWindowTitle(f"{self.filepathforgraph} | Spectral Signature")

        # ✅ UPDATED formatting
        coord_text = f"{lat} | {lon}"
        self.ax.set_title(f"({x},{y})\n{coord_text}")

        self.ax.set_xlabel("Band")
        self.ax.set_ylabel("Intensity")
        self.ax.grid(True)
        self.canvas.draw()
        
        # Update output CRS label when file is loaded
        try:
            with rasterio.open(filepathforgraph) as src:
                epsg_code = src.crs.to_epsg()
                if epsg_code:
                    self.output_crs_label.setText(f"Output CRS: EPSG:{epsg_code}")
                else:
                    self.output_crs_label.setText(f"Output CRS: {src.crs.to_string()}")
        except:
            pass

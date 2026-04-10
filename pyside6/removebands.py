# remove_bands.py

import rasterio
from PySide6.QtWidgets import QInputDialog, QMessageBox

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
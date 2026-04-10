import rasterio
from PySide6.QtWidgets import QInputDialog, QMessageBox
from basic_tools import rotate_flip_data


def rotate_flip_action_ui(parent, filepath):
    try:
        # Ask rotation angle
        angle, ok = QInputDialog.getInt(
            parent, "Rotate", "Enter rotation angle (0, 90, 180, 270):", 0, 0, 360, 1
        )
        if not ok:
            return

        # Ask flip options
        flip_h, ok1 = QInputDialog.getItem(
            parent, "Flip Horizontal", "Flip Horizontally?", ["No", "Yes"], 0, False
        )
        if not ok1:
            return

        flip_v, ok2 = QInputDialog.getItem(
            parent, "Flip Vertical", "Flip Vertically?", ["No", "Yes"], 0, False
        )
        if not ok2:
            return

        flip_horizontal = (flip_h == "Yes")
        flip_vertical = (flip_v == "Yes")

        # Call processing function
        transformed = rotate_flip_data(
            filepath,
            angle=angle,
            flip_horizontal=flip_horizontal,
            flip_vertical=flip_vertical
        )

        # Save output
        output_path = filepath.replace(".tif", "_rotated.tif")

        with rasterio.open(filepath) as src:
            profile = src.profile

            profile.update({
                "height": transformed.shape[1],
                "width": transformed.shape[2]
            })

            with rasterio.open(output_path, "w", **profile) as dst:
                dst.write(transformed)

        QMessageBox.information(
            parent,
            "Success",
            f"Transformed file saved as:\n{output_path}"
        )

    except Exception as e:
        QMessageBox.critical(parent, "Error", f"Rotation/Flip failed:\n{e}")

def resize_data_action_ui(parent, filepath):
    try:
        # Ask for scale factors
        scale_x, ok1 = QInputDialog.getDouble(
            parent, "Resize Data", "Enter X scale (e.g. 0.5 or 2.0):", 1.0, 0.1, 10.0, 2
        )
        if not ok1:
            return

        scale_y, ok2 = QInputDialog.getDouble(
            parent, "Resize Data", "Enter Y scale (e.g. 0.5 or 2.0):", 1.0, 0.1, 10.0, 2
        )
        if not ok2:
            return

        # Call external function
        resized_data = resize_data(filepath, scale_x, scale_y)

        # Save new file
        output_path = filepath.replace(".tif", "_resized.tif")

        with rasterio.open(filepath) as src:
            profile = src.profile

            profile.update({
                "height": resized_data.shape[1],
                "width": resized_data.shape[2]
            })

            with rasterio.open(output_path, "w", **profile) as dst:
                dst.write(resized_data)

        QMessageBox.information(
            parent,
            "Success",
            f"Resized file saved as:\n{output_path}"
        )

    except Exception as e:
        QMessageBox.critical(parent, "Error", f"Resize failed:\n{e}")










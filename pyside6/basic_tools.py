import numpy as np
import rasterio
from scipy.ndimage import zoom, rotate


# -------------------------------
# 1. RESIZE DATA
# -------------------------------
def resize_data(filepath, scale_x=1.0, scale_y=1.0):
    with rasterio.open(filepath) as src:
        data = src.read()

        resized = np.array([
            zoom(band, (scale_y, scale_x))
            for band in data
        ])

        return resized


# -------------------------------
# 2. ROTATE / FLIP DATA
# -------------------------------

def rotate_flip_data(filepath, angle=0, flip_horizontal=False, flip_vertical=False):
    with rasterio.open(filepath) as src:
        data = src.read()

        transformed = []

        # 🔥 Rotate first band to get correct target shape
        sample = rotate(
            data[0],
            angle,
            reshape=True,
            mode='constant', cval=0
        )

        target_h, target_w = sample.shape

        for band in data:
            img = band

            if angle != 0:
                img = rotate(
                    img,
                    angle,
                    reshape=True,
                    mode='constant', cval=0
                )

            # 🔥 Ensure SAME SHAPE (no silent cropping)
            padded = np.zeros((target_h, target_w), dtype=img.dtype)
            h, w = img.shape
            padded[:h, :w] = img

            img = padded

            # flips
            if flip_horizontal:
                img = np.fliplr(img)

            if flip_vertical:
                img = np.flipud(img)

            transformed.append(img)

        return np.stack(transformed)

# -------------------------------
# 3. STRETCH DATA (Contrast)
# -------------------------------
def stretch_data(filepath, method="linear"):
    with rasterio.open(filepath) as src:
        data = src.read().astype(np.float32)

        if method == "linear":
            min_val = np.percentile(data, 2)
            max_val = np.percentile(data, 98)
            stretched = (data - min_val) / (max_val - min_val)

        elif method == "minmax":
            stretched = (data - data.min()) / (data.max() - data.min())

        else:
            raise ValueError("Unknown stretch method")

        return np.clip(stretched, 0, 1)


# -------------------------------
# 4. GLOBAL STATISTICS
# -------------------------------
def statistics(filepath):
    with rasterio.open(filepath) as src:
        data = src.read()

        stats = []

        for i, band in enumerate(data):
            stats.append({
                "band": i + 1,
                "min": float(np.min(band)),
                "max": float(np.max(band)),
                "mean": float(np.mean(band)),
                "std": float(np.std(band))
            })

        return stats


# -------------------------------
# 5. SPATIAL STATISTICS (Local)
# -------------------------------
def spatial_statistics(filepath, window_size=3):
    from scipy.ndimage import uniform_filter

    with rasterio.open(filepath) as src:
        data = src.read()

        local_mean = np.array([
            uniform_filter(band, size=window_size)
            for band in data
        ])

        local_variance = np.array([
            uniform_filter(band**2, size=window_size) - (uniform_filter(band, size=window_size))**2
            for band in data
        ])

        return local_mean, local_variance


# -------------------------------
# 6. BAND MATH
# -------------------------------
def band_math(filepath, expression):
    """
    Example expression:
    "(b10 - b5) / (b10 + b5)"
    """
    with rasterio.open(filepath) as src:
        data = src.read()

        context = {}
        for i in range(data.shape[0]):
            context[f"b{i+1}"] = data[i]

        result = eval(expression, {}, context)
        return result


# -------------------------------
# 7. SPECTRAL MATH
# -------------------------------
def spectral_math(filepath, operation="normalize"):
    with rasterio.open(filepath) as src:
        data = src.read().astype(np.float32)

        if operation == "normalize":
            norm = np.linalg.norm(data, axis=0)
            result = data / (norm + 1e-8)

        elif operation == "mean_center":
            mean = np.mean(data, axis=0)
            result = data - mean

        else:
            raise ValueError("Unknown spectral operation")

        return result
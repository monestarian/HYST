import numpy as np
from skimage.feature import graycomatrix, graycoprops
from scipy.ndimage import uniform_filter


def occurrence_measures(image):
    mean = np.mean(image)
    variance = np.var(image)
    std = np.std(image)

    hist, _ = np.histogram(image.flatten(), bins=256, range=(0,255), density=True)
    hist = hist + 1e-10

    entropy = -np.sum(hist * np.log2(hist))
    energy = np.sum(hist ** 2)

    return {
        "Mean": mean,
        "Variance": variance,
        "Std": std,
        "Entropy": entropy,
        "Energy": energy
    }


def cooccurrence_measures(image):

    glcm = graycomatrix(
        image,
        distances=[1],
        angles=[0],
        levels=256,
        symmetric=True,
        normed=True
    )

    contrast = graycoprops(glcm, 'contrast')[0,0]
    correlation = graycoprops(glcm, 'correlation')[0,0]
    energy = graycoprops(glcm, 'energy')[0,0]
    homogeneity = graycoprops(glcm, 'homogeneity')[0,0]

    return {
        "Contrast": contrast,
        "Correlation": correlation,
        "Energy": energy,
        "Homogeneity": homogeneity
    }


def lee_filter(img, size=5):
    mean = uniform_filter(img, size)
    mean_sq = uniform_filter(img**2, size)
    variance = mean_sq - mean**2
    overall_var = np.var(img)

    weight = variance / (variance + overall_var)
    return mean + weight * (img - mean)


# Enhanced Lee Filter
def enhanced_lee_filter(img, size=5):
    mean = uniform_filter(img, size)
    variance = uniform_filter(img**2, size) - mean**2
    noise_var = np.mean(variance)

    k = variance / (variance + noise_var)
    return mean + k * (img - mean)


# Frost Filter
def frost_filter(img, size=5, damping=2.0):
    mean = uniform_filter(img, size)
    variance = uniform_filter(img**2, size) - mean**2

    weight = np.exp(-damping * variance)
    return mean * weight + img * (1 - weight)


# Enhanced Frost Filter
def enhanced_frost_filter(img, size=5, damping=2.0):
    mean = uniform_filter(img, size)
    variance = uniform_filter(img**2, size) - mean**2

    weight = np.exp(-damping * variance / (mean + 1e-6))
    return mean * weight + img * (1 - weight)

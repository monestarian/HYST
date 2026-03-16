# EnMAP Custom Composite Viewer: Project Summary & Key Takeaways

## 1. Core Tech Stack
* **Framework:** Streamlit (for UI and state management).
* **Geospatial Processing:** `rasterio` (for reading .tif files, bounding boxes, coordinate transformations, and pixel sampling).
* **Mapping:** `leafmap.foliumap` (for building the base map and rendering raster layers).
* **Interactivity:** `streamlit_folium.st_folium` (CRITICAL: used instead of leafmap's native `.to_streamlit()` to capture map clicks without resetting the app state).
* **Data Visualization:** `pandas` and `st.line_chart` (for plotting 202-band spectral signatures).

## 2. Data Handling & Band Structure
The application handles 204-band GeoTIFFs (30m spatial resolution) with mixed data types:
* **Bands 1–202 (Hyperspectral):** Visualized as 3-band RGB composites using reflectance min/max stretch values (e.g., 110–2000). Sampled collectively to generate spectral signature graphs.
* **Band 203 (Aboveground Biomass Density - AGBD):** Continuous variable (Mg/ha). Requires sequential colormaps (e.g., `viridis`, `Greens`) and specific continuous min/max stretching.
* **Band 204 (Plant Functional Type - PFT):** Categorical variable based on the MODIS Type 5 scheme (0-11 classes). Requires categorical colormaps (e.g., `tab20`) to distinctly separate land cover types.

## 3. Key Geospatial Logic
* **Dynamic Centering:** The app calculates a master bounding box by iterating through all loaded `.tif` files, finding the absolute min/max extents, and computing the exact center in EPSG:4326 (Lat/Lon) to set the initial map view.
* **Coordinate Transformation for Sampling:** Map clicks return EPSG:4326 Lat/Lon coordinates. Before extracting a spectral signature, these must be transformed (`rasterio.warp.transform`) into the local CRS of the specific `.tif` file.
* **Tuple Unpacking Safety:** `rasterio.warp.transform` can return either 2D (X, Y) or 3D (X, Y, Z) coordinates. Always use the splat operator (`xs, ys, *_ = transform(...)`) or index assignment to prevent strict type-checking errors (like Pylance tuple mismatch).

## 4. UI/UX Enhancements
* **CSS Injection for Map Cursors:** Leaflet's default "grab hand" cursor is unintuitive for pixel selection. Injecting custom CSS via `m.get_root().html.add_child()` overrides this, setting the `.leaflet-container` to `cursor: crosshair !important;` for precise clicking.
* **Graceful Fails:** The app dynamically checks if coordinate clicks fall out-of-bounds of the loaded rasters and provides a clean Streamlit error message rather than crashing the Python backend.


# EnMAP Interactive Composite Viewer & Spectral Analyzer

A Python-based interactive web application built with Streamlit and Leafmap. This tool allows researchers and data scientists to visualize high-dimensional hyperspectral data (specifically the EnMAP `hybiomass` dataset) and extract point-based spectral signatures on the fly.

## 🚀 Features

* **Multi-File Ingestion:** Load multiple GeoTIFF (`.tif`) patches simultaneously. The map automatically calculates the bounding box to center all loaded datasets.
* **Dynamic Visualization Modes:**
    * **RGB Composite:** Render True Color or False Color composites by dynamically assigning Red, Green, and Blue bands.
    * **Aboveground Biomass (AGBD):** Visualize the GEDI-derived biomass density layer (Band 203) using customizable heatmaps (e.g., Viridis).
    * **Plant Functional Type (PFT):** Display categorical plant classification data (Band 204).
* **Real-time Contrast Stretching:** Adjust `Vmin` and `Vmax` on the fly to enhance dark or washed-out images without preprocessing the raw data.
* **Point-and-Click Spectral Analysis:** * Click anywhere on the raster to extract the full 202-band spectral signature of that exact pixel.
    * Instantly plots the reflectance curve (Z-profile) using Streamlit's native charting.
    * Supports manual Latitude/Longitude coordinate entry for precise querying.

## 🛠️ Prerequisites & Installation

Ensure you have Python 3.9+ installed. You will need the following libraries to run this application:

```bash
pip install streamlit rasterio leafmap folium streamlit-folium pandas
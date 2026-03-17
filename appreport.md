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




# update and correction for coordinates in app4
# Streamlit & Rasterio Fixes: Pixel Extraction and State Syncing

This document outlines the recent modifications made to the EnMAP Interactive Composite Viewer to enable exact pixel coordinate extraction and to synchronize map clicks with manual input fields.

---

## 1. Extracting Pixel Coordinates (Row & Column)

### What was fixed
Initially, the application successfully transformed the clicked Latitude and Longitude into the local coordinate reference system (CRS) of the raster to sample the spectral values, but it did not tell the user *where* in the actual image array (the pixel row and column) that click occurred.

### How it was fixed
We used **Rasterio's built-in `src.index()` method**. 
Once the geographic coordinates (Lat/Lon) are converted into the raster's native spatial coordinates (`x`, `y`), `src.index(x, y)` calculates exactly which row and column in the underlying numpy array correspond to that spatial point.

**Code Change:**
```python
# Inside get_spectral_signature()

# 1. Transform Lat/Lon to raster's spatial x, y
xs, ys, *_ = transform('EPSG:4326', src.crs, [lon], [lat])
x, y = xs[0], ys[0]

# 2. Get the internal pixel coordinates (row, col)
row, col = src.index(x, y) 

# 3. Return these alongside the spectral signature
return values, os.path.basename(filepath), row, col

# 1. Initialize session state
if "lat_val" not in st.session_state:
    st.session_state.lat_val = 0.0
if "lon_val" not in st.session_state:
    st.session_state.lon_val = 0.0
if "last_click" not in st.session_state:
    st.session_state.last_click = None

# 2. Update state if a new map click is detected
if isinstance(map_data, dict) and map_data.get("last_clicked"):
    current_click = map_data["last_clicked"]
    if current_click != st.session_state.last_click:
        st.session_state.lat_val = current_click["lat"]
        st.session_state.lon_val = current_click["lng"]
        st.session_state.last_click = current_click

# 3. Bind the number_inputs to the session state keys
with input_col1: 
    target_lat = st.number_input("Latitude", format="%.6f", key="lat_val")
with input_col2: 
    target_lon = st.number_input("Longitude", format="%.6f", key="lon_val")




# adding file path system app5

Since EnMAP hyperspectral `.tif` files are often much larger than Streamlit's default 200MB limit, you need to manually increase the `maxUploadSize`. Streamlit does not create a configuration file by default, so you must implement one of the two corrections below.

## Method 1: Create a `config.toml` File (Recommended)
This method makes the size limit increase permanent for your project, so you don't have to remember to add it to your run command every time.

**How to apply:**
1. Navigate to your project's root directory (the folder where your main Streamlit Python script is located).
2. Create a new folder named `.streamlit` (you must include the dot at the beginning).
3. Inside the `.streamlit` folder, create a new text file and name it `config.toml`.
4. Open `config.toml` in your code editor and paste the following configuration:

toml
[server]
maxUploadSize = 2000


# Streamlit Multi-Raster Viewer: Update Summary

This document outlines the modifications made to the EnMAP Interactive Composite Viewer to support simultaneous, independent viewing of up to 4 images.

## 1. Dynamic Grid System
**What was fixed:** The original application used a static, hardcoded two-column layout (Map on the left, Analysis on the right) that only supported viewing one consolidated interface at a time.
**How it was implemented:** * Added an `st.radio` widget allowing the user to select between 1, 2, 3, or 4 simultaneous views.
* Replaced the static layout with dynamic column generation. Based on the selected number, the app creates a grid using `st.columns()`. For 4 views, it concatenates two sets of 2 columns (`st.columns(2) + st.columns(2)`) to create a 2x2 grid. 
* The UI generation was wrapped in a `for i in range(num_views):` loop to render the interface for each view dynamically.

## 2. Independent Widget State Management
**What was fixed:** In Streamlit, rendering the same widget multiple times causes a `DuplicateWidgetID` error, and their states overwrite each other. The settings for one image would inadvertently apply to all images.
**How it was implemented:** * Utilized Streamlit's `key` parameter. Every interactive widget inside the loop (e.g., `st.selectbox`, `st.number_input`, `st_folium`) was assigned a unique string identifier by appending the loop index `_{i}`. 
* Example: `key=f"vmin_rgb_{i}"`. This isolates the session state of every slider, dropdown, and map to its specific view.

## 3. Dedicated Maps and Spectral Graphs
**What was fixed:** The original code combined all uploaded `.tif` files into a single map and extracted the signature from the first valid bounding box it found.
**How it was implemented:** * Moved the `leafmap` instantiations, map rendering (`st_folium`), and the spectral line chart creation *inside* the view loop.
* Each view now gets its own completely independent map instance, its own coordinate tracking (`map_data["last_clicked"]`), and its own `st.line_chart` that updates without affecting the other views.

## 4. Targeted Spectral Extraction
**What was fixed:** The `get_spectral_signature` function previously iterated through all uploaded files to find a match for the clicked coordinates, which caused conflicts when multiple images covered the same geographic area.
**How it was implemented:** * Refactored the function into `get_single_spectral_signature(filepath, lat, lon)`.
* Instead of passing a list of all files, the app now passes only the specific `filepath` of the image selected in that distinct view. This ensures the spectral graph accurately reflects the exact raster the user clicked on, preventing data crossover.

## 5. File Mapping
**What was fixed:** The UI needed a way to let users pick which specific uploaded file to display in which view. The original code only stored a flat list of paths.
**How it was implemented:** * Changed the `file_paths` list to a `file_dict` dictionary, mapping the original file name (`uploaded_file.name`) to its temporary system path.
* Added an `st.selectbox` in each view loop populated with `file_dict.keys()`, allowing the user to select an image by name, while the backend easily retrieves the correct local path for rendering and extraction.
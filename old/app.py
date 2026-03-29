import streamlit as st
import rasterio
from rasterio.warp import transform, transform_bounds
import leafmap.foliumap as leafmap
import pandas as pd
import os
import folium
from streamlit_folium import st_folium
import numpy as np

# 1. Page Configuration
st.set_page_config(page_title="EnMAP Multi-Pane Comparative Analysis", layout="wide")
st.title("EnMAP Multi-Pane Comparative Analysis")

# Initialize Session State per pane (Max 4 panes based on your radio button)
for i in range(4):
    if f"lat_{i}" not in st.session_state:
        st.session_state[f"lat_{i}"] = None
    if f"lon_{i}" not in st.session_state:
        st.session_state[f"lon_{i}"] = None

# 2. Sidebar
with st.sidebar:
    st.header("1. Data & Layout")
    uploaded_files = st.file_uploader("Upload .tif files", type=['tif', 'tiff'], accept_multiple_files=True)
    num_panes = st.radio("Comparison Mode:", [1, 2, 3, 4], index=0, horizontal=True)

st.divider()

# 3. Core Processing Functions
def get_map_center(filepath):
    """Calculates the center of the given raster to correctly focus the map."""
    try:
        with rasterio.open(filepath) as src:
            left, bottom, right, top = transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
        return (bottom + top) / 2.0, (left + right) / 2.0
    except Exception:
        return 0.0, 0.0

def get_pixel_data(path, lat, lon):
    """
    Transforms WGS84 Lat/Lon to Raster CRS and extracts pixel values.
    Returns (values_array, pixel_coords)
    """
    try:
        with rasterio.open(path) as src:
            # Transform Lat/Lon (EPSG:4326) to the raster's native CRS
            xs, ys = transform('EPSG:4326', src.crs, [lon], [lat])
            
            # Convert the transformed coordinates to Row/Column indices
            row, col = src.index(xs[0], ys[0])
            
            # Bounds check
            if 0 <= row < src.height and 0 <= col < src.width:
                # Read all bands for that single pixel
                window = rasterio.windows.Window(col, row, 1, 1)
                data = src.read(window=window).flatten()
                return data, (row, col)
    except Exception as e:
        return None, None
    return None, None

# 4. Processing Uploaded Files
if not uploaded_files:
    st.info("Please upload .tif files in the sidebar to begin.")
else:
    temp_dir = "temp_rasters"
    if not os.path.exists(temp_dir): 
        os.makedirs(temp_dir)
    
    file_paths = []
    for uploaded_file in uploaded_files:
        p = os.path.join(temp_dir, uploaded_file.name)
        # Ensure file is fully written to disk before processing
        if not os.path.exists(p):
            with open(p, "wb") as f:
                f.write(uploaded_file.getbuffer())
                f.flush()
                os.fsync(f.fileno())
        file_paths.append(p)

    # 5. Dynamic Grid Layout
    cols = st.columns(num_panes) if num_panes > 1 else [st.container()]

    # 6. Render Panes
    for i in range(num_panes):
        with cols[i % len(cols)]:
            st.subheader(f"Pane {i+1}")
            
            # Auto-select a different file for each pane by default
            default_idx = i if i < len(file_paths) else 0
            file_to_show = st.selectbox(f"Select File:", file_paths, index=default_idx, format_func=os.path.basename, key=f"fsel_{i}")
            
            # Visualization Settings
            with st.expander("Visualization Settings"):
                v_mode = st.selectbox("Type", ["RGB", "B&W", "AGBD", "PFT"], key=f"v_{i}")
                if v_mode == "RGB":
                    p_params = {"bands": [45, 29, 15], "vmin": 110, "vmax": 2000}
                elif v_mode == "B&W":
                    bw_band = st.number_input("Select Band", 1, 202, 45, key=f"bw_{i}")
                    c1, c2 = st.columns(2)
                    v_min = c1.number_input("Min", value=100, key=f"vmin_{i}")
                    v_max = c2.number_input("Max", value=3500, key=f"vmax_{i}")
                    p_params = {"bands": [bw_band], "cmap": "gray", "vmin": v_min, "vmax": v_max}
                elif v_mode == "AGBD":
                    p_params = {"bands": [203], "cmap": "viridis", "vmin": 0, "vmax": 300}
                else: # PFT
                    p_params = {"bands": [204], "cmap": "tab20", "vmin": 0, "vmax": 15}

            # Per-Pane Manual Coordinates
            with st.expander("Manual Coordinate Input"):
                mc1, mc2 = st.columns(2)
                m_lat = mc1.number_input("Latitude", format="%.6f", value=st.session_state[f"lat_{i}"] or 0.0, key=f"mlat_{i}")
                m_lon = mc2.number_input("Longitude", format="%.6f", value=st.session_state[f"lon_{i}"] or 0.0, key=f"mlon_{i}")
                if st.button("Extract Coordinates", key=f"btn_{i}", use_container_width=True):
                    st.session_state[f"lat_{i}"] = m_lat
                    st.session_state[f"lon_{i}"] = m_lon
                    st.rerun()

            # Map Creation
            c_lat, c_lon = get_map_center(file_to_show)
            m = leafmap.Map(center=[c_lat, c_lon], zoom=11, draw_control=False)
            
            # Comprehensive CSS to force Crosshair cursor
            cursor_css = """
            <style>
            .leaflet-container { cursor: crosshair !important; }
            .leaflet-interactive { cursor: crosshair !important; }
            .leaflet-grab { cursor: crosshair !important; }
            .leaflet-dragging .leaflet-grab { cursor: crosshair !important; }
            </style>
            """
            # Inject into header for better application inside the Folium iframe
            m.get_root().header.add_child(folium.Element(cursor_css))
            
            try:
                m.add_raster(file_to_show, **p_params)
            except Exception as e:
                st.error(f"Rendering error: {e}")
            
            # Display Map
            map_output = st_folium(m, key=f"map_{i}", height=300, use_container_width=True)

            # Capture Clicks specific to this pane
            if map_output and map_output.get("last_clicked"):
                clicked = map_output["last_clicked"]
                if (clicked["lat"] != st.session_state[f"lat_{i}"]):
                    st.session_state[f"lat_{i}"] = clicked["lat"]
                    st.session_state[f"lon_{i}"] = clicked["lng"]
                    st.rerun()

            # 7. Extract and Display Data for THIS pane
            current_lat = st.session_state[f"lat_{i}"]
            current_lon = st.session_state[f"lon_{i}"]

            if current_lat is not None and current_lon is not None:
                pixel_values, coords = get_pixel_data(file_to_show, current_lat, current_lon)
                
                if pixel_values is not None:
                    st.success(f"**Target:** Lat: {current_lat:.5f} | Lon: {current_lon:.5f}")
                    st.caption(f"**Pixel Found!** Row: {coords[0]}, Col: {coords[1]}")
                    
                    # Create Reflectance Chart (Bands 1-202)
                    spectral_data = pixel_values[:202]
                    chart_df = pd.DataFrame({
                        "Band Index (1-202)": range(1, len(spectral_data) + 1),
                        "Reflectance": spectral_data
                    }).set_index("Band Index (1-202)").fillna(0)
                    
                    st.line_chart(chart_df, height=180)
                    
                    # Extra Product metrics
                    m1, m2 = st.columns(2)
                    if len(pixel_values) >= 203:
                        agbd_val = pixel_values[202]
                        if not np.isnan(agbd_val):
                            m1.metric("AGBD", f"{agbd_val:.2f}")
                        else:
                            m1.caption("AGBD: NaN")
                    
                    if len(pixel_values) >= 204:
                        pft_val = pixel_values[203]
                        if not np.isnan(pft_val):
                            m2.metric("PFT Class", int(pft_val))
                        else:
                            m2.caption("PFT: NaN")
                else:
                    st.warning("Coordinate is outside image bounds.")
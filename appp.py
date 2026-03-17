import streamlit as st
import rasterio
from rasterio.warp import transform
import leafmap.foliumap as leafmap
import pandas as pd
import os
import folium
from streamlit_folium import st_folium
import numpy as np

# 1. Page Configuration
st.set_page_config(page_title="EnMAP Multi-Pane Comparative Analysis", layout="wide")
st.title("EnMAP Multi-Pane Comparative Analysis")

# Initialize Session State
if "clicked_lat" not in st.session_state:
    st.session_state.clicked_lat = None
if "clicked_lon" not in st.session_state:
    st.session_state.clicked_lon = None

# 2. Sidebar
with st.sidebar:
    st.header("1. Data & Layout")
    uploaded_files = st.file_uploader("Upload .tif files", type=['tif', 'tiff'], accept_multiple_files=True)
    num_panes = st.radio("Comparison Mode:", [1, 2, 3, 4], index=0, horizontal=True)
    
    st.divider()
    st.header("2. Manual Coordinates")
    m_lat = st.number_input("Latitude", format="%.6f", value=st.session_state.clicked_lat if st.session_state.clicked_lat else 0.0)
    m_lon = st.number_input("Longitude", format="%.6f", value=st.session_state.clicked_lon if st.session_state.clicked_lon else 0.0)
    if st.button("Extract from Manual Coordinates", use_container_width=True):
        st.session_state.clicked_lat = m_lat
        st.session_state.clicked_lon = m_lon

st.divider()

# 3. Core Processing Function
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
        # Fix: Ensure file is fully written to disk before processing
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
            file_to_show = st.selectbox(f"Select File:", file_paths, format_func=os.path.basename, key=f"fsel_{i}")
            
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
                    # Fix: Single band for colormap to avoid rio_tiler errors
                    p_params = {"bands": [bw_band], "cmap": "gray", "vmin": v_min, "vmax": v_max}
                elif v_mode == "AGBD":
                    p_params = {"bands": [203], "cmap": "viridis", "vmin": 0, "vmax": 300}
                else: # PFT
                    p_params = {"bands": [204], "cmap": "tab20", "vmin": 0, "vmax": 15}

            # Map Creation
            m = leafmap.Map(draw_control=False)
            try:
                m.add_raster(file_to_show, **p_params)
            except Exception as e:
                st.error(f"Rendering error: {e}")
            
            # Display Map
            map_output = st_folium(m, key=f"map_{i}", height=300, use_container_width=True)

            # Capture Clicks
            if map_output and map_output.get("last_clicked"):
                clicked = map_output["last_clicked"]
                if (clicked["lat"] != st.session_state.clicked_lat):
                    st.session_state.clicked_lat = clicked["lat"]
                    st.session_state.clicked_lon = clicked["lng"]
                    st.rerun()

            # 7. Extract and Display Data
            if st.session_state.clicked_lat:
                pixel_values, coords = get_pixel_data(file_to_show, st.session_state.clicked_lat, st.session_state.clicked_lon)
                
                if pixel_values is not None:
                    st.caption(f"**Pixel Found!** Row: {coords[0]}, Col: {coords[1]}")
                    
                    # Create Reflectance Chart (Bands 1-202)
                    spectral_data = pixel_values[:202]
                    # Fill NaNs with 0 for the chart
                    chart_df = pd.DataFrame({
                        "Band": range(1, len(spectral_data) + 1),
                        "Value": spectral_data
                    }).set_index("Band").fillna(0)
                    
                    st.line_chart(chart_df, height=180)
                    
                    # Extra Product metrics
                    m1, m2 = st.columns(2)
                    # Check AGBD (Band 203)
                    if len(pixel_values) >= 203:
                        agbd_val = pixel_values[202]
                        if not np.isnan(agbd_val):
                            m1.metric("AGBD", f"{agbd_val:.2f}")
                        else:
                            m1.caption("AGBD: NaN")
                    
                    # Check PFT (Band 204) - Fix: NaN check before int conversion
                    if len(pixel_values) >= 204:
                        pft_val = pixel_values[203]
                        if not np.isnan(pft_val):
                            m2.metric("PFT Class", int(pft_val))
                        else:
                            m2.caption("PFT: NaN")
                else:
                    st.warning("Click is outside image bounds.")

# Global status
if st.session_state.clicked_lat:
    st.sidebar.success(f"Global Focus: {st.session_state.clicked_lat:.4f}, {st.session_state.clicked_lon:.4f}")
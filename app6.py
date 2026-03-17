#simultaneous viewing implemented

import streamlit as st
import rasterio
from rasterio.warp import transform_bounds, transform
import leafmap.foliumap as leafmap
import pandas as pd
import os
import tempfile
from streamlit_folium import st_folium
import folium

# 1. Configure the page
st.set_page_config(page_title="Multi-Raster Viewer", layout="wide")
st.title("EnMAP Interactive Composite Viewer")

# ==========================================
# 2. File Inputs (Top Section)
# ==========================================
st.write("Upload your .tif files below:")
uploaded_files = st.file_uploader(
    label="Select multiple .tif files",
    type=["tif", "tiff"],
    accept_multiple_files=True
)

file_dict = {}

if uploaded_files:
    # Create a persistent temporary directory for this session
    if "temp_dir" not in st.session_state:
        st.session_state.temp_dir = tempfile.mkdtemp()
    
    for uploaded_file in uploaded_files:
        temp_path = os.path.join(st.session_state.temp_dir, uploaded_file.name)
        
        # Only write the file to disk if it hasn't been saved yet (speeds up reruns)
        if not os.path.exists(temp_path):
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
        file_dict[uploaded_file.name] = temp_path

st.divider()

# ==========================================
# 3. Helper Functions
# ==========================================
@st.cache_data
def get_map_center(filepath):
    """Calculates the center of a single raster file."""
    with rasterio.open(filepath) as src:
        left, bottom, right, top = transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
    return (bottom + top) / 2, (left + right) / 2

def get_single_spectral_signature(filepath, lat, lon):
    """Extracts bands 1-202 for a specific raster file at given coordinates."""
    with rasterio.open(filepath) as src:
        try:
            xs, ys, *_ = transform('EPSG:4326', src.crs, [lon], [lat])
            x, y = xs[0], ys[0]
            
            if (src.bounds.left <= x <= src.bounds.right) and (src.bounds.bottom <= y <= src.bounds.top):
                row, col = src.index(x, y)
                gen = src.sample([(x, y)], indexes=list(range(1, 203)))
                values = list(gen)[0] 
                return values, row, col
        except Exception:
            pass
    return None, None, None

# ==========================================
# 4. Main Layout & Parallel Views
# ==========================================
if not file_dict:
    st.info("Please upload at least one .tif file above to begin.")
else:
    # Let user select how many parallel views they want
    num_views = st.radio("Number of simultaneous views:", [1, 2, 3, 4], horizontal=True)
    st.divider()
    
    # Determine column layout based on number of views
    cols = []
    if num_views == 1:
        cols = st.columns(1)
    elif num_views == 2:
        cols = st.columns(2)
    elif num_views == 3:
        cols = st.columns(3)
    elif num_views == 4:
        # Create a 2x2 grid by combining two sets of 2 columns
        cols = st.columns(2) + st.columns(2)
        
    file_names = list(file_dict.keys())

    # Iterate and build each view independently
    for i in range(num_views):
        with cols[i]:
            st.subheader(f"View {i+1}")
            
            # Select which file to show in this view
            selected_file = st.selectbox("Select Image", file_names, key=f"file_sel_{i}")
            filepath = file_dict[selected_file]
            
            # -- VISUALIZATION SETTINGS PER VIEW --
            with st.expander(f"Visualization Settings (View {i+1})", expanded=False):
                vis_mode = st.selectbox(
                    "Visualization Type",
                    [
                        "RGB Composite (Hyperspectral)", 
                        "Black & White (Single Band)",  
                        "Aboveground Biomass (AGBD)", 
                        "Plant Functional Type (PFT)"
                    ],
                    key=f"vis_mode_{i}"
                )

                plot_bands = []
                cmap = None
                vmin_val = 0.0
                vmax_val = 1.0

                if vis_mode == "RGB Composite (Hyperspectral)":
                    c1, c2, c3 = st.columns(3)
                    with c1: r_band = st.number_input('R:', value=45, step=1, key=f"r_{i}")
                    with c2: g_band = st.number_input('G:', value=29, step=1, key=f"g_{i}")
                    with c3: b_band = st.number_input('B:', value=15, step=1, key=f"b_{i}")
                    
                    c4, c5 = st.columns(2)
                    with c4: vmin_val = st.number_input('Vmin:', value=110.0, key=f"vmin_rgb_{i}")
                    with c5: vmax_val = st.number_input('Vmax:', value=2000.0, key=f"vmax_rgb_{i}")
                    plot_bands = [int(r_band), int(g_band), int(b_band)]

                elif vis_mode == "Black & White (Single Band)":
                    c1, c2 = st.columns(2)
                    with c1: bw_band = st.number_input('Band:', value=45, step=1, key=f"bw_{i}")
                    with c2: cmap = st.selectbox('Colormap:', ['gray', 'bone', 'gist_yarg'], key=f"cmap_bw_{i}")
                    c3, c4 = st.columns(2)
                    with c3: vmin_val = st.number_input('Vmin:', value=110.0, key=f"vmin_bw_{i}")
                    with c4: vmax_val = st.number_input('Vmax:', value=2000.0, key=f"vmax_bw_{i}")
                    plot_bands = [int(bw_band)]

                elif vis_mode == "Aboveground Biomass (AGBD)":
                    c1, c2, c3 = st.columns(3)
                    with c1: cmap = st.selectbox('Cmap:', ['viridis', 'Greens', 'YlGn'], key=f"cmap_agb_{i}")
                    with c2: vmin_val = st.number_input('Vmin:', value=0.0, key=f"vmin_agb_{i}") 
                    with c3: vmax_val = st.number_input('Vmax:', value=300.0, key=f"vmax_agb_{i}")
                    plot_bands = [203]

                elif vis_mode == "Plant Functional Type (PFT)":
                    c1, c2, c3 = st.columns(3)
                    with c1: cmap = st.selectbox('Cmap:', ['tab20', 'Set1', 'Paired'], key=f"cmap_pft_{i}")
                    with c2: vmin_val = st.number_input('Vmin:', value=0.0, key=f"vmin_pft_{i}")
                    with c3: vmax_val = st.number_input('Vmax:', value=15.0, key=f"vmax_pft_{i}")
                    plot_bands = [204]

            # -- MAP VIEW PER VIEW --
            lat_center, lon_center = get_map_center(filepath)
            m = leafmap.Map(center=[lat_center, lon_center], zoom=11)
            
            cursor_css = """
            <style>
            .leaflet-container { cursor: crosshair !important; }
            .leaflet-interactive { cursor: crosshair !important; }
            </style>
            """
            m.get_root().html.add_child(folium.Element(cursor_css)) # type: ignore
            
            m.add_raster(
                filepath, bands=plot_bands, cmap=cmap, 
                vmin=vmin_val, vmax=vmax_val, 
                layer_name=selected_file
            )
            
            # Ensure unique key for each map so they don't overwrite session states
            map_data = st_folium(m, height=400, use_container_width=True, key=f"map_{i}")

            # -- SPECTRAL ANALYSIS PER VIEW --
            if map_data and map_data.get("last_clicked"):
                click_lat = map_data["last_clicked"]["lat"]
                click_lon = map_data["last_clicked"]["lng"]
                
                with st.spinner("Extracting signature..."):
                    signature, row, col = get_single_spectral_signature(filepath, click_lat, click_lon)
                
                if signature is not None:
                    st.caption(f"**Target:** Lat: {click_lat:.5f} | Lon: {click_lon:.5f}")
                    st.caption(f"**Pixel:** Row `{row}`, Column `{col}`")
                    
                    chart_data = pd.DataFrame({
                        "Band Index (1-202)": range(1, 203),
                        "Reflectance": signature
                    }).set_index("Band Index (1-202)")
                    
                    st.line_chart(chart_data)
                else:
                    st.warning("Click is out of bounds for this specific image.")
            else:
                st.info("Click on the map above to view the spectral signature.")
            
            # Add some spacing if we are in the 4-view grid to separate top and bottom rows
            if num_views == 4 and i < 2:
                st.write("---")
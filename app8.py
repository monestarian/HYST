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
        
        # Only write the file to disk if it hasn't been saved yet
        if not os.path.exists(temp_path):
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
        file_dict[uploaded_file.name] = temp_path

st.divider()

# ==========================================
# 3. Helper Functions (Multi-File Support)
# ==========================================
def get_combined_map_center(filepaths):
    """Calculates the bounding box center for all provided rasters."""
    if not filepaths: 
        return 0.0, 0.0
    min_left, min_bottom, max_right, max_top = float('inf'), float('inf'), float('-inf'), float('-inf')
    for filepath in filepaths:
        with rasterio.open(filepath) as src:
            left, bottom, right, top = transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
            min_left, min_bottom = min(min_left, left), min(min_bottom, bottom)
            max_right, max_top = max(max_right, right), max(max_top, top)
    return (min_bottom + max_top) / 2, (min_left + max_right) / 2

def get_spectral_signature(filepaths, lat, lon):
    """Checks selected rasters for the given Lat/Lon and extracts bands 1-202."""
    for filepath in filepaths:
        with rasterio.open(filepath) as src:
            try:
                xs, ys, *_ = transform('EPSG:4326', src.crs, [lon], [lat])
                x, y = xs, ys
                
                # Check if coordinate is within the bounds of this specific file
                if (src.bounds.left <= x <= src.bounds.right) and (src.bounds.bottom <= y <= src.bounds.top):
                    row, col = src.index(x, y)
                    gen = src.sample([(x, y)], indexes=list(range(1, 203)))
                    values = list(gen) 
                    return values, os.path.basename(filepath), row, col
            except Exception:
                continue
    return None, None, None, None

# ==========================================
# 4. Main Layout & Parallel Views
# ==========================================
if not file_dict:
    st.info("Please upload at least one .tif file above to begin.")
else:
    # Let user select how many parallel views they want
    num_views = st.radio("Number of simultaneous views:",[1,2,3,4], horizontal=True)
    st.divider()
    
    # Determine column layout
    cols = []
    if num_views == 1: cols = st.columns(1)
    elif num_views == 2: cols = st.columns(2)
    elif num_views == 3: cols = st.columns(3)
    elif num_views == 4: cols = st.columns(2) + st.columns(2) # 2x2 grid
        
    file_names = list(file_dict.keys())

    # Iterate and build each view independently
    for i in range(num_views):
        with cols[i]:
            st.subheader(f"View {i+1}")
            
            sel_key = f"file_sel_{i}"
            
            # --- FIX: Clean up stale session state ---
            if sel_key in st.session_state:
                # Keep only the previously selected files that still exist in the new upload
                st.session_state[sel_key] = [f for f in st.session_state[sel_key] if f in file_names]
            # -----------------------------------------
            
            # Use multiselect so multiple images can be loaded in a SINGLE view
            selected_files = st.multiselect(
                "Select Images for this View", 
                options=file_names, 
                # If there's no state yet, default to the first file. 
                # If state exists, Streamlit uses it automatically and ignores default.
                default=[file_names] if file_names and sel_key not in st.session_state else None, 
                key=sel_key
            )
            
            view_filepaths = [file_dict[f] for f in selected_files]
            
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

            # -- MAP RENDERING PER VIEW --
            if view_filepaths:
                lat_center, lon_center = get_combined_map_center(view_filepaths)
                m = leafmap.Map(center=[lat_center, lon_center], zoom=11)
                m.add_basemap("Esri.WorldStreetMap") 
                
                cursor_css = """
                <style>
                .leaflet-container { cursor: crosshair !important; }
                .leaflet-interactive { cursor: crosshair !important; }
                </style>
                """
                m.get_root().html.add_child(folium.Element(cursor_css)) # type: ignore
                
                # Render all selected files on the map
                for fp in view_filepaths:
                    m.add_raster(
                        fp, bands=plot_bands, cmap=cmap, 
                        vmin=vmin_val, vmax=vmax_val, 
                        layer_name=os.path.basename(fp)
                    )
                
                map_data = st_folium(m, height=400, use_container_width=True, key=f"map_{i}")

                # -- STATE MANAGEMENT FOR COORDINATES --
                if f"lat_val_{i}" not in st.session_state:
                    st.session_state[f"lat_val_{i}"] = 0.0
                if f"lon_val_{i}" not in st.session_state:
                    st.session_state[f"lon_val_{i}"] = 0.0
                if f"last_click_{i}" not in st.session_state:
                    st.session_state[f"last_click_{i}"] = None

                # Update state if map is clicked
                if map_data and map_data.get("last_clicked"):
                    current_click = map_data["last_clicked"]
                    if current_click != st.session_state[f"last_click_{i}"]:
                        st.session_state[f"lat_val_{i}"] = current_click["lat"]
                        st.session_state[f"lon_val_{i}"] = current_click["lng"]
                        st.session_state[f"last_click_{i}"] = current_click

                # Manual coordinate input fields tied to session state
                input_col1, input_col2 = st.columns(2)
                with input_col1: 
                    target_lat = st.number_input("Latitude", format="%.6f", key=f"lat_val_{i}")
                with input_col2: 
                    target_lon = st.number_input("Longitude", format="%.6f", key=f"lon_val_{i}")

                # -- SPECTRAL ANALYSIS --
                if target_lat != 0.0 and target_lon != 0.0:
                    with st.spinner("Extracting signature..."):
                        signature, source_file, row, col = get_spectral_signature(view_filepaths, target_lat, target_lon)
                    
                    if signature is not None:
                        st.caption(f"**Source:** `{source_file}` | **Pixel:** Row `{row}`, Col `{col}`")
                        
                        chart_data = pd.DataFrame({
                            "Band Index (1-202)": range(1, 203),
                            "Reflectance": signature
                        }).set_index("Band Index (1-202)")
                        
                        st.line_chart(chart_data)
                    else:
                        st.warning("Coordinates are out of bounds for the images in this view.")
                else:
                    st.info("Click the map or enter coordinates to view the spectral signature.")

            else:
                st.info("Select at least one image to display in this view.")
            
            # Spacer for 2x2 grid
            if num_views == 4 and i < 2:
                st.write("---")
import streamlit as st
import rasterio
from rasterio.warp import transform_bounds, transform
import leafmap.foliumap as leafmap
import pandas as pd
import os
from streamlit_folium import st_folium
import folium

# 1. Configure the page
st.set_page_config(page_title="Multi-Raster Viewer", layout="wide")
st.title("EnMAP Interactive Composite Viewer")

# 2. File Inputs (Top Section)
st.write("Enter the full paths to your .tif files below (one path per line):")
file_paths_str = st.text_area(
    label='File Paths:',
    value=r"C:\Users\shash\Downloads\projects\hstool\hybiomass_south_asia\hybiomass_dataset\South_Asia\01931\024.tif",
    height=68,
    placeholder="C:\\path\\to\\file1.tif\nC:\\path\\to\\file2.tif"
)

# Parse file paths
file_paths = [f.strip() for f in file_paths_str.split('\n') if f.strip() and os.path.exists(f.strip())]

st.divider()

# 3. Visualization UI & State
with st.expander("Visualization Settings", expanded=False):
    vis_mode = st.selectbox(
        "Select Visualization Type",
        ["RGB Composite (Hyperspectral)", "Aboveground Biomass (AGBD)", "Plant Functional Type (PFT)"]
    )

    plot_bands = []
    cmap = None
    vmin_val = 0
    vmax_val = 1

    if vis_mode == "RGB Composite (Hyperspectral)":
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: r_band = st.number_input('Red:', value=45, step=1)
        with col2: g_band = st.number_input('Green:', value=29, step=1)
        with col3: b_band = st.number_input('Blue:', value=15, step=1)
        with col4: vmin_val = st.number_input('Vmin:', value=110)
        with col5: vmax_val = st.number_input('Vmax:', value=2000)
        plot_bands = [int(r_band), int(g_band), int(b_band)]

    elif vis_mode == "Aboveground Biomass (AGBD)":
        col1, col2, col3 = st.columns(3)
        with col1: cmap = st.selectbox('Colormap:', ['viridis', 'Greens', 'YlGn'])
        with col2: vmin_val = st.number_input('Vmin:', value=0.0) 
        with col3: vmax_val = st.number_input('Vmax:', value=300.0)
        plot_bands = [203]

    elif vis_mode == "Plant Functional Type (PFT)":
        col1, col2, col3 = st.columns(3)
        with col1: cmap = st.selectbox('Colormap:', ['tab20', 'Set1', 'Paired'])
        with col2: vmin_val = st.number_input('Vmin:', value=0)
        with col3: vmax_val = st.number_input('Vmax:', value=15)
        plot_bands = [204]

st.divider()

# 4. Helper Functions
def get_combined_map_center(filepaths):
    min_left, min_bottom, max_right, max_top = float('inf'), float('inf'), float('-inf'), float('-inf')
    for filepath in filepaths:
        with rasterio.open(filepath) as src:
            left, bottom, right, top = transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
            min_left, min_bottom = min(min_left, left), min(min_bottom, bottom)
            max_right, max_top = max(max_right, right), max(max_top, top)
    return (min_bottom + max_top) / 2, (min_left + max_right) / 2

def get_spectral_signature(filepaths, lat, lon):
    """Checks all rasters for the given Lat/Lon and extracts bands 1-202."""
    for filepath in filepaths:
        with rasterio.open(filepath) as src:
            # Transform input Lat/Lon to the local CRS of the GeoTIFF
            try:
                xs, ys, *_ = transform('EPSG:4326', src.crs, [lon], [lat])
                x, y = xs[0], ys[0]
                
                # Check if the transformed coordinates fall within this specific raster's bounds
                if (src.bounds.left <= x <= src.bounds.right) and (src.bounds.bottom <= y <= src.bounds.top):
                    # Sample values for bands 1 through 202
                    gen = src.sample([(x, y)], indexes=list(range(1, 203)))
                    values = list(gen)[0] 
                    return values, os.path.basename(filepath)
            except Exception:
                continue # If transformation or sampling fails, try the next file
    return None, None

# 5. Main Layout: Map (Left) & Analysis (Right)
if not file_paths:
    st.info("Please provide at least one valid .tif file path above to begin.")
else:
    # Set up a 2:1 column ratio
    col_map, col_analysis = st.columns([2, 1])

    # -- LEFT COLUMN: MAP --
    with col_map:
        st.subheader("Map View")
        lat_center, lon_center = get_combined_map_center(file_paths)
        m = leafmap.Map(center=[lat_center, lon_center], zoom=12)
        # --- NEW: Inject CSS to change the mouse cursor ---
        cursor_css = """
        <style>
        /* Force the cursor to be a crosshair for precise clicking */
        .leaflet-container { cursor: crosshair !important; }
        .leaflet-interactive { cursor: crosshair !important; }
        </style>
        """
        m.get_root().html.add_child(folium.Element(cursor_css)) # type: ignore
        # --------------------------------------------------
        for filepath in file_paths:
            m.add_raster(
                filepath, bands=plot_bands, cmap=cmap, 
                vmin=vmin_val, vmax=vmax_val, 
                layer_name=os.path.basename(filepath)
            )
            
        # FIX: Use st_folium to render the map AND capture the click dictionary
        from streamlit_folium import st_folium
        map_data = st_folium(m, height=550, use_container_width=True)

    # -- RIGHT COLUMN: ANALYSIS PANEL --
    with col_analysis:
        st.subheader("Spectral Analysis")
        st.write("Click on the map or enter coordinates manually.")
        
        # Manual Input Fields
        input_col1, input_col2 = st.columns(2)
        with input_col1: man_lat = st.number_input("Latitude", format="%.6f", value=0.0)
        with input_col2: man_lon = st.number_input("Longitude", format="%.6f", value=0.0)
        
        # Determine target coordinates
        target_lat, target_lon = None, None
        
        # FIX: map_data is now a standard Python dictionary, so we can check it safely
        if isinstance(map_data, dict) and map_data.get("last_clicked"):
            target_lat = map_data["last_clicked"]["lat"]
            target_lon = map_data["last_clicked"]["lng"]
            st.success(f"**Map Clicked:**\nLat: {target_lat:.5f} | Lon: {target_lon:.5f}")
        elif man_lat != 0.0 or man_lon != 0.0:
            target_lat = man_lat
            target_lon = man_lon
            st.info(f"**Manual Input:**\nLat: {target_lat:.5f} | Lon: {target_lon:.5f}")

        # Extract and Plot
        if target_lat is not None and target_lon is not None:
            with st.spinner("Extracting signature..."):
                signature, source_file = get_spectral_signature(file_paths, target_lat, target_lon)
                
            if signature is not None:
                st.caption(f"Source: `{source_file}`")
                
                # Create a DataFrame for Streamlit's native line chart
                chart_data = pd.DataFrame({
                    "Band Index (1-202)": range(1, 203),
                    "Reflectance": signature
                }).set_index("Band Index (1-202)")
                
                # Plot the spectral curve
                st.line_chart(chart_data)
            else:
                st.error("**Out of bounds!** The selected coordinates do not fall within the spatial extent of any loaded .tif files.")
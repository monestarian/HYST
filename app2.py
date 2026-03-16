import streamlit as st
import rasterio
from rasterio.warp import transform_bounds
import leafmap.foliumap as leafmap
import os

# 1. Configure the page
st.set_page_config(page_title="Multi-Raster Viewer", layout="wide")
st.title("EnMAP Custom Composite Viewer (Multi-File)")

# 2. Create the User Interface (UI) Elements
st.write("Enter the full paths to your .tif files below (one path per line):")
file_paths_str = st.text_area(
    label='File Paths:',
    value=r"C:\Users\shash\Downloads\projects\hstool\hybiomass_south_asia\hybiomass_dataset\South_Asia\01931\024.tif",
    height=100,
    placeholder="C:\\path\\to\\file1.tif\nC:\\path\\to\\file2.tif"
)

# Band selection widgets in neat columns
st.subheader("Band Selection")
col1, col2, col3 = st.columns(3)
with col1:
    r_band = st.number_input('Red Band:', value=45, step=1)
with col2:
    g_band = st.number_input('Green Band:', value=29, step=1)
with col3:
    b_band = st.number_input('Blue Band:', value=15, step=1)

# Contrast stretching widgets
st.subheader("Contrast Stretching")
col4, col5 = st.columns(2)
with col4:
    vmin_val = st.number_input('Vmin:', value=110)
with col5:
    vmax_val = st.number_input('Vmax:', value=2000)

# 3. Helper function to calculate the combined Lat/Lon center
def get_combined_map_center(filepaths):
    min_left, min_bottom, max_right, max_top = float('inf'), float('inf'), float('-inf'), float('-inf')
    
    for filepath in filepaths:
        with rasterio.open(filepath) as src:
            bounds = src.bounds
            crs = src.crs
            # Transform the bounding box to EPSG:4326 (Lat/Lon)
            left, bottom, right, top = transform_bounds(crs, 'EPSG:4326', *bounds)
            
            # Update combined bounding box
            min_left = min(min_left, left)
            min_bottom = min(min_bottom, bottom)
            max_right = max(max_right, right)
            max_top = max(max_top, top)
            
    lat = (min_bottom + max_top) / 2
    lon = (min_left + max_right) / 2
    return lat, lon

# 4. The main logic triggered by the button
if st.button("Render Map", type="primary"):
    # Clean up the input string into a list of valid paths
    file_paths = [f.strip() for f in file_paths_str.split('\n') if f.strip()]
    
    if file_paths:
        with st.spinner("Rendering map... Please wait."):
            try:
                # Calculate the exact center based on all provided rasters
                lat, lon = get_combined_map_center(file_paths)
                
                # Initialize map using foliumap (lowered zoom slightly to accommodate multiple files)
                m = leafmap.Map(center=[lat, lon], zoom=11)
                
                # Loop through each file and add it to the map
                for filepath in file_paths:
                    if not os.path.exists(filepath):
                        st.warning(f"File not found, skipping: {filepath}")
                        continue
                        
                    filename = os.path.basename(filepath)
                    m.add_raster(
                        filepath, 
                        bands=[int(r_band), int(g_band), int(b_band)], 
                        vmin=vmin_val, 
                        vmax=vmax_val,
                        layer_name=f"EnMAP - {filename}"
                    )
                
                # Display it in Streamlit!
                m.to_streamlit(height=600)
                
            except Exception as e:
                st.error(f"Oops! Something went wrong while rendering: {e}")
    else:
        st.warning("Please provide at least one valid file path.")
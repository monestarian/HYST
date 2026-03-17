import streamlit as st
import rasterio
from rasterio.warp import transform_bounds
import leafmap.foliumap as leafmap
import os
from texture_filters import (
    occurrence_measures,
    cooccurrence_measures,
    lee_filter,
    enhanced_lee_filter,
    frost_filter,
    enhanced_frost_filter
)

# 1. Configure the page
st.set_page_config(page_title="Multi-Raster Viewer", layout="wide")
st.title("EnMAP Custom Composite Viewer")

# 2. Create the User Interface (UI) Elements
st.write("Enter the full paths to your .tif files below (one path per line):")
file_paths_str = st.text_area(
    label='File Paths:',
    value=r"C:\Users\shash\Downloads\projects\hstool\hybiomass_south_asia\hybiomass_dataset\South_Asia\01931\024.tif",
    height=100,
    placeholder="C:\\path\\to\\file1.tif\nC:\\path\\to\\file2.tif"
)

st.divider()

# Visualization Type Selector
vis_mode = st.selectbox(
    "Select Visualization Type",
    ["RGB Composite (Hyperspectral)", "Aboveground Biomass (AGBD)", "Plant Functional Type (PFT)"]
)

st.subheader("Visualization Settings")

# Initialize variables to hold dynamic settings
plot_bands = []
cmap = None
vmin_val = 0
vmax_val = 1

# Conditionally show UI based on selected mode
if vis_mode == "RGB Composite (Hyperspectral)":
    st.write("Select bands for RGB Composite (1-202):")
    col1, col2, col3 = st.columns(3)
    with col1:
        r_band = st.number_input('Red Band:', value=45, step=1, min_value=1, max_value=202)
    with col2:
        g_band = st.number_input('Green Band:', value=29, step=1, min_value=1, max_value=202)
    with col3:
        b_band = st.number_input('Blue Band:', value=15, step=1, min_value=1, max_value=202)
    
    col4, col5 = st.columns(2)
    with col4:
        vmin_val = st.number_input('Vmin (Reflectance):', value=110)
    with col5:
        vmax_val = st.number_input('Vmax (Reflectance):', value=2000)
        
    plot_bands = [int(r_band), int(g_band), int(b_band)]

elif vis_mode == "Aboveground Biomass (AGBD)":
    st.write("Visualizing Band 203 (AGBD)")
    col1, col2, col3 = st.columns(3)
    with col1:
        cmap = st.selectbox('Colormap:', ['viridis', 'Greens', 'YlGn', 'plasma'])
    with col2:
        # Biomass default max is usually lower than reflectance, adjust as needed based on your data scale
        vmin_val = st.number_input('Vmin (Biomass):', value=0.0) 
    with col3:
        vmax_val = st.number_input('Vmax (Biomass):', value=300.0)
        
    plot_bands = [203]

elif vis_mode == "Plant Functional Type (PFT)":
    st.write("Visualizing Band 204 (MODIS Type 5 PFT Scheme)")
    col1, col2, col3 = st.columns(3)
    with col1:
        # Categorical colormaps are best for classification data
        cmap = st.selectbox('Colormap:', ['tab20', 'Set1', 'Paired'])
    with col2:
        vmin_val = st.number_input('Vmin (Class Min):', value=0)
    with col3:
        vmax_val = st.number_input('Vmax (Class Max):', value=15)
        
    plot_bands = [204]

st.divider()

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

filter_type = st.selectbox(
    "Select Filter Type",
    ["None", "Texture", "Adaptive", "FFT Filtering"]
)

texture_type = None
occ_measure = None
co_measure = None
adaptive_filter = None


if filter_type == "Texture":

    texture_type = st.selectbox(
        "Texture Method",
        ["Occurrence Measures", "Co-occurrence Measures"]
    )

    if texture_type == "Occurrence Measures":
        occ_measure = st.selectbox(
            "Occurrence Measure",
            ["Mean", "Variance", "Std", "Entropy", "Energy"]
        )

    elif texture_type == "Co-occurrence Measures":
        co_measure = st.selectbox(
            "Co-occurrence Measure",
            ["Contrast", "Correlation", "Energy", "Homogeneity"]
        )


elif filter_type == "Adaptive":

    adaptive_filter = st.selectbox(
        "Adaptive Filter",
        ["Lee", "Enhanced Lee", "Frost", "Enhanced Frost"]
    )


elif filter_type == "FFT Filtering":

    st.info("FFT filtering will be added here later.")

# 4. The main logic triggered by the button
if st.button("Render Map", type="primary"):
    # Clean up the input string into a list of valid paths
    file_paths = [f.strip() for f in file_paths_str.split('\n') if f.strip()]
    
    if file_paths:
        with st.spinner(f"Rendering {vis_mode}... Please wait."):
            try:
                # Calculate the exact center based on all provided rasters
                lat, lon = get_combined_map_center(file_paths)
                
                # Initialize map
                m = leafmap.Map(center=[lat, lon], zoom=11)
                
                # Loop through each file and add it to the map
                for filepath in file_paths:
                    if not os.path.exists(filepath):
                        st.warning(f"File not found, skipping: {filepath}")
                        continue
                        
                    filename = os.path.basename(filepath)
                        # OPEN raster
                    with rasterio.open(filepath) as src:
                        data = src.read(1)

                        # APPLY FILTERS
                        if filter_type == "Texture":
                            if texture_type == "Occurrence Measures":
                                data = occurrence_measures(data)
                            elif texture_type == "Co-occurrence Measures":
                                data = cooccurrence_measures(data)
                        if filter_type == "Adaptive":
                            if texture_type == "Lee":
                                data = lee_filter(data)
                            elif texture_type == "Enhanced Lee":
                                data = enhanced_lee_filter(data)
                            elif texture_type == "Frost":
                                data = frost_filter(data)   
                            elif texture_type == "Enhanced Frost":
                                 data = enhanced_frost_filter(data)   

                    
                    # Add raster with dynamic parameters based on mode
                    m.add_raster(
                        filepath, 
                        bands=plot_bands, 
                        cmap=cmap, # Will be ignored by leafmap if plotting 3 RGB bands
                        vmin=vmin_val, 
                        vmax=vmax_val,
                        layer_name=f"{filename} - {vis_mode.split(' ')[0]}"
                    )
                
                # Display it in Streamlit!
                m.to_streamlit(height=600)
                
            except Exception as e:
                st.error(f"Oops! Something went wrong while rendering: {e}")
    else:
        st.warning("Please provide at least one valid file path.")

st.subheader("Filters")


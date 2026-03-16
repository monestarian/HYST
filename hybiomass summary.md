This summary is designed to be pasted into a new Gemini or AI chat window to provide immediate, technical context on the HyBiomass project without re-explaining the basics.

🛰️ Project Context: HyBiomass Analysis (2025/2026)
Core Goal: Build a Python-based custom visualization tool for the HyBiomass Benchmark Dataset (DLR/NASA). The focus is on hyperspectral data visualization, biomass (AGBD) analysis, and geospatial mapping for the Asia region.

1. Dataset Technical Specifications
Format: Multi-band GeoTIFF (.tif). No external .hdr or .xml metadata provided.

Dimensions: 128x128 pixel "patches" (30m spatial resolution).

Coordinate System: Local UTM zones (stored in the GeoTIFF header).

Band Structure (204 Layers total):

Bands 0–201 (Indices 1–202): EnMAP Hyperspectral data (202 bands).

Band 202 (Index -2): GEDI-derived Aboveground Biomass Density (AGBD).

Band 203 (Index -1): Plant Functional Type (MODIS Type 5 PFT Scheme).

2. Spectral Mapping (EnMAP 202-band subset)
22 noisy water-vapor bands were removed from the original EnMAP 242-band set.

True Color RGB: Red (Band 29), Green (Band 15), Blue (Band 6).

False Color NIR: Red (Band 45), Green (Band 29), Blue (Band 15).

Atmospheric Penetration (SWIR): Band 140 (Red), Band 45 (Green), Band 29 (Blue).

Wavelength Range: ~420 nm to 2450 nm.

3. Required Python Stack (Modern)
Environment: Python 3.12 (High stability for GDAL/Rasterio 1.5+).

Libraries: * rasterio: For GeoTIFF reading and coordinate extraction via the Affine Transform.

rioxarray: For multi-dimensional "DataCube" manipulation.

leafmap: For interactive mapping and pixel inspection.

numpy 2.0 / matplotlib: For high-speed spectral signature plotting.

4. Critical Workflows
Geospatial Lookup: Coordinates are extracted from the .tif header using src.crs and src.xy(64,64), then transformed from UTM to WGS84 (Lat/Lon).

Spectral Signature: Plotting pixel values across Bands 0–201 to show the "fingerprint" of the forest.

Data Bifurcation: Even though files are merged, the tool must "slice" the array to separate imagery (0-201) from biomass labels (202).

Performance: Using .npy files for indexing metadata is preferred over .csv for O(1) random access in the visualization tool.
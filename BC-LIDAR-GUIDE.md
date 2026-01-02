# BC LiDAR Data Guide for Squamish Chief

This guide explains how to download BC LiDAR elevation data for the Squamish Chief area and convert it to Cesium terrain tiles that can be hosted locally with this application.

## Overview

**What you'll get:** High-resolution 1-2m terrain data for the Squamish Chief climbing area  
**Data size:** ~50-200 MB for the Squamish Chief area  
**Processing time:** 10-30 minutes depending on your computer  
**Tools required:** Docker (recommended) or GDAL + Cesium Terrain Builder

---

## Step 1: Download BC LiDAR Data

### Option A: BC Data Catalogue (Direct Download)

1. **Go to the LidarBC Open Data Portal:**
   ```
   https://governmentofbc.maps.arcgis.com/apps/MapSeries/index.html?appid=d06b37979b0c4f28b9e5f81b1f855c75
   ```

2. **Navigate to the Squamish Chief area:**
   - Coordinates: **49.682°N, 123.157°W**
   - Zoom in to the Stawamus Chief Provincial Park area

3. **Select and download DEM tiles:**
   - Click on available LiDAR tiles covering the Chief
   - Download the **DEM (Digital Elevation Model)** files, NOT the point clouds
   - Look for files in GeoTIFF (.tif) format
   - You'll typically need 1-4 tiles to cover the entire Chief

### Option B: BC Geographic Warehouse (WCS Service)

For programmatic access, use the Web Coverage Service:

```bash
# Install required tools
pip install owslib requests

# Download using the provided script
python scripts/download_bc_lidar.py
```

### Option C: Direct FTP Access

BC LiDAR data is available via FTP:

```
ftp://ftp.geobc.gov.bc.ca/publish/outgoing/2_LiDAR/
```

Look for directories containing "Squamish" or check the index for tile coverage.

### Recommended Tile Coverage

For the Squamish Chief, you need data covering approximately:
- **Northwest:** -123.17°, 49.70°
- **Southeast:** -123.14°, 49.67°

Download all DEM tiles that overlap this area.

---

## Step 2: Prepare the Data

### Merge Multiple Tiles (if needed)

If you downloaded multiple GeoTIFF files, merge them:

```bash
# Using GDAL (install: apt install gdal-bin or brew install gdal)
gdal_merge.py -o squamish_merged.tif tile1.tif tile2.tif tile3.tif

# Or with gdalwarp for reprojection to WGS84
gdalwarp -t_srs EPSG:4326 -r bilinear input.tif output_wgs84.tif
```

### Verify the Data

```bash
# Check the file info
gdalinfo squamish_merged.tif

# Should show:
# - Coordinate System: EPSG:4326 (WGS84) or NAD83
# - Size: e.g., 5000 x 5000 pixels
# - Pixel Size: e.g., 1m resolution
```

### Reproject to WGS84 (Required for Cesium)

BC LiDAR is often in NAD83 / BC Albers (EPSG:3005). Convert to WGS84:

```bash
gdalwarp \
  -t_srs EPSG:4326 \
  -r bilinear \
  -of GTiff \
  squamish_merged.tif \
  squamish_wgs84.tif
```

---

## Step 3: Create Cesium Terrain Tiles

### Option A: Using Docker (Recommended)

This is the easiest method using the `tumgis/ctb-quantized-mesh` Docker image:

```bash
# Create output directory
mkdir -p terrain-tiles

# Run Cesium Terrain Builder
docker run -it --rm \
  -v "$(pwd)/squamish_wgs84.tif:/data/input.tif" \
  -v "$(pwd)/terrain-tiles:/data/output" \
  tumgis/ctb-quantized-mesh \
  ctb-tile -f Mesh -C -N -o /data/output /data/input.tif
```

**Explanation of options:**
- `-f Mesh` - Output quantized-mesh format (required for Cesium)
- `-C` - Enable compression
- `-N` - Generate vertex normals (for lighting)
- `-o` - Output directory

### Option B: Using ctb-tile Directly

If you have Cesium Terrain Builder installed locally:

```bash
# Generate terrain tiles
ctb-tile -f Mesh -C -N -o terrain-tiles squamish_wgs84.tif

# Generate layer.json metadata
ctb-tile -f Mesh -C -N -l -o terrain-tiles squamish_wgs84.tif
```

### Option C: Using GDAL + Python (Alternative)

See `scripts/create_terrain_tiles.py` for a pure-Python approach using GDAL.

---

## Step 4: Generate layer.json

The terrain tiles need a `layer.json` file for Cesium to read them. If not auto-generated, create one:

```bash
# Using ctb-tile
ctb-tile -f Mesh -l -o terrain-tiles squamish_wgs84.tif
```

Or create manually - see `terrain-tiles/layer.json.example` in this repository.

---

## Step 5: Copy Tiles to Project

Move the generated terrain tiles to your project:

```bash
# Copy the entire terrain-tiles directory
cp -r terrain-tiles /path/to/climbing-map/

# Verify structure
ls -la climbing-map/terrain-tiles/
# Should contain:
# - layer.json
# - 0/, 1/, 2/, ... (zoom level directories)
```

### Expected Directory Structure

```
climbing-map/
├── terrain-tiles/
│   ├── layer.json
│   ├── 0/
│   │   └── 0/
│   │       └── 0.terrain
│   ├── 1/
│   │   └── ...
│   ├── ...
│   └── 15/
│       └── ...
├── index.html
├── app.js
└── ...
```

---

## Step 6: Test the Terrain

1. Start the local server:
   ```bash
   python -m http.server 8000
   ```

2. Open http://localhost:8000 in your browser

3. Check the browser console - you should see:
   ```
   ✅ Using local BC LiDAR terrain
   ```

4. Navigate to the Squamish Chief - you should see detailed terrain!

---

## Troubleshooting

### "Local terrain not available" error

1. Check that `terrain-tiles/layer.json` exists
2. Verify the terrain tiles were generated correctly
3. Check browser network tab for 404 errors

### Terrain appears flat

1. Verify your input DEM has elevation data (not all zeros)
2. Check that the coordinate system is WGS84 (EPSG:4326)
3. Try increasing terrain exaggeration in the UI

### Tiles are too large

Reduce the zoom levels generated:

```bash
ctb-tile -f Mesh -C -N -s 0 -e 14 -o terrain-tiles input.tif
```

### CORS errors

If hosting on a different domain, configure your server to send CORS headers:

```
Access-Control-Allow-Origin: *
```

---

## Quick Reference Commands

```bash
# Full pipeline - single command
docker run -it --rm \
  -v "$(pwd):/data" \
  tumgis/ctb-quantized-mesh \
  bash -c "
    gdalwarp -t_srs EPSG:4326 -r bilinear /data/input.tif /data/wgs84.tif && \
    ctb-tile -f Mesh -C -N -o /data/terrain-tiles /data/wgs84.tif && \
    ctb-tile -f Mesh -l -o /data/terrain-tiles /data/wgs84.tif
  "
```

---

## Data Sources Reference

| Source | URL | Format |
|--------|-----|--------|
| LidarBC Map Viewer | https://governmentofbc.maps.arcgis.com/apps/MapSeries/index.html?appid=d06b37979b0c4f28b9e5f81b1f855c75 | Web Map |
| BC Data Catalogue | https://catalogue.data.gov.bc.ca/dataset?q=lidar | Various |
| BC FTP Server | ftp://ftp.geobc.gov.bc.ca/publish/outgoing/2_LiDAR/ | GeoTIFF |
| GeoBC WCS | https://openmaps.gov.bc.ca/geo/pub/wcs | WCS |

---

## Sample layer.json

If you need to create `layer.json` manually:

```json
{
  "tilejson": "2.1.0",
  "format": "quantized-mesh-1.0",
  "version": "1.0.0",
  "scheme": "tms",
  "tiles": ["{z}/{x}/{y}.terrain"],
  "minzoom": 0,
  "maxzoom": 15,
  "bounds": [-123.20, 49.65, -123.10, 49.72],
  "projection": "EPSG:4326",
  "available": [
    [{"startX": 0, "startY": 0, "endX": 1, "endY": 0}]
  ]
}
```

---

## Need Help?

- **Cesium Terrain Builder Docs:** https://github.com/geo-data/cesium-terrain-builder
- **GDAL Documentation:** https://gdal.org/
- **BC LiDAR Program:** https://www2.gov.bc.ca/gov/content/data/geographic-data-services/lidarbc
- **CesiumJS Terrain Docs:** https://cesium.com/learn/cesiumjs/ref-doc/CesiumTerrainProvider.html

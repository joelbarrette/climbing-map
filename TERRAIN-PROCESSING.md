# BC LiDAR to Cesium Terrain Tiles - Processing Guide

This guide documents the complete workflow for converting BC LiDAR LAZ files into Cesium quantized-mesh terrain tiles for self-hosted use.

## Overview

**Pipeline:** LAZ → DEM (GeoTIFF) → Reprojected GeoTIFF → Cesium Terrain Tiles

**Tools Required (all via Docker):**
- `pdal/pdal` - Point cloud processing
- `ghcr.io/osgeo/gdal:alpine-small-latest` - Raster processing
- `tumgis/ctb-quantized-mesh` - Cesium terrain tile generation

---

## Step 1: Download BC LiDAR Data

1. Go to [BC LiDAR Portal](https://governmentofbc.maps.arcgis.com/apps/MapSeries/index.html?appid=d06b37571a664c94bce811f87eb5e23c)
2. Navigate to your area of interest
3. Download the LAZ file(s) - they will be in NAD83/UTM Zone 10N (EPSG:3157) or similar

Place downloaded files in `data/raw/`:
```bash
mkdir -p data/raw data/processed
mv ~/Downloads/*.laz data/raw/
```

---

## Step 2: Convert LAZ to DEM (GeoTIFF)

Create a PDAL pipeline file:

```bash
cat > data/pipeline.json << 'EOF'
{
  "pipeline": [
    {
      "type": "readers.las",
      "filename": "/data/raw/INPUT_FILE.laz"
    },
    {
      "type": "filters.range",
      "limits": "Classification[2:2]"
    },
    {
      "type": "writers.gdal",
      "filename": "/data/processed/dem.tif",
      "resolution": 1.0,
      "output_type": "mean",
      "gdalopts": "COMPRESS=LZW"
    }
  ]
}
EOF
```

**Note:** Replace `INPUT_FILE.laz` with your actual filename.

**Classification filter options:**
- `Classification[2:2]` - Ground points only (recommended for terrain)
- Remove the filter entirely to use all points (for DSM/surface model)

Run PDAL:
```bash
docker run --rm -v "$(pwd)/data:/data" pdal/pdal \
  pdal pipeline /data/pipeline.json
```

---

## Step 3: Reproject to WGS84

Cesium requires WGS84 (EPSG:4326) coordinates:

```bash
docker run --rm -v "$(pwd)/data/processed:/data" \
  ghcr.io/osgeo/gdal:alpine-small-latest \
  gdalwarp -t_srs EPSG:4326 -r bilinear \
  /data/dem.tif /data/wgs84.tif
```

Verify the output bounds:
```bash
docker run --rm -v "$(pwd)/data/processed:/data" \
  ghcr.io/osgeo/gdal:alpine-small-latest \
  gdalinfo /data/wgs84.tif 2>&1 | grep -E "Upper|Lower|Center|Size"
```

**Save these coordinates** - you'll need them for `layer.json`.

---

## Step 4: Generate Cesium Terrain Tiles

```bash
docker run --rm \
  -v "$(pwd)/data/processed:/data" \
  -v "$(pwd)/terrain-tiles:/output" \
  tumgis/ctb-quantized-mesh \
  ctb-tile -f Mesh -C -o /output /data/wgs84.tif
```

**Flags:**
- `-f Mesh` - Output quantized-mesh format
- `-C` - Enable gzip compression
- `-o /output` - Output directory

This creates a directory structure like:
```
terrain-tiles/
├── 0/0/0.terrain
├── 1/0/1.terrain
├── 2/1/3.terrain
├── ...zoom levels...
└── layer.json (auto-generated but needs fixing)
```

---

## Step 5: Fix layer.json

The auto-generated `layer.json` needs corrections. Create a proper one:

```bash
cat > terrain-tiles/layer.json << 'EOF'
{
  "tilejson": "2.1.0",
  "name": "Your Terrain Name",
  "description": "Description of terrain",
  "version": "1.1.0",
  "format": "quantized-mesh-1.0",
  "attribution": "BC LiDAR Program",
  "scheme": "tms",
  "tiles": ["{z}/{x}/{y}.terrain"],
  "projection": "EPSG:4326",
  "bounds": [WEST, SOUTH, EAST, NORTH],
  "minzoom": 0,
  "maxzoom": 18
}
EOF
```

**Replace bounds** with the values from Step 3's gdalinfo output:
- `WEST` = Upper Left X (longitude, negative for BC)
- `SOUTH` = Lower Left Y (latitude)
- `EAST` = Lower Right X (longitude)
- `NORTH` = Upper Left Y (latitude)

### Optional: Add `available` array

For better tile loading hints, add an `available` array listing which tiles exist at each zoom level. You can generate this by inspecting the tile directory:

```bash
# List all generated tiles
find terrain-tiles -name "*.terrain" | head -50
```

---

## Step 6: Serve with Proper Headers

**CRITICAL:** Cesium terrain tiles are gzip compressed and MUST be served with `Content-Encoding: gzip` header.

### Option A: Custom Python Server (Development)

Use this `server.py`:

```python
#!/usr/bin/env python3
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        
        # Critical: terrain files are gzip compressed
        if self.path.endswith('.terrain'):
            self.send_header('Content-Encoding', 'gzip')
            self.send_header('Content-Type', 'application/octet-stream')
        
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

if __name__ == '__main__':
    port = 8000
    server = HTTPServer(('', port), CORSRequestHandler)
    print(f'Serving at http://localhost:{port}')
    server.serve_forever()
```

Run: `python3 server.py`

### Option B: Nginx (Production)

```nginx
location /terrain-tiles/ {
    add_header Access-Control-Allow-Origin *;
    add_header Content-Encoding gzip;
    types {
        application/octet-stream terrain;
    }
}
```

### Option C: Decompress tiles (Alternative)

If you can't set headers, decompress the tiles:

```bash
find terrain-tiles -name "*.terrain" -exec sh -c 'gunzip -c "$1" > "$1.tmp" && mv "$1.tmp" "$1"' _ {} \;
```

---

## Step 7: Configure Cesium Terrain Provider

In your app's terrain configuration:

```javascript
async function createTerrainProvider() {
    return await Cesium.CesiumTerrainProvider.fromUrl(
        'terrain-tiles/',  // Relative path to tiles
        {
            requestVertexNormals: false,
            requestWaterMask: false
        }
    );
}

// Usage
const viewer = new Cesium.Viewer('cesiumContainer', {
    baseLayerPicker: false,
    baseLayer: false,  // Disable default imagery
    terrainProvider: await createTerrainProvider()
});

// Add imagery separately
viewer.imageryLayers.addImageryProvider(
    new Cesium.OpenStreetMapImageryProvider({
        url: 'https://tile.openstreetmap.org/'
    })
);
```

---

## Troubleshooting

### Error: "Invalid typed array length: 8894653434"
**Cause:** Server not sending `Content-Encoding: gzip` header for .terrain files.
**Fix:** Use the custom server.py or configure your server to send proper headers.

### Error: 401 Unauthorized (Cesium Ion)
**Cause:** Code still references Cesium Ion.
**Fix:** Remove all Ion references, set `baseLayerPicker: false`, use OpenStreetMap imagery.

### Terrain appears flat / tiles not loading
**Cause:** Incorrect bounds in layer.json or tiles in wrong location.
**Fix:** 
1. Verify bounds match gdalinfo output
2. Check tile structure: `ls terrain-tiles/*/`
3. Verify your camera position is within the terrain bounds

### No ground points in LAZ file
**Cause:** LAZ file is a DSM (surface model) not classified.
**Fix:** Remove the classification filter from the PDAL pipeline, or use a different LAZ file.

---

## Quick Reference Commands

```bash
# Check LAZ file info
docker run --rm -v "$(pwd)/data:/data" pdal/pdal \
  pdal info /data/raw/INPUT.laz --summary

# Check GeoTIFF bounds
docker run --rm -v "$(pwd)/data/processed:/data" \
  ghcr.io/osgeo/gdal:alpine-small-latest \
  gdalinfo /data/wgs84.tif

# Count generated tiles
find terrain-tiles -name "*.terrain" | wc -l

# Check if tiles are gzip compressed
file terrain-tiles/0/0/0.terrain
# Should show: "gzip compressed data"

# Test tile serving headers
curl -I http://localhost:8000/terrain-tiles/0/0/0.terrain
# Should include: Content-Encoding: gzip
```

---

## File Structure After Processing

```
climbing-map/
├── data/
│   ├── raw/
│   │   └── *.laz              # Original LiDAR files
│   ├── processed/
│   │   ├── dem.tif            # Intermediate DEM
│   │   └── wgs84.tif          # Reprojected DEM
│   └── pipeline.json          # PDAL pipeline
├── terrain-tiles/
│   ├── layer.json             # Terrain metadata
│   └── {z}/{x}/{y}.terrain    # Tile files
├── server.py                  # Custom HTTP server
├── index.html                 # Web app
├── app.js                     # Cesium viewer
└── terrain.js                 # Terrain provider config
```

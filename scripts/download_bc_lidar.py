#!/usr/bin/env python3
"""
Download BC LiDAR DEM data for the Squamish Chief area.

This script downloads elevation data from the BC Geographic Warehouse
using the Web Coverage Service (WCS).

Usage:
    python download_bc_lidar.py

Requirements:
    pip install owslib requests numpy
"""

import os
import sys
import requests
from pathlib import Path

# Squamish Chief bounding box (WGS84)
BOUNDS = {
    'west': -123.20,
    'south': 49.65,
    'east': -123.10,
    'north': 49.72
}

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / 'data' / 'raw'

def download_bc_dem():
    """Download BC DEM data for the Squamish Chief area."""
    
    print("=" * 60)
    print("BC LiDAR DEM Downloader for Squamish Chief")
    print("=" * 60)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\nTarget area:")
    print(f"  West:  {BOUNDS['west']}")
    print(f"  East:  {BOUNDS['east']}")
    print(f"  South: {BOUNDS['south']}")
    print(f"  North: {BOUNDS['north']}")
    
    # BC Data Catalogue WCS endpoint for DEM
    # Note: This uses the CDEM (Canadian Digital Elevation Model) as fallback
    # For actual BC LiDAR, you'll need to download from the map viewer
    
    print("\n" + "=" * 60)
    print("AUTOMATIC DOWNLOAD OPTIONS")
    print("=" * 60)
    
    print("""
Option 1: Canadian Digital Elevation Model (CDEM)
-------------------------------------------------
This is lower resolution (~20m) but covers all of Canada.
Good for testing, but BC LiDAR is much better for climbing.

To download CDEM:
    1. Visit: https://open.canada.ca/data/en/dataset/7f245e4d-76c2-4caa-951a-45d1d2051333
    2. Download tiles covering the Squamish area
    3. Or use the script below with 'cdem' option

Option 2: BC LiDAR (Recommended - Manual Download)
--------------------------------------------------
High resolution (~1-2m), perfect for climbing routes.

Steps:
    1. Open the BC LiDAR Map Viewer:
       https://governmentofbc.maps.arcgis.com/apps/MapSeries/index.html?appid=d06b37979b0c4f28b9e5f81b1f855c75
    
    2. Navigate to Squamish Chief (49.682°N, 123.157°W)
    
    3. Click on available LiDAR coverage tiles
    
    4. Download the DEM (Digital Elevation Model) files
       - Look for GeoTIFF (.tif) format
       - Download all tiles that cover the Chief
    
    5. Save files to: {output_dir}

Option 3: BC Open Data API
--------------------------
Some datasets are available via API. Checking availability...
""".format(output_dir=OUTPUT_DIR))

    # Try to fetch from BC Open Data
    check_bc_opendata()
    
    print("\n" + "=" * 60)
    print("RECOMMENDED: Manual Download from LidarBC")
    print("=" * 60)
    print(f"""
The best terrain data comes from downloading directly from LidarBC.

1. Go to: https://governmentofbc.maps.arcgis.com/apps/MapSeries/index.html?appid=d06b37979b0c4f28b9e5f81b1f855c75

2. Use the map to find Squamish Chief (search for "Stawamus Chief")

3. Click on LiDAR tiles that cover the area

4. Download DEM files (GeoTIFF format)

5. Save to: {output_dir}

6. Then run: python scripts/process_terrain.py
""".format(output_dir=OUTPUT_DIR))


def check_bc_opendata():
    """Check BC Open Data for available elevation data."""
    
    print("Checking BC Open Data API...")
    
    try:
        # BC Data Catalogue API
        api_url = "https://catalogue.data.gov.bc.ca/api/3/action/package_search"
        params = {
            'q': 'lidar dem squamish',
            'rows': 5
        }
        
        response = requests.get(api_url, params=params, timeout=10)
        
        if response.ok:
            data = response.json()
            results = data.get('result', {}).get('results', [])
            
            if results:
                print(f"\nFound {len(results)} related datasets:")
                for r in results:
                    print(f"  - {r.get('title', 'Unknown')}")
                    print(f"    ID: {r.get('id', 'N/A')}")
            else:
                print("  No direct matches found via API")
        else:
            print(f"  API returned status {response.status_code}")
            
    except Exception as e:
        print(f"  Could not connect to API: {e}")


def download_cdem_fallback():
    """Download Canadian DEM as a fallback (lower resolution)."""
    
    print("\nDownloading Canadian DEM (fallback, ~20m resolution)...")
    
    # CDEM WCS endpoint
    wcs_url = "https://datacube.services.geo.ca/ows/elevation"
    
    params = {
        'service': 'WCS',
        'version': '2.0.1', 
        'request': 'GetCoverage',
        'CoverageId': 'dtm',
        'subset': [
            f"Long({BOUNDS['west']},{BOUNDS['east']})",
            f"Lat({BOUNDS['south']},{BOUNDS['north']})"
        ],
        'format': 'image/tiff'
    }
    
    try:
        response = requests.get(wcs_url, params=params, timeout=60, stream=True)
        
        if response.ok:
            output_file = OUTPUT_DIR / 'cdem_squamish.tif'
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"  Downloaded to: {output_file}")
            return str(output_file)
        else:
            print(f"  Download failed: {response.status_code}")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    return None


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'cdem':
        download_cdem_fallback()
    else:
        download_bc_dem()

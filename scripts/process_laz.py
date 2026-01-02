#!/usr/bin/env python3
"""
Process LAZ/LAS point cloud files into Cesium terrain tiles.

This script converts BC LiDAR LAZ files to:
1. Raster DEM (GeoTIFF)
2. Cesium quantized-mesh terrain tiles

Usage:
    python process_laz.py <input.laz>
    
Example:
    python process_laz.py ../data/raw/dsm.laz

Requirements:
    - Docker (recommended) OR
    - PDAL (apt install pdal)
    - GDAL (apt install gdal-bin)
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

# Directories
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
RAW_DATA_DIR = PROJECT_DIR / 'data' / 'raw'
PROCESSED_DIR = PROJECT_DIR / 'data' / 'processed'
OUTPUT_DIR = PROJECT_DIR / 'terrain-tiles'


def check_dependencies():
    """Check if required tools are available."""
    print("Checking dependencies...")
    
    docker = shutil.which('docker') is not None
    pdal = shutil.which('pdal') is not None
    gdal = shutil.which('gdalwarp') is not None
    
    print(f"  Docker: {'✅' if docker else '❌'}")
    print(f"  PDAL:   {'✅' if pdal else '❌'}")
    print(f"  GDAL:   {'✅' if gdal else '❌'}")
    
    return {'docker': docker, 'pdal': pdal, 'gdal': gdal}


def convert_laz_to_dem_docker(laz_file, output_tif):
    """Convert LAZ to DEM using Docker."""
    
    print(f"\n📦 Converting LAZ to DEM using Docker...")
    
    laz_path = Path(laz_file).resolve()
    output_path = Path(output_tif).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # PDAL pipeline for LAZ to raster
    pipeline = {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": "/data/input.laz"
            },
            {
                "type": "filters.range",
                "limits": "Classification![7:7]"  # Exclude noise
            },
            {
                "type": "writers.gdal",
                "filename": "/data/output.tif",
                "output_type": "idw",  # Inverse distance weighting
                "resolution": 1.0,     # 1 meter resolution
                "radius": 2.0,
                "gdaldriver": "GTiff",
                "data_type": "float32"
            }
        ]
    }
    
    # Write pipeline to temp file
    pipeline_file = PROCESSED_DIR / 'pipeline.json'
    pipeline_file.parent.mkdir(parents=True, exist_ok=True)
    with open(pipeline_file, 'w') as f:
        json.dump(pipeline, f)
    
    # Run PDAL in Docker
    cmd = [
        'docker', 'run', '--rm',
        '-v', f'{laz_path.parent}:/data/input_dir',
        '-v', f'{output_path.parent}:/data',
        '-v', f'{pipeline_file.parent}:/data/config',
        'pdal/pdal:latest',
        'pdal', 'pipeline', '/data/config/pipeline.json',
        '--readers.las.filename=/data/input_dir/' + laz_path.name,
        '--writers.gdal.filename=/data/output.tif'
    ]
    
    print(f"  Running PDAL pipeline...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"  ❌ PDAL error: {result.stderr}")
        # Try alternative method
        return convert_laz_simple_docker(laz_file, output_tif)
    
    # Rename output
    temp_output = output_path.parent / 'output.tif'
    if temp_output.exists():
        shutil.move(temp_output, output_path)
    
    return output_path.exists()


def convert_laz_simple_docker(laz_file, output_tif):
    """Simpler LAZ conversion using las2dem in Docker."""
    
    print(f"\n📦 Trying alternative conversion method...")
    
    laz_path = Path(laz_file).resolve()
    output_path = Path(output_tif).resolve()
    
    # Use LAStools approach with PDAL
    cmd = [
        'docker', 'run', '--rm',
        '-v', f'{laz_path.parent}:/input',
        '-v', f'{output_path.parent}:/output',
        'pdal/pdal:latest',
        'pdal', 'translate',
        f'/input/{laz_path.name}',
        '/output/dem.tif',
        '--writers.gdal.resolution=1.0',
        '--writers.gdal.output_type=idw'
    ]
    
    print(f"  Running pdal translate...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"  PDAL translate output: {result.stderr}")
    
    temp_output = output_path.parent / 'dem.tif'
    if temp_output.exists():
        shutil.move(temp_output, output_path)
        return True
    
    return False


def convert_laz_to_dem_pdal(laz_file, output_tif):
    """Convert LAZ to DEM using local PDAL."""
    
    print(f"\n📦 Converting LAZ to DEM using local PDAL...")
    
    output_path = Path(output_tif)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # PDAL pipeline
    pipeline = {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": str(laz_file)
            },
            {
                "type": "filters.range",
                "limits": "Classification![7:7]"
            },
            {
                "type": "writers.gdal",
                "filename": str(output_tif),
                "output_type": "idw",
                "resolution": 1.0,
                "radius": 2.0,
                "gdaldriver": "GTiff",
                "data_type": "float32"
            }
        ]
    }
    
    pipeline_file = PROCESSED_DIR / 'pipeline.json'
    with open(pipeline_file, 'w') as f:
        json.dump(pipeline, f)
    
    cmd = ['pdal', 'pipeline', str(pipeline_file)]
    
    print(f"  Running: pdal pipeline...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"  ❌ Error: {result.stderr}")
        return False
    
    return output_path.exists()


def reproject_to_wgs84(input_tif, output_tif):
    """Reproject DEM to WGS84 for Cesium."""
    
    print(f"\n🌍 Reprojecting to WGS84...")
    
    output_path = Path(output_tif)
    
    # Try Docker first
    if shutil.which('docker'):
        input_path = Path(input_tif).resolve()
        
        cmd = [
            'docker', 'run', '--rm',
            '-v', f'{input_path.parent}:/data',
            'osgeo/gdal:latest',
            'gdalwarp',
            '-t_srs', 'EPSG:4326',
            '-r', 'bilinear',
            '-of', 'GTiff',
            '-co', 'COMPRESS=LZW',
            f'/data/{input_path.name}',
            f'/data/wgs84.tif'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        temp_output = input_path.parent / 'wgs84.tif'
        if temp_output.exists():
            shutil.move(temp_output, output_path)
            return True
    
    # Try local GDAL
    if shutil.which('gdalwarp'):
        cmd = [
            'gdalwarp',
            '-t_srs', 'EPSG:4326',
            '-r', 'bilinear',
            '-of', 'GTiff',
            '-co', 'COMPRESS=LZW',
            str(input_tif),
            str(output_tif)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return output_path.exists()
    
    print("  ❌ No GDAL available!")
    return False


def create_terrain_tiles(dem_tif):
    """Convert DEM to Cesium terrain tiles."""
    
    print(f"\n🏔️  Creating Cesium terrain tiles...")
    
    dem_path = Path(dem_tif).resolve()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Use Docker with CTB
    cmd = [
        'docker', 'run', '--rm',
        '-v', f'{dem_path.parent}:/data/input',
        '-v', f'{OUTPUT_DIR}:/data/output',
        'tumgis/ctb-quantized-mesh',
        'ctb-tile',
        '-f', 'Mesh',
        '-C',
        '-N',
        '-o', '/data/output',
        f'/data/input/{dem_path.name}'
    ]
    
    print(f"  Running ctb-tile...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"  Warning: {result.stderr}")
    
    # Create layer.json
    cmd = [
        'docker', 'run', '--rm',
        '-v', f'{dem_path.parent}:/data/input',
        '-v', f'{OUTPUT_DIR}:/data/output',
        'tumgis/ctb-quantized-mesh',
        'ctb-tile',
        '-f', 'Mesh',
        '-l',
        '-o', '/data/output',
        f'/data/input/{dem_path.name}'
    ]
    
    print(f"  Creating layer.json...")
    subprocess.run(cmd, capture_output=True, text=True)
    
    return (OUTPUT_DIR / 'layer.json').exists()


def get_file_info(filepath):
    """Get info about a LAZ/TIF file."""
    
    filepath = Path(filepath)
    size_mb = filepath.stat().st_size / (1024 * 1024)
    
    print(f"\n📄 File: {filepath.name}")
    print(f"   Size: {size_mb:.1f} MB")
    
    # Try to get more info with PDAL
    if shutil.which('pdal'):
        cmd = ['pdal', 'info', '--summary', str(filepath)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            try:
                info = json.loads(result.stdout)
                summary = info.get('summary', {})
                bounds = summary.get('bounds', {})
                print(f"   Points: {summary.get('num_points', 'N/A'):,}")
                if bounds:
                    print(f"   Bounds: ({bounds.get('minx', 0):.2f}, {bounds.get('miny', 0):.2f}) to ({bounds.get('maxx', 0):.2f}, {bounds.get('maxy', 0):.2f})")
            except:
                pass
    elif shutil.which('docker'):
        cmd = [
            'docker', 'run', '--rm',
            '-v', f'{filepath.parent}:/data',
            'pdal/pdal:latest',
            'pdal', 'info', '--summary', f'/data/{filepath.name}'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            try:
                info = json.loads(result.stdout)
                summary = info.get('summary', {})
                print(f"   Points: {summary.get('num_points', 'N/A'):,}")
            except:
                pass


def main():
    print("=" * 60)
    print("LAZ to Cesium Terrain Processor")
    print("=" * 60)
    
    # Check for input file
    if len(sys.argv) < 2:
        # Look for LAZ files in data/raw
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        laz_files = list(RAW_DATA_DIR.glob('*.laz')) + list(RAW_DATA_DIR.glob('*.las'))
        
        if not laz_files:
            print(f"\n❌ No LAZ file specified and none found in {RAW_DATA_DIR}")
            print(f"\nUsage: python {sys.argv[0]} <path/to/file.laz>")
            print(f"\nOr place your .laz files in: {RAW_DATA_DIR}")
            sys.exit(1)
        
        laz_file = laz_files[0]
        print(f"\n📂 Found: {laz_file}")
    else:
        laz_file = Path(sys.argv[1])
        if not laz_file.exists():
            print(f"\n❌ File not found: {laz_file}")
            sys.exit(1)
    
    # Check dependencies
    deps = check_dependencies()
    
    if not deps['docker'] and not deps['pdal']:
        print("\n❌ Docker or PDAL is required!")
        print("   Install Docker: https://docs.docker.com/get-docker/")
        print("   Or install PDAL: apt install pdal")
        sys.exit(1)
    
    # Get file info
    get_file_info(laz_file)
    
    # Create directories
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Convert LAZ to DEM
    dem_file = PROCESSED_DIR / 'dem.tif'
    
    if deps['docker']:
        success = convert_laz_to_dem_docker(laz_file, dem_file)
    elif deps['pdal']:
        success = convert_laz_to_dem_pdal(laz_file, dem_file)
    else:
        success = False
    
    if not success or not dem_file.exists():
        print("\n❌ Failed to convert LAZ to DEM")
        print("\nTry manual conversion:")
        print(f"  pdal translate {laz_file} {dem_file} --writers.gdal.resolution=1.0")
        sys.exit(1)
    
    print(f"  ✅ DEM created: {dem_file}")
    
    # Step 2: Reproject to WGS84
    wgs84_file = PROCESSED_DIR / 'wgs84.tif'
    
    if not reproject_to_wgs84(dem_file, wgs84_file):
        print("\n❌ Failed to reproject to WGS84")
        sys.exit(1)
    
    print(f"  ✅ Reprojected: {wgs84_file}")
    
    # Step 3: Create terrain tiles
    if not create_terrain_tiles(wgs84_file):
        print("\n⚠️  Terrain tiles may not have been created correctly")
        print(f"    Check {OUTPUT_DIR} for output")
    
    # Verify output
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    layer_json = OUTPUT_DIR / 'layer.json'
    if layer_json.exists():
        print(f"✅ layer.json exists")
        
        terrain_files = list(OUTPUT_DIR.rglob('*.terrain'))
        print(f"✅ {len(terrain_files)} terrain tiles created")
        
        total_size = sum(f.stat().st_size for f in OUTPUT_DIR.rglob('*') if f.is_file())
        print(f"✅ Total size: {total_size / (1024*1024):.1f} MB")
        
        print("\n" + "=" * 60)
        print("SUCCESS! 🎉")
        print("=" * 60)
        print(f"\nYour terrain is ready! Start the server:")
        print(f"  cd {PROJECT_DIR}")
        print(f"  python -m http.server 8000")
        print(f"\nThen open: http://localhost:8000")
    else:
        print(f"❌ layer.json not found")
        print(f"\nManual steps to try:")
        print(f"  1. Check that {wgs84_file} was created")
        print(f"  2. Run: docker run -v {PROCESSED_DIR}:/data tumgis/ctb-quantized-mesh ctb-tile -f Mesh -C -N -o /data/tiles /data/wgs84.tif")


if __name__ == '__main__':
    main()

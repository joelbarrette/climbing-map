#!/usr/bin/env python3
"""
Process BC LiDAR DEM data into Cesium terrain tiles.

This script converts GeoTIFF DEM files into quantized-mesh terrain tiles
that can be used with CesiumJS.

Usage:
    python process_terrain.py [input.tif]

If no input file is specified, processes all .tif files in data/raw/

Requirements:
    - Docker (recommended) OR
    - GDAL (apt install gdal-bin)
    - Cesium Terrain Builder (https://github.com/geo-data/cesium-terrain-builder)
"""

import os
import sys
import subprocess
import shutil
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
    
    # Check for Docker
    docker_available = shutil.which('docker') is not None
    print(f"  Docker: {'✅ Available' if docker_available else '❌ Not found'}")
    
    # Check for GDAL
    gdal_available = shutil.which('gdalwarp') is not None
    print(f"  GDAL: {'✅ Available' if gdal_available else '❌ Not found'}")
    
    # Check for ctb-tile
    ctb_available = shutil.which('ctb-tile') is not None
    print(f"  ctb-tile: {'✅ Available' if ctb_available else '❌ Not found'}")
    
    if not docker_available and not (gdal_available and ctb_available):
        print("\n⚠️  Either Docker or (GDAL + ctb-tile) is required!")
        print("   Install Docker: https://docs.docker.com/get-docker/")
        print("   Or install GDAL: apt install gdal-bin")
        return False
    
    return docker_available, gdal_available, ctb_available


def find_input_files():
    """Find GeoTIFF files to process."""
    
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    tif_files = list(RAW_DATA_DIR.glob('*.tif')) + list(RAW_DATA_DIR.glob('*.tiff'))
    
    if not tif_files:
        print(f"\n❌ No GeoTIFF files found in {RAW_DATA_DIR}")
        print("\nPlease download BC LiDAR DEM data first.")
        print("See BC-LIDAR-GUIDE.md for instructions.")
        return []
    
    print(f"\nFound {len(tif_files)} GeoTIFF file(s):")
    for f in tif_files:
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  - {f.name} ({size_mb:.1f} MB)")
    
    return tif_files


def process_with_docker(input_files):
    """Process terrain using Docker container."""
    
    print("\n" + "=" * 60)
    print("Processing with Docker")
    print("=" * 60)
    
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Merge files if multiple
    if len(input_files) > 1:
        print("\nMerging multiple input files...")
        merged_file = PROCESSED_DIR / 'merged.tif'
        
        cmd = [
            'docker', 'run', '--rm',
            '-v', f'{RAW_DATA_DIR}:/data/input',
            '-v', f'{PROCESSED_DIR}:/data/output',
            'osgeo/gdal:latest',
            'gdal_merge.py', '-o', '/data/output/merged.tif'
        ] + [f'/data/input/{f.name}' for f in input_files]
        
        print(f"Running: {' '.join(cmd[:8])}...")
        subprocess.run(cmd, check=True)
        input_file = merged_file
    else:
        input_file = input_files[0]
    
    # Reproject to WGS84
    print("\nReprojecting to WGS84...")
    wgs84_file = PROCESSED_DIR / 'wgs84.tif'
    
    cmd = [
        'docker', 'run', '--rm',
        '-v', f'{input_file.parent}:/data/input',
        '-v', f'{PROCESSED_DIR}:/data/output',
        'osgeo/gdal:latest',
        'gdalwarp',
        '-t_srs', 'EPSG:4326',
        '-r', 'bilinear',
        '-of', 'GTiff',
        f'/data/input/{input_file.name}',
        '/data/output/wgs84.tif'
    ]
    
    print(f"Running: gdalwarp...")
    subprocess.run(cmd, check=True)
    
    # Create terrain tiles
    print("\nCreating Cesium terrain tiles...")
    
    cmd = [
        'docker', 'run', '--rm',
        '-v', f'{PROCESSED_DIR}:/data/input',
        '-v', f'{OUTPUT_DIR}:/data/output',
        'tumgis/ctb-quantized-mesh',
        'ctb-tile',
        '-f', 'Mesh',
        '-C',  # Compression
        '-N',  # Vertex normals
        '-o', '/data/output',
        '/data/input/wgs84.tif'
    ]
    
    print(f"Running: ctb-tile...")
    subprocess.run(cmd, check=True)
    
    # Create layer.json
    print("\nCreating layer.json metadata...")
    
    cmd = [
        'docker', 'run', '--rm',
        '-v', f'{PROCESSED_DIR}:/data/input',
        '-v', f'{OUTPUT_DIR}:/data/output',
        'tumgis/ctb-quantized-mesh',
        'ctb-tile',
        '-f', 'Mesh',
        '-l',  # Layer.json only
        '-o', '/data/output',
        '/data/input/wgs84.tif'
    ]
    
    subprocess.run(cmd, check=True)
    
    print("\n✅ Terrain tiles created successfully!")
    print(f"   Output: {OUTPUT_DIR}")


def process_with_local_tools(input_files, gdal_available, ctb_available):
    """Process terrain using locally installed tools."""
    
    print("\n" + "=" * 60)
    print("Processing with local tools")
    print("=" * 60)
    
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Merge files if multiple
    if len(input_files) > 1:
        print("\nMerging multiple input files...")
        merged_file = PROCESSED_DIR / 'merged.tif'
        
        cmd = ['gdal_merge.py', '-o', str(merged_file)] + [str(f) for f in input_files]
        subprocess.run(cmd, check=True)
        input_file = merged_file
    else:
        input_file = input_files[0]
    
    # Reproject to WGS84
    print("\nReprojecting to WGS84...")
    wgs84_file = PROCESSED_DIR / 'wgs84.tif'
    
    cmd = [
        'gdalwarp',
        '-t_srs', 'EPSG:4326',
        '-r', 'bilinear',
        '-of', 'GTiff',
        str(input_file),
        str(wgs84_file)
    ]
    
    subprocess.run(cmd, check=True)
    
    if ctb_available:
        # Create terrain tiles
        print("\nCreating Cesium terrain tiles...")
        
        cmd = [
            'ctb-tile',
            '-f', 'Mesh',
            '-C',
            '-N',
            '-o', str(OUTPUT_DIR),
            str(wgs84_file)
        ]
        
        subprocess.run(cmd, check=True)
        
        # Create layer.json
        print("\nCreating layer.json...")
        
        cmd = [
            'ctb-tile',
            '-f', 'Mesh',
            '-l',
            '-o', str(OUTPUT_DIR),
            str(wgs84_file)
        ]
        
        subprocess.run(cmd, check=True)
        
        print("\n✅ Terrain tiles created successfully!")
    else:
        print("\n⚠️  ctb-tile not found. Please use Docker instead:")
        print(f"    docker run -v {PROCESSED_DIR}:/data tumgis/ctb-quantized-mesh \\")
        print(f"      ctb-tile -f Mesh -C -N -o /data/output /data/wgs84.tif")


def verify_output():
    """Verify the terrain tiles were created correctly."""
    
    print("\n" + "=" * 60)
    print("Verifying output")
    print("=" * 60)
    
    layer_json = OUTPUT_DIR / 'layer.json'
    
    if layer_json.exists():
        print(f"✅ layer.json exists")
        
        # Count tile directories
        tile_dirs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir()]
        print(f"✅ Found {len(tile_dirs)} zoom level directories")
        
        # Check for terrain files
        terrain_files = list(OUTPUT_DIR.rglob('*.terrain'))
        print(f"✅ Found {len(terrain_files)} terrain tiles")
        
        # Calculate total size
        total_size = sum(f.stat().st_size for f in OUTPUT_DIR.rglob('*') if f.is_file())
        print(f"✅ Total size: {total_size / (1024*1024):.1f} MB")
        
        print("\n" + "=" * 60)
        print("SUCCESS! Your terrain is ready to use.")
        print("=" * 60)
        print(f"\nStart the server with:")
        print(f"  cd {PROJECT_DIR}")
        print(f"  python -m http.server 8000")
        print(f"\nThen open http://localhost:8000")
        
        return True
    else:
        print(f"❌ layer.json not found at {layer_json}")
        return False


def main():
    """Main entry point."""
    
    print("=" * 60)
    print("BC LiDAR Terrain Processor for Cesium")
    print("=" * 60)
    
    # Check dependencies
    deps = check_dependencies()
    if not deps:
        sys.exit(1)
    
    docker_available, gdal_available, ctb_available = deps
    
    # Handle command line argument
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
        if input_path.exists():
            input_files = [input_path]
        else:
            print(f"❌ File not found: {input_path}")
            sys.exit(1)
    else:
        input_files = find_input_files()
    
    if not input_files:
        sys.exit(1)
    
    # Process based on available tools
    try:
        if docker_available:
            process_with_docker(input_files)
        else:
            process_with_local_tools(input_files, gdal_available, ctb_available)
        
        verify_output()
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Processing failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

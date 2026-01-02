# Squamish Chief Climbing Route Map

A web-based 3D visualization tool for exploring climbing routes on the Squamish Chief using CesiumJS and BC LiDAR DEM data.

**🚫 No Cesium Ion account required** - This application is fully self-hosted!

## Features

- 🗻 **3D Terrain Visualization**: High-resolution terrain rendering using BC LiDAR DEM data
- 🧗 **Climbing Route Overlay**: Interactive visualization of climbing routes with grades, lengths, and descriptions
- 📍 **Interactive Markers**: Click on routes to view detailed information
- 🎨 **Color-Coded Routes**: Routes colored by difficulty grade (5.6-5.9 to 5.13+)
- 📊 **Grade Filtering**: Filter routes by climbing grade
- 📷 **Camera Presets**: Quick navigation to popular climbing areas (Grand Wall, Apron, etc.)
- ➕ **Add Custom Routes**: Draw and save your own climbing routes
- 💾 **Data Export**: Export routes to GeoJSON format
- 🎛️ **Terrain Controls**: Adjust terrain exaggeration and visibility
- 🏠 **Self-Hosted**: All terrain data can be bundled with the site

## Quick Start

### Prerequisites

- A modern web browser (Chrome, Firefox, Safari, or Edge)
- Python 3 or Node.js (for local web server)
- Docker (for processing BC LiDAR data)

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/joelbarrette/climbing-map.git
   cd climbing-map
   ```

2. Start a local web server:
   ```bash
   # Using Python 3
   python -m http.server 8000
   
   # Or using Node.js
   npx http-server -p 8000
   ```

3. Open http://localhost:8000 in your browser

The app will work immediately with flat terrain. For 3D terrain, follow the BC LiDAR guide below.

---

## Adding BC LiDAR Terrain Data

For detailed terrain of the Squamish Chief, download and process BC LiDAR data.  
See **[BC-LIDAR-GUIDE.md](BC-LIDAR-GUIDE.md)** for complete instructions.

### Quick Overview

1. **Download BC LiDAR DEM** from [LidarBC Map Viewer](https://governmentofbc.maps.arcgis.com/apps/MapSeries/index.html?appid=d06b37979b0c4f28b9e5f81b1f855c75)
   - Navigate to Squamish Chief (49.682°N, 123.157°W)
   - Download DEM tiles in GeoTIFF format
   - Save to `data/raw/`

2. **Process the terrain**:
   ```bash
   python scripts/process_terrain.py
   ```

3. **Restart the server** - terrain will load automatically!

### Alternative: Quick Test with Maptiler

For a quick test with worldwide terrain (lower resolution):

1. Get a free API key at https://cloud.maptiler.com/account/keys/
2. Edit `terrain.js` and set your key:
   ```javascript
   maptilerKey: 'YOUR_API_KEY',
   ```

---

## Project Structure

```
climbing-map/
├── index.html              # Main HTML file
├── app.js                  # Main application logic
├── routes.js               # Climbing routes data and visualization
├── terrain.js              # Terrain loading (self-hosted)
├── styles.css              # Application styling
├── BC-LIDAR-GUIDE.md       # Detailed terrain setup guide
├── terrain-tiles/          # Your processed BC LiDAR tiles go here
│   ├── layer.json
│   └── {z}/{x}/{y}.terrain
├── data/
│   ├── raw/                # Place downloaded DEM files here
│   └── sample-routes.geojson
└── scripts/
    ├── download_bc_lidar.py   # Helper to find BC LiDAR data
    └── process_terrain.py     # Convert DEM to Cesium tiles
```

---

## Usage Guide

### Viewing Routes

- **Pan**: Left-click and drag
- **Rotate**: Right-click and drag
- **Zoom**: Scroll wheel or pinch
- **Tilt**: Middle-click and drag (or Ctrl+left-click)
- **Select Route**: Click on a route line or marker

### Adding a New Route

1. Click the "Add New Route" button
2. Fill in the route details (name, grade, length, pitches)
3. Click on the map to draw the route path
4. Right-click when finished drawing
5. Click "Save Route"

### Camera Presets

Use the preset buttons to quickly navigate to:
- **Overview**: Full view of the Squamish Chief
- **South Face**: View of the south-facing climbs
- **Grand Wall**: Focus on the Grand Wall area
- **Apron Area**: View of the Apron climbing area

### Filtering Routes

Use the grade filter checkboxes to show/hide routes by difficulty:
- 5.6-5.9 (Green)
- 5.10 (Blue)
- 5.11 (Yellow)
- 5.12 (Orange)
- 5.13+ (Red)

### Exporting Data

Routes can be exported to GeoJSON format for use in other applications:

```javascript
// In browser console
const geoJSON = exportRoutesToGeoJSON();
console.log(geoJSON);

// Or download as file
downloadRoutesGeoJSON();
```

## Sample Routes Included

The application includes several famous Squamish Chief routes:

1. **Grand Wall** (5.11, 9 pitches, 400m) - Classic multipitch
2. **Apron Strings** (5.10, 6 pitches, 350m) - Excellent moderate
3. **Split Pillar** (5.10, 5 pitches, 280m) - Popular moderate
4. **Calculus Crack** (5.12, 3 pitches, 200m) - Technical crack
5. **The Squamish Buttress** (5.6-5.9, 8 pitches, 450m) - Beginner-friendly

## Customization

### Adding More Routes

Edit `routes.js` and add to the `SAMPLE_ROUTES` array:

```javascript
{
    name: "Your Route Name",
    grade: "5.11",
    length: 300,
    pitches: 5,
    description: "Route description",
    firstAscent: "Climber Name (Year)",
    coordinates: [
        { longitude: -123.1567, latitude: 49.6815, height: 450 },
        { longitude: -123.1567, latitude: 49.6817, height: 500 },
        // ... more points
    ]
}
```

### Changing Color Scheme

Edit the `GRADE_COLORS` object in `routes.js`:

```javascript
const GRADE_COLORS = {
    '5.6-5.9': Cesium.Color.GREEN,
    '5.10': Cesium.Color.BLUE,
    '5.11': Cesium.Color.YELLOW,
    '5.12': Cesium.Color.ORANGE,
    '5.13+': Cesium.Color.RED
};
```

### Adjusting Terrain Detail

In `terrain.js`, modify:

```javascript
viewer.scene.globe.maximumScreenSpaceError = 1.0; // Lower = more detail
viewer.scene.globe.tileCacheSize = 1000; // Higher = more caching
```

## Technologies Used

- [CesiumJS](https://cesium.com/cesiumjs/) - 3D geospatial visualization
- Vanilla JavaScript - No frameworks required
- HTML5 & CSS3 - Modern web standards
- BC LiDAR Data - High-resolution terrain
- GeoJSON - Standardized geographic data format

## Data Sources

- **Terrain Data**: BC LiDAR from [LidarBC Program](https://www2.gov.bc.ca/gov/content/data/geographic-data-services/lidarbc)
- **Route Information**: Community-contributed climbing route data
- **Base Imagery**: Cesium World Imagery

## Browser Compatibility

- Chrome 90+ ✅
- Firefox 88+ ✅
- Safari 14+ ✅
- Edge 90+ ✅

## Performance Tips

- For best performance, use a dedicated GPU
- Close other GPU-intensive applications
- Reduce terrain exaggeration if experiencing lag
- Use grade filters to reduce visible routes
- Consider lowering screen resolution on slower devices

## Troubleshooting

### Map not loading
- Check browser console for errors
- Verify your Cesium Ion access token is valid
- Ensure you're serving files from a web server (not file://)

### Terrain appears flat
- Verify BC LiDAR data is properly loaded
- Check terrain provider configuration in `terrain.js`
- Try increasing terrain exaggeration

### Routes not visible
- Check that "Show Routes" is enabled
- Verify grade filters include your route's grade
- Ensure camera is zoomed in close enough
- Check browser console for JavaScript errors

## Contributing

Contributions are welcome! Please feel free to:

- Add more climbing routes
- Improve terrain processing
- Enhance the UI/UX
- Add new features (route search, statistics, etc.)
- Fix bugs and improve documentation

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Squamish climbing community for route information
- Province of British Columbia for LiDAR data
- Cesium team for the excellent 3D mapping platform

## Resources

- [Squamish Climbing Guide](https://www.squamishclimbing.com/)
- [BC Data Catalogue](https://catalogue.data.gov.bc.ca/)
- [CesiumJS Documentation](https://cesium.com/docs/)
- [Cesium Terrain Builder](https://github.com/geo-data/cesium-terrain-builder)
- [Mountain Project - Squamish](https://www.mountainproject.com/area/105907743/squamish)

## Contact

For questions or feedback, please open an issue on GitHub.

---

**Happy Climbing! 🧗‍♂️**
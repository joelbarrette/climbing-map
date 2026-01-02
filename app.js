// Main Application File
// Squamish Chief Climbing Route Viewer

// Initialize Cesium Viewer
let viewer;
let terrainProvider;
let routeEntities = [];
let isDrawing = false;
let drawingPoints = [];

// Squamish Chief coordinates (centered on BC LiDAR coverage)
const SQUAMISH_CHIEF = {
    longitude: -123.1415,
    latitude: 49.6813,
    height: 700
};

// Initialize the application
async function initApp() {
    // No Cesium Ion token required - using open source providers
    
    showLoading(true);
    
    try {
        // Get terrain provider (local BC LiDAR or fallback)
        const terrain = await createTerrainProvider();
        
        // Viewer options
        const viewerOptions = {
            // Disable default imagery (we'll add our own)
            baseLayer: false,
            baseLayerPicker: false,
            geocoder: false,
            homeButton: true,
            sceneModePicker: false,
            navigationHelpButton: false,
            animation: false,
            timeline: false,
            fullscreenButton: true,
            vrButton: false,
            infoBox: true,
            selectionIndicator: true
        };
        
        // Only add terrain if we have one
        if (terrain) {
            viewerOptions.terrainProvider = terrain;
        }
        
        // Create the Cesium Viewer
        viewer = new Cesium.Viewer('cesiumContainer', viewerOptions);
        
        // Add ESRI World Imagery (high-resolution satellite, no API key needed)
        try {
            const esriImagery = await Cesium.ArcGisMapServerImageryProvider.fromUrl(
                'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'
            );
            viewer.imageryLayers.addImageryProvider(esriImagery);
        } catch (imageryError) {
            console.warn('Failed to load ESRI imagery, falling back to OSM:', imageryError);
            // Fallback to OpenStreetMap
            viewer.imageryLayers.addImageryProvider(
                new Cesium.OpenStreetMapImageryProvider({
                    url: 'https://tile.openstreetmap.org/'
                })
            );
        }
        
        // Enhanced lighting for better cliff visualization
        viewer.scene.globe.enableLighting = true;
        viewer.scene.globe.dynamicAtmosphereLighting = true;
        viewer.scene.globe.dynamicAtmosphereLightingFromSun = true;
        
        // Improved directional light for cliffs
        viewer.scene.light = new Cesium.DirectionalLight({
            direction: new Cesium.Cartesian3(0.5, 0.5, -0.7)
        });
        
        // Configure for high-resolution terrain viewing
        viewer.scene.globe.maximumScreenSpaceError = 1.0; // Lower for sharper textures
        viewer.scene.globe.tileCacheSize = 2000; // Increased cache
        
        // Set initial camera position to Squamish Chief
        flyToSquamishChief();
        
        // Load climbing routes
        loadClimbingRoutes();
        
        // Setup event handlers
        setupEventHandlers();
        
        showLoading(false);
        
    } catch (error) {
        console.error('Error initializing application:', error);
        showLoading(false);
        alert('Error loading the map. Please check the console for details.');
    }
}

// Fly camera to Squamish Chief overview
function flyToSquamishChief() {
    viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(
            SQUAMISH_CHIEF.longitude,
            SQUAMISH_CHIEF.latitude,
            SQUAMISH_CHIEF.height + 1500
        ),
        orientation: {
            heading: Cesium.Math.toRadians(0),
            pitch: Cesium.Math.toRadians(-45),
            roll: 0.0
        },
        duration: 3
    });
}

// Setup all event handlers
function setupEventHandlers() {
    // Terrain controls
    document.getElementById('showTerrain').addEventListener('change', (e) => {
        viewer.scene.globe.show = e.target.checked;
    });
    
    document.getElementById('terrainExaggeration').addEventListener('input', (e) => {
        const value = parseFloat(e.target.value);
        viewer.scene.verticalExaggeration = value;
        document.getElementById('exaggerationValue').textContent = value.toFixed(1);
    });
    
    // Route controls
    document.getElementById('showRoutes').addEventListener('change', (e) => {
        toggleRouteVisibility(e.target.checked);
    });
    
    document.getElementById('showLabels').addEventListener('change', (e) => {
        toggleRouteLabelVisibility(e.target.checked);
    });
    
    // Grade filters
    document.querySelectorAll('.grade-filter').forEach(checkbox => {
        checkbox.addEventListener('change', filterRoutesByGrade);
    });
    
    // Camera presets
    document.getElementById('viewOverview').addEventListener('click', () => {
        flyToSquamishChief();
    });
    
    document.getElementById('viewSouthFace').addEventListener('click', () => {
        flyToLocation(SQUAMISH_CHIEF.longitude, SQUAMISH_CHIEF.latitude, 800, -60, 180);
    });
    
    document.getElementById('viewGrandWall').addEventListener('click', () => {
        flyToLocation(SQUAMISH_CHIEF.longitude - 0.002, SQUAMISH_CHIEF.latitude, 700, -70, 90);
    });
    
    document.getElementById('viewApronArea').addEventListener('click', () => {
        flyToLocation(SQUAMISH_CHIEF.longitude, SQUAMISH_CHIEF.latitude - 0.001, 600, -55, 0);
    });
    
    // Add route button
    document.getElementById('addRoute').addEventListener('click', startAddingRoute);
    document.getElementById('cancelRoute').addEventListener('click', cancelAddingRoute);
    document.getElementById('newRouteForm').addEventListener('submit', saveNewRoute);
    
    // Info panel close
    document.getElementById('closeInfo').addEventListener('click', () => {
        document.getElementById('infoPanel').classList.add('hidden');
    });
    
    // Entity selection
    viewer.selectedEntityChanged.addEventListener((entity) => {
        if (entity && entity.properties && entity.properties.routeData) {
            showRouteInfo(entity);
        }
    });
}

// Fly to a specific location
function flyToLocation(longitude, latitude, height, pitch, heading) {
    viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(longitude, latitude, height),
        orientation: {
            heading: Cesium.Math.toRadians(heading),
            pitch: Cesium.Math.toRadians(pitch),
            roll: 0.0
        },
        duration: 2
    });
}

// Toggle route visibility
function toggleRouteVisibility(show) {
    routeEntities.forEach(entity => {
        entity.show = show;
    });
}

// Toggle route label visibility
function toggleRouteLabelVisibility(show) {
    routeEntities.forEach(entity => {
        if (entity.label) {
            entity.label.show = show;
        }
    });
}

// Filter routes by grade
function filterRoutesByGrade() {
    const selectedGrades = Array.from(document.querySelectorAll('.grade-filter:checked'))
        .map(cb => cb.value);
    
    routeEntities.forEach(entity => {
        if (entity.properties && entity.properties.routeData) {
            const routeData = entity.properties.routeData.getValue();
            entity.show = selectedGrades.includes(routeData.grade);
        }
    });
}

// Show route information panel
function showRouteInfo(entity) {
    const routeData = entity.properties.routeData.getValue();
    const infoPanel = document.getElementById('infoPanel');
    
    document.getElementById('routeName').textContent = routeData.name;
    
    let detailsHTML = `
        <p><strong>Grade:</strong> ${routeData.grade}</p>
        <p><strong>Length:</strong> ${routeData.length}m</p>
        <p><strong>Pitches:</strong> ${routeData.pitches}</p>
        <p><strong>Description:</strong> ${routeData.description}</p>
    `;
    
    if (routeData.firstAscent) {
        detailsHTML += `<p><strong>First Ascent:</strong> ${routeData.firstAscent}</p>`;
    }
    
    document.getElementById('routeDetails').innerHTML = detailsHTML;
    infoPanel.classList.remove('hidden');
}

// Start adding a new route
function startAddingRoute() {
    document.getElementById('addRouteForm').classList.remove('hidden');
    document.getElementById('controlPanel').classList.add('minimized');
    isDrawing = true;
    drawingPoints = [];
    
    // Add click handler for drawing
    viewer.screenSpaceEventHandler.setInputAction((click) => {
        if (!isDrawing) return;
        
        const cartesian = viewer.camera.pickEllipsoid(click.position, viewer.scene.globe.ellipsoid);
        if (cartesian) {
            drawingPoints.push(cartesian);
            
            // Add a point entity
            viewer.entities.add({
                position: cartesian,
                point: {
                    pixelSize: 8,
                    color: Cesium.Color.YELLOW,
                    outlineColor: Cesium.Color.BLACK,
                    outlineWidth: 2
                }
            });
            
            // Draw line if we have at least 2 points
            if (drawingPoints.length > 1) {
                viewer.entities.add({
                    polyline: {
                        positions: [drawingPoints[drawingPoints.length - 2], drawingPoints[drawingPoints.length - 1]],
                        width: 3,
                        material: Cesium.Color.YELLOW
                    }
                });
            }
        }
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
    
    // Right-click to finish
    viewer.screenSpaceEventHandler.setInputAction(() => {
        if (isDrawing && drawingPoints.length > 1) {
            // Route drawing completed
            alert('Route path completed. Fill in the details and click Save.');
        }
    }, Cesium.ScreenSpaceEventType.RIGHT_CLICK);
}

// Cancel adding a route
function cancelAddingRoute() {
    isDrawing = false;
    drawingPoints = [];
    document.getElementById('addRouteForm').classList.add('hidden');
    document.getElementById('controlPanel').classList.remove('minimized');
    
    // Remove temporary drawing entities
    const entitiesToRemove = [];
    viewer.entities.values.forEach(entity => {
        if (entity.point && entity.point.color.getValue().equals(Cesium.Color.YELLOW)) {
            entitiesToRemove.push(entity);
        }
    });
    entitiesToRemove.forEach(entity => viewer.entities.remove(entity));
    
    // Reset form
    document.getElementById('newRouteForm').reset();
}

// Save new route
function saveNewRoute(e) {
    e.preventDefault();
    
    if (drawingPoints.length < 2) {
        alert('Please draw a route path on the map first.');
        return;
    }
    
    const formData = new FormData(e.target);
    const routeData = {
        name: formData.get('name'),
        grade: formData.get('grade'),
        length: parseInt(formData.get('length')) || 0,
        pitches: parseInt(formData.get('pitches')) || 1,
        description: formData.get('description') || '',
        coordinates: drawingPoints.map(point => {
            const cartographic = Cesium.Cartographic.fromCartesian(point);
            return {
                longitude: Cesium.Math.toDegrees(cartographic.longitude),
                latitude: Cesium.Math.toDegrees(cartographic.latitude),
                height: cartographic.height
            };
        })
    };
    
    // Add the route to the map
    addRouteToMap(routeData);
    
    // Save to local storage
    saveRouteToStorage(routeData);
    
    // Clean up
    cancelAddingRoute();
    
    alert('Route saved successfully!');
}

// Show/hide loading indicator
function showLoading(show) {
    const indicator = document.getElementById('loadingIndicator');
    if (show) {
        indicator.classList.remove('hidden');
    } else {
        indicator.classList.add('hidden');
    }
}

// Save route to local storage
function saveRouteToStorage(routeData) {
    const routes = JSON.parse(localStorage.getItem('climbingRoutes') || '[]');
    routes.push(routeData);
    localStorage.setItem('climbingRoutes', JSON.stringify(routes));
}

// Load routes from local storage
function loadRoutesFromStorage() {
    const routes = JSON.parse(localStorage.getItem('climbingRoutes') || '[]');
    routes.forEach(route => addRouteToMap(route));
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', initApp);

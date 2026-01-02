// Climbing Routes Data and Visualization Module
// Manages climbing routes overlay on the 3D terrain

/**
 * Sample climbing routes data for Squamish Chief
 * This includes some famous routes - replace with actual route data
 */
const SAMPLE_ROUTES = [
    {
        name: "Grand Wall",
        grade: "5.11",
        length: 400,
        pitches: 9,
        description: "A classic Squamish multipitch route on excellent granite. The Grand Wall is one of the most sought-after climbs in North America.",
        firstAscent: "Jim Baldwin & Ed Cooper (1961)",
        coordinates: [
            { longitude: -123.1567, latitude: 49.6815, height: 450 },
            { longitude: -123.1567, latitude: 49.6817, height: 500 },
            { longitude: -123.1566, latitude: 49.6819, height: 550 },
            { longitude: -123.1565, latitude: 49.6821, height: 600 },
            { longitude: -123.1565, latitude: 49.6823, height: 650 },
            { longitude: -123.1564, latitude: 49.6825, height: 700 }
        ]
    },
    {
        name: "Apron Strings",
        grade: "5.10",
        length: 350,
        pitches: 6,
        description: "An excellent moderate climb on the Apron. Great exposure and varied climbing.",
        firstAscent: "Unknown",
        coordinates: [
            { longitude: -123.1570, latitude: 49.6810, height: 400 },
            { longitude: -123.1569, latitude: 49.6812, height: 450 },
            { longitude: -123.1568, latitude: 49.6814, height: 500 },
            { longitude: -123.1567, latitude: 49.6816, height: 550 },
            { longitude: -123.1566, latitude: 49.6818, height: 600 }
        ]
    },
    {
        name: "Split Pillar",
        grade: "5.10",
        length: 280,
        pitches: 5,
        description: "A popular moderate route with spectacular position. Follows a prominent pillar feature.",
        coordinates: [
            { longitude: -123.1565, latitude: 49.6812, height: 420 },
            { longitude: -123.1564, latitude: 49.6814, height: 480 },
            { longitude: -123.1564, latitude: 49.6816, height: 540 },
            { longitude: -123.1563, latitude: 49.6818, height: 600 },
            { longitude: -123.1562, latitude: 49.6820, height: 650 }
        ]
    },
    {
        name: "Calculus Crack",
        grade: "5.12",
        length: 200,
        pitches: 3,
        description: "A challenging finger and hand crack. Technical and sustained climbing.",
        coordinates: [
            { longitude: -123.1572, latitude: 49.6818, height: 500 },
            { longitude: -123.1571, latitude: 49.6820, height: 560 },
            { longitude: -123.1570, latitude: 49.6822, height: 620 }
        ]
    },
    {
        name: "The Squamish Buttress",
        grade: "5.6-5.9",
        length: 450,
        pitches: 8,
        description: "A perfect beginner multipitch route. Excellent rock and beautiful views.",
        coordinates: [
            { longitude: -123.1568, latitude: 49.6808, height: 380 },
            { longitude: -123.1567, latitude: 49.6810, height: 430 },
            { longitude: -123.1567, latitude: 49.6812, height: 480 },
            { longitude: -123.1566, latitude: 49.6814, height: 530 },
            { longitude: -123.1566, latitude: 49.6816, height: 580 },
            { longitude: -123.1565, latitude: 49.6818, height: 630 }
        ]
    }
];

/**
 * Color scheme for different climbing grades
 */
const GRADE_COLORS = {
    '5.6-5.9': Cesium.Color.GREEN,
    '5.10': Cesium.Color.BLUE,
    '5.11': Cesium.Color.YELLOW,
    '5.12': Cesium.Color.ORANGE,
    '5.13+': Cesium.Color.RED
};

/**
 * Load all climbing routes onto the map
 */
function loadClimbingRoutes() {
    // Load sample routes
    SAMPLE_ROUTES.forEach(route => addRouteToMap(route));
    
    // Load user-created routes from local storage
    loadRoutesFromStorage();
    
    console.log(`Loaded ${routeEntities.length} climbing routes`);
}

/**
 * Add a single climbing route to the map
 */
function addRouteToMap(routeData) {
    if (!routeData.coordinates || routeData.coordinates.length < 2) {
        console.error('Invalid route data: missing coordinates');
        return;
    }
    
    // Convert coordinates to Cesium Cartesian3 positions
    const positions = routeData.coordinates.map(coord => 
        Cesium.Cartesian3.fromDegrees(coord.longitude, coord.latitude, coord.height)
    );
    
    // Get color based on grade
    const color = GRADE_COLORS[routeData.grade] || Cesium.Color.WHITE;
    
    // Create the route line
    const routeLine = viewer.entities.add({
        name: routeData.name,
        polyline: {
            positions: positions,
            width: 5,
            material: new Cesium.PolylineOutlineMaterialProperty({
                color: color,
                outlineWidth: 2,
                outlineColor: Cesium.Color.BLACK
            }),
            clampToGround: false,
            arcType: Cesium.ArcType.NONE
        },
        properties: {
            routeData: routeData
        }
    });
    
    // Add start point marker
    const startPosition = positions[0];
    const startMarker = viewer.entities.add({
        name: `${routeData.name} - Start`,
        position: startPosition,
        point: {
            pixelSize: 12,
            color: color,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2
        },
        label: {
            text: routeData.name,
            font: '14px sans-serif',
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -15),
            distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 5000)
        },
        properties: {
            routeData: routeData
        }
    });
    
    // Add end point marker
    const endPosition = positions[positions.length - 1];
    const endMarker = viewer.entities.add({
        name: `${routeData.name} - Summit`,
        position: endPosition,
        billboard: {
            image: createSummitIcon(color),
            width: 24,
            height: 24,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM
        },
        properties: {
            routeData: routeData
        }
    });
    
    // Store references to all route entities
    routeEntities.push(routeLine, startMarker, endMarker);
    
    // Add pitch markers if route has multiple pitches
    if (routeData.pitches > 1 && positions.length > 2) {
        addPitchMarkers(routeData, positions);
    }
}

/**
 * Add markers for individual pitches along the route
 */
function addPitchMarkers(routeData, positions) {
    const pitchInterval = Math.floor(positions.length / routeData.pitches);
    
    for (let i = 1; i < routeData.pitches; i++) {
        const index = Math.min(i * pitchInterval, positions.length - 1);
        const position = positions[index];
        
        const pitchMarker = viewer.entities.add({
            name: `${routeData.name} - Pitch ${i}`,
            position: position,
            point: {
                pixelSize: 8,
                color: Cesium.Color.WHITE,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 1
            },
            label: {
                text: `P${i}`,
                font: '10px sans-serif',
                fillColor: Cesium.Color.WHITE,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 1,
                style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                pixelOffset: new Cesium.Cartesian2(10, 0),
                distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 2000)
            },
            properties: {
                routeData: routeData,
                pitchNumber: i
            }
        });
        
        routeEntities.push(pitchMarker);
    }
}

/**
 * Create a canvas-based summit icon
 */
function createSummitIcon(color) {
    const canvas = document.createElement('canvas');
    canvas.width = 24;
    canvas.height = 24;
    const ctx = canvas.getContext('2d');
    
    // Draw triangle (mountain peak)
    ctx.beginPath();
    ctx.moveTo(12, 2);
    ctx.lineTo(22, 22);
    ctx.lineTo(2, 22);
    ctx.closePath();
    
    // Fill with color
    ctx.fillStyle = color.toCssColorString();
    ctx.fill();
    
    // Black outline
    ctx.strokeStyle = 'black';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    return canvas;
}

/**
 * Remove all routes from the map
 */
function clearAllRoutes() {
    routeEntities.forEach(entity => {
        viewer.entities.remove(entity);
    });
    routeEntities = [];
}

/**
 * Export routes to GeoJSON format
 */
function exportRoutesToGeoJSON() {
    const features = [];
    
    routeEntities.forEach(entity => {
        if (entity.polyline && entity.properties && entity.properties.routeData) {
            const routeData = entity.properties.routeData.getValue();
            
            const coordinates = routeData.coordinates.map(coord => [
                coord.longitude,
                coord.latitude,
                coord.height
            ]);
            
            features.push({
                type: 'Feature',
                geometry: {
                    type: 'LineString',
                    coordinates: coordinates
                },
                properties: {
                    name: routeData.name,
                    grade: routeData.grade,
                    length: routeData.length,
                    pitches: routeData.pitches,
                    description: routeData.description,
                    firstAscent: routeData.firstAscent
                }
            });
        }
    });
    
    const geoJSON = {
        type: 'FeatureCollection',
        features: features
    };
    
    return JSON.stringify(geoJSON, null, 2);
}

/**
 * Import routes from GeoJSON
 */
function importRoutesFromGeoJSON(geoJSONString) {
    try {
        const geoJSON = JSON.parse(geoJSONString);
        
        if (geoJSON.type !== 'FeatureCollection') {
            throw new Error('Invalid GeoJSON: expected FeatureCollection');
        }
        
        geoJSON.features.forEach(feature => {
            if (feature.geometry.type === 'LineString') {
                const routeData = {
                    name: feature.properties.name || 'Unnamed Route',
                    grade: feature.properties.grade || '5.10',
                    length: feature.properties.length || 0,
                    pitches: feature.properties.pitches || 1,
                    description: feature.properties.description || '',
                    firstAscent: feature.properties.firstAscent || '',
                    coordinates: feature.geometry.coordinates.map(coord => ({
                        longitude: coord[0],
                        latitude: coord[1],
                        height: coord[2] || 0
                    }))
                };
                
                addRouteToMap(routeData);
                saveRouteToStorage(routeData);
            }
        });
        
        console.log(`Imported ${geoJSON.features.length} routes`);
        
    } catch (error) {
        console.error('Error importing GeoJSON:', error);
        alert('Failed to import routes. Please check the GeoJSON format.');
    }
}

/**
 * Download routes as GeoJSON file
 */
function downloadRoutesGeoJSON() {
    const geoJSON = exportRoutesToGeoJSON();
    const blob = new Blob([geoJSON], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = 'squamish-chief-routes.geojson';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Calculate route statistics
 */
function calculateRouteStatistics() {
    const stats = {
        totalRoutes: 0,
        byGrade: {},
        totalLength: 0,
        totalPitches: 0,
        averageLength: 0
    };
    
    routeEntities.forEach(entity => {
        if (entity.polyline && entity.properties && entity.properties.routeData) {
            const routeData = entity.properties.routeData.getValue();
            
            stats.totalRoutes++;
            stats.totalLength += routeData.length || 0;
            stats.totalPitches += routeData.pitches || 0;
            
            const grade = routeData.grade;
            stats.byGrade[grade] = (stats.byGrade[grade] || 0) + 1;
        }
    });
    
    stats.averageLength = stats.totalRoutes > 0 ? 
        Math.round(stats.totalLength / stats.totalRoutes) : 0;
    
    return stats;
}

/**
 * Find routes by name
 */
function findRouteByName(searchTerm) {
    const term = searchTerm.toLowerCase();
    const matches = [];
    
    routeEntities.forEach(entity => {
        if (entity.properties && entity.properties.routeData) {
            const routeData = entity.properties.routeData.getValue();
            if (routeData.name.toLowerCase().includes(term)) {
                matches.push({
                    entity: entity,
                    data: routeData
                });
            }
        }
    });
    
    return matches;
}

/**
 * Fly to a specific route
 */
function flyToRoute(routeName) {
    const matches = findRouteByName(routeName);
    
    if (matches.length > 0) {
        const route = matches[0];
        const coords = route.data.coordinates[0];
        
        viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(
                coords.longitude,
                coords.latitude,
                coords.height + 200
            ),
            orientation: {
                heading: Cesium.Math.toRadians(0),
                pitch: Cesium.Math.toRadians(-60),
                roll: 0.0
            },
            duration: 2
        });
        
        // Select the route entity
        viewer.selectedEntity = route.entity;
    } else {
        console.warn(`Route not found: ${routeName}`);
    }
}

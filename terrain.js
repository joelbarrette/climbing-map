// Terrain Configuration Module
// Self-hosted BC LiDAR terrain - NO Cesium Ion required

/**
 * Configuration for terrain sources
 * Priority: Local BC LiDAR > Maptiler > Flat terrain
 */
const TERRAIN_CONFIG = {
    // Path to locally hosted quantized-mesh terrain tiles
    localTerrainPath: './terrain-tiles',
    
    // Maptiler free tier API key (optional fallback)
    // Get one at https://cloud.maptiler.com/account/keys/
    maptilerKey: null,
    
    // Squamish Chief area bounds
    bounds: {
        west: -123.20,
        south: 49.65,
        east: -123.10,
        north: 49.72
    }
};

/**
 * Create the terrain provider
 * Tries local BC LiDAR first, falls back to alternatives
 */
async function createTerrainProvider() {
    // Try local BC LiDAR terrain first
    try {
        const localTerrain = await tryLocalTerrain();
        if (localTerrain) {
            console.log('✅ Using local BC LiDAR terrain');
            return localTerrain;
        }
    } catch (e) {
        console.log('Local terrain not available:', e.message);
    }
    
    // Try Maptiler terrain (free tier available)
    if (TERRAIN_CONFIG.maptilerKey) {
        try {
            const maptilerTerrain = await Cesium.CesiumTerrainProvider.fromUrl(
                `https://api.maptiler.com/tiles/terrain-quantized-mesh/?key=${TERRAIN_CONFIG.maptilerKey}`,
                { requestVertexNormals: true }
            );
            console.log('✅ Using Maptiler terrain');
            return maptilerTerrain;
        } catch (e) {
            console.log('Maptiler terrain not available:', e.message);
        }
    }
    
    // Fall back to ellipsoid (flat) terrain
    console.log('⚠️ Using flat terrain - follow BC-LIDAR-GUIDE.md to add terrain');
    return undefined;
}

/**
 * Try to load locally hosted terrain tiles
 */
async function tryLocalTerrain() {
    const testUrl = `${TERRAIN_CONFIG.localTerrainPath}/layer.json`;
    
    const response = await fetch(testUrl);
    if (!response.ok) {
        throw new Error('Local terrain tiles not found at ' + testUrl);
    }
    
    // Parse layer.json to verify it's valid
    const layerJson = await response.json();
    console.log('Found local terrain:', layerJson.name);
    console.log('Terrain bounds:', layerJson.bounds);
    
    // Use CesiumTerrainProvider with skipLevelZero to avoid errors on small areas
    const provider = await Cesium.CesiumTerrainProvider.fromUrl(
        TERRAIN_CONFIG.localTerrainPath,
        {
            requestVertexNormals: true,
            requestWaterMask: false,
            credit: new Cesium.Credit('BC LiDAR Program')
        }
    );
    
    return provider;
}

/**
 * Set terrain exaggeration for better cliff visualization
 */
function setTerrainExaggeration(factor) {
    if (viewer && viewer.scene) {
        viewer.scene.verticalExaggeration = factor;
    }
}

/**
 * Configure viewer for optimal terrain viewing
 */
function configureTerrainViewing() {
    if (!viewer || !viewer.scene) return;
    
    viewer.scene.globe.maximumScreenSpaceError = 1.0;
    viewer.scene.globe.tileCacheSize = 1000;
    viewer.scene.globe.enableLighting = true;
    viewer.scene.globe.depthTestAgainstTerrain = true;
    viewer.scene.fog.enabled = true;
    viewer.scene.fog.density = 0.0001;
}

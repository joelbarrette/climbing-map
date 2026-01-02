# Squamish Chief Climbing Routes - GeoJSON Data

This directory contains GeoJSON files for climbing routes.

## Format

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [longitude, latitude, height],
          ...
        ]
      },
      "properties": {
        "name": "Route Name",
        "grade": "5.11",
        "length": 400,
        "pitches": 9,
        "description": "Route description",
        "firstAscent": "Climber Name (Year)"
      }
    }
  ]
}
```

## Adding Routes

1. Create or edit a `.geojson` file in this directory
2. Follow the format above
3. Coordinates should be in [longitude, latitude, height] format
4. Height is in meters above sea level

## Importing

To import routes into the application:

```javascript
// Load GeoJSON file
fetch('data/routes.geojson')
  .then(response => response.json())
  .then(geoJSON => {
    importRoutesFromGeoJSON(JSON.stringify(geoJSON));
  });
```

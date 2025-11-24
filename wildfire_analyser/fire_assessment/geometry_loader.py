import json
import ee
from pathlib import Path

class GeometryLoader:
    @staticmethod
    def load_geojson(path: str) -> ee.Geometry:
        """Load a GeoJSON file and return an Earth Engine Geometry."""
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"GeoJSON not found: {path}")

        with open(file_path, 'r') as f:
            geojson = json.load(f)

        # Converts GeoJSON to EE geometry
        geometry = ee.Geometry(geojson['features'][0]['geometry'])
        return geometry

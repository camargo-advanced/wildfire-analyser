# assessment_runner.py
from src.gee_authenticator import GEEAuthenticator
from src.geometry_loader import GeometryLoader
import ee


class AssessmentRunner:
    def __init__(self, gee_client: GEEAuthenticator, roi: ee.Geometry):
        """
        Receives an initialized GEEAuthenticator and a Region of Interest (ROI).
        """
        self.gee = gee_client.ee
        self.roi = roi

    def run_analysis(self):
        """
        Example analysis: Sentinel-2 filtered by date AND spatial ROI.
        """
        collection = self.gee.ImageCollection("COPERNICUS/S2") \
                             .filterDate("2025-01-01", "2025-01-31") \
                             .filterBounds(self.roi)

        print("Analysis running with ROI:")
        print(self.roi.getInfo())

        print(f"Number of images intersecting ROI: {collection.size().getInfo()}")


# Main execution block
if __name__ == "__main__":
    import logging
    import os

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    try:
        # Initialize GEE
        gee_client = GEEAuthenticator()

        # Load ROI from GeoJSON
        geojson_path = os.path.join("polygons", "eejatai.geojson")
        roi = GeometryLoader.load_geojson(geojson_path)

        # Pass ROI to the runner
        runner = AssessmentRunner(gee_client, roi)

        runner.run_analysis()

    except Exception as e:
        logging.exception("Unexpected error during processing")

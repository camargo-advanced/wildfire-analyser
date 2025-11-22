# assessment_runner.py
import logging
logger = logging.getLogger(__name__)

from src.gee_authenticator import GEEAuthenticator
from src.geometry_loader import GeometryLoader
from datetime import datetime, timedelta
import ee


class AssessmentRunner:
    def __init__(self, gee_client: GEEAuthenticator, roi: ee.Geometry):
        """
        Receives an initialized GEEAuthenticator and a Region of Interest (ROI).
        """
        self.gee = gee_client.ee
        self.roi = roi

    def get_best_images(self, start_date: str, end_date: str):

        base_collection = self.gee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                                .filterBounds(self.roi)

        before_image = None
        after_image = None

        sd = datetime.strptime(start_date, "%Y-%m-%d")
        ed = datetime.strptime(end_date, "%Y-%m-%d")

        before_start = (sd - timedelta(days=30)).strftime("%Y-%m-%d")
        before_end   = start_date

        after_start  = end_date
        after_end    = (ed + timedelta(days=30)).strftime("%Y-%m-%d")

        cloud_threshold = 5

        while cloud_threshold <= 100 and (before_image is None or after_image is None):

            logger.info(f"Trying cloud threshold: {cloud_threshold}%")

            filtered = base_collection.filterMetadata(
                "CLOUDY_PIXEL_PERCENTAGE",
                "less_than",
                cloud_threshold
            )

            # BEFORE IMAGE
            if before_image is None:
                candidate = filtered \
                    .filterDate(before_start, before_end) \
                    .sort("system:time_start", False) \
                    .first()

                # Only query metadata if image exists
                if candidate is not None and candidate.getInfo():
                    before_image = candidate

                    date = before_image.date().format("YYYY-MM-dd").getInfo()
                    img_id = before_image.get("system:index").getInfo()

                    logger.info(f"[BEFORE] Selected {date} | ID: {img_id} | Clouds: {cloud_threshold}%")

            # AFTER IMAGE
            if after_image is None:
                candidate = filtered \
                    .filterDate(after_start, after_end) \
                    .sort("system:time_start", True) \
                    .first()

                if candidate is not None and candidate.getInfo():
                    after_image = candidate

                    date = after_image.date().format("YYYY-MM-dd").getInfo()
                    img_id = after_image.get("system:index").getInfo()

                    logger.info(f"[AFTER] Selected {date} | ID: {img_id} | Clouds: {cloud_threshold}%")

            cloud_threshold += 5

        # Final result warning if missing
        if before_image is None or after_image is None:
            logger.warning("Could not find both images within constraints.")

        return before_image, after_image



    def run_analysis(self, start_date: str, end_date: str):
        pre_event_image, post_event_image = self.get_best_images(start_date, end_date)

# Main execution block
if __name__ == "__main__":
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

        # Define date parameters here
        start = "2025-01-01"
        end = "2025-01-31"

        runner.run_analysis(start, end)

    except Exception as e:
        logger.exception("Unexpected error during processing")


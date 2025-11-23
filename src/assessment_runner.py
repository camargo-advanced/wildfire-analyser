# assessment_runner.py
import logging
from datetime import datetime, timedelta
import ee

from src.gee_authenticator import GEEAuthenticator
from src.geometry_loader import GeometryLoader

logger = logging.getLogger(__name__)
DAYS_BEFORE_AFTER = 45
CLOUD_THRESHOLD = 50
COLLECTION_ID = "COPERNICUS/S2_SR_HARMONIZED"


class AssessmentRunner:
    def __init__(self, gee_client: GEEAuthenticator, roi: ee.Geometry):
        """
        Receives an initialized GEEAuthenticator and a Region of Interest (ROI).
        """
        self.gee = gee_client.ee
        self.roi = roi

    def _expand_dates(self, start_date: str, end_date: str):
        sd = datetime.strptime(start_date, "%Y-%m-%d")
        ed = datetime.strptime(end_date, "%Y-%m-%d")
        before_start = (sd - timedelta(days=DAYS_BEFORE_AFTER)).strftime("%Y-%m-%d")
        after_end = (ed + timedelta(days=DAYS_BEFORE_AFTER)).strftime("%Y-%m-%d")
        return before_start, start_date, end_date, after_end

    def _load_collection(self, start: str, end: str):
        """Load all images intersecting ROI within date range and under cloud threshold."""
        return (self.gee.ImageCollection(COLLECTION_ID)
                .filterBounds(self.roi)
                .filterDate(start, end)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', CLOUD_THRESHOLD))
                .sort('CLOUDY_PIXEL_PERCENTAGE'))

    def _mask_clouds(self, image: ee.Image):
        """Mask clouds using QA60 band (Sentinel-2 SR)."""
        qa = image.select('QA60')
        cloud_mask = qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0))
        return image.updateMask(cloud_mask)

    def _build_mosaic(self, collection: ee.ImageCollection):
        """Generate mosaic and return IDs of images used."""
        size = collection.size().getInfo()
        if size == 0:
            logger.warning("No images in collection to build mosaic.")
            return None, []

        images_list = collection.toList(size)
        images = [ee.Image(images_list.get(i)) for i in range(size)]
        masked_images = [self._mask_clouds(img) for img in images]
        mosaic = ee.ImageCollection(masked_images).mosaic()
        image_ids = [img.get('system:index').getInfo() for img in images]
        return mosaic, image_ids

    def run_analysis(self, start_date: str, end_date: str):
        before_start, before_end, after_start, after_end = self._expand_dates(start_date, end_date)

        logger.info(f"Building BEFORE mosaic: {before_start} → {before_end}")
        before_col = self._load_collection(before_start, before_end)
        before_mosaic, before_ids = self._build_mosaic(before_col)

        logger.info(f"Building AFTER mosaic: {after_start} → {after_end}")
        after_col = self._load_collection(after_start, after_end)
        after_mosaic, after_ids = self._build_mosaic(after_col)

        return {
            "before": {"mosaic": before_mosaic, "image_ids": before_ids},
            "after": {"mosaic": after_mosaic, "image_ids": after_ids}
        }


# Main execution block
if __name__ == "__main__":
    import os
    import json

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    try:
        # Initialize GEE via Authenticator
        gee_client = GEEAuthenticator()

        # Load ROI from GeoJSON
        geojson_path = os.path.join("polygons", "eejatai.geojson")
        roi = GeometryLoader.load_geojson(geojson_path)

        # Run assessment
        runner = AssessmentRunner(gee_client, roi)
        result = runner.run_analysis("2025-01-01", "2025-01-31")

        logger.info("BEFORE image IDs: %s", result['before']['image_ids'])
        logger.info("AFTER image IDs: %s", result['after']['image_ids'])

    except Exception as e:
        logger.exception("Unexpected error during processing")

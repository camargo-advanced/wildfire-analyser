# mosaic_selector.py
import ee
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MosaicSelector:
    def __init__(self, collection_id: str, roi: ee.Geometry, min_geo_coverage: float = 97):
        """
        collection_id: e.g. 'COPERNICUS/S2_SR_HARMONIZED'
        roi: ee.Geometry polygon
        min_geo_coverage: coverage threshold in percentage (0-100)
        """
        self.collection = ee.ImageCollection(collection_id)
        self.roi = roi
        self.min_geo_coverage = min_geo_coverage

    def _get_collection(self, start: str, end: str, cloud_limit: float):
        """Returns all images intersecting ROI and under cloud limit."""
        col = (self.collection
               .filterDate(start, end)
               .filterBounds(self.roi)
               .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_limit)))
        return col

    def _coverage_percent(self, mosaic: ee.Image) -> float:
        """Estimates % of ROI that has valid (non-masked) pixels."""
        roi_area = self.roi.area().getInfo()

        # convert mask to 1 (valid) / 0 (invalid)
        mask = mosaic.mask().reduce(ee.Reducer.min())
        try:
            valid_area = mask.multiply(ee.Image.pixelArea()) \
                            .reduceRegion(
                                reducer=ee.Reducer.sum(),
                                geometry=self.roi,
                                scale=20,
                                maxPixels=1e13
                            ).getInfo()

            # Segurança para lidar com None ou lista em vez de dict
            if valid_area is None:
                valid_area_val = 0
            elif isinstance(valid_area, dict):
                valid_area_val = list(valid_area.values())[0]
            elif isinstance(valid_area, (list, tuple)):
                valid_area_val = valid_area[0]
            else:
                valid_area_val = float(valid_area)

        except Exception as e:
            logger.warning(f"Error computing coverage: {e}")
            valid_area_val = 0

        return (valid_area_val / roi_area) * 100


    def has_sufficient_cover(self, mosaic: ee.Image) -> bool:
        """Checks if mosaic meets the minimum coverage threshold."""
        if mosaic is None or mosaic.bandNames().size().getInfo() == 0:
            return False

        coverage_percent = self._coverage_percent(mosaic)
        return coverage_percent >= self.min_geo_coverage

    def filter_by_clouds(self, collection: ee.ImageCollection, cloud_limit: float):
        """Filters an ImageCollection by cloud percentage."""
        return collection.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_limit))

    def build_mosaic(self, start: str, end: str, cloud_limit: float):
        """Builds a mosaic from all images in the period and returns it with coverage %."""
        try:
            collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                            .filterBounds(self.roi) \
                            .filterDate(start, end)
            if collection.size().getInfo() == 0:
                logger.warning(f"No images found for period {start} to {end}. Skipping.")
                return None, 0

            collection = self.filter_by_clouds(collection, cloud_limit)
            if collection.size().getInfo() == 0:
                logger.warning(f"No images left after cloud filter for period {start} to {end}.")
                return None, 0

            mosaic = collection.mosaic()
            coverage_percent = self._coverage_percent(mosaic)

            return mosaic, coverage_percent
        except ee.EEException as e:
            logger.warning(f"Error building mosaic for {start} to {end}: {e}")
            return None, 0

    def find_valid_mosaic(self, target_date: str):
        """
        Finds a mosaic with:
        - ≥ min_geo_coverage coverage
        - cloud limit escalating 5% → 50%
        - max ±30 days expansion around target_date
        """
        base_date = datetime.strptime(target_date, "%Y-%m-%d")
        max_shift = 30  # days
        cloud_limit = 5

        while cloud_limit <= 50:
            logger.info(f"🔎 Trying cloud limit: {cloud_limit}%")
            for shift in range(0, max_shift + 1, 5):
                start = (base_date - timedelta(days=shift)).strftime("%Y-%m-%d")
                end   = (base_date + timedelta(days=shift)).strftime("%Y-%m-%d")

                mosaic, coverage = self.build_mosaic(start, end, cloud_limit)
                if mosaic and coverage >= self.min_geo_coverage:
                    logger.info(f"✅ Valid mosaic found! {coverage:.2f}% coverage")
                    return mosaic

            cloud_limit += 5

        logger.warning("❌ No valid mosaic found.")
        return None

# post_fire_assessment.py
import logging
import requests
from datetime import datetime, timedelta
import ee
from rasterio.io import MemoryFile

from wildfire_analyser.fire_assessment.gee_client import GEEClient
from wildfire_analyser.fire_assessment.geometry_loader import GeometryLoader

logger = logging.getLogger(__name__)

DAYS_BEFORE_AFTER = 30
CLOUD_THRESHOLD = 100
COLLECTION_ID = "COPERNICUS/S2_SR_HARMONIZED"


class PostFireAssessment:
    def __init__(self, geojson_path: str, start_date: str, end_date: str):
        """
        Receives an initialized GEEClient and a Region of Interest (ROI).
        """
        self.gee = GEEClient().ee
        logger.info("Connected to GEE")
        self.roi = GeometryLoader.load_geojson(geojson_path)
        self.start_date = start_date

        self.end_date = end_date

    def _download_geotiff_bytes(self, image: ee.Image, scale: int = 10):
        url = image.getDownloadURL({
            "scale": scale,
            "region": self.roi,
            "format": "GEO_TIFF"
        })

        response = requests.get(url)
        response.raise_for_status()

        return response.content  # ← binário TIFF

    def _expand_dates(self, start_date: str, end_date: str):
        sd = datetime.strptime(start_date, "%Y-%m-%d")
        ed = datetime.strptime(end_date, "%Y-%m-%d")
        before_start = (sd - timedelta(days=DAYS_BEFORE_AFTER)).strftime("%Y-%m-%d")
        after_end = (ed + timedelta(days=DAYS_BEFORE_AFTER)).strftime("%Y-%m-%d")
        return before_start, start_date, end_date, after_end

    def _load_full_collection(self):
        """Load all images intersecting ROI under cloud threshold, mask clouds, select bands, add reflectance."""
        bands_to_select = ['B2', 'B3', 'B4', 'B8', 'B12', 'QA60']
        
        collection = (
            self.gee.ImageCollection(COLLECTION_ID)
            .filterBounds(self.roi)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', CLOUD_THRESHOLD))
            .sort('CLOUDY_PIXEL_PERCENTAGE', False)
            .select(bands_to_select)
        )
        
        # Função para adicionar reflectância (_refl) e máscara de nuvens
        def preprocess(img):
            refl_bands = img.select('B.*').multiply(0.0001)
            refl_names = refl_bands.bandNames().map(lambda b: ee.String(b).cat('_refl'))
            img = img.addBands(refl_bands.rename(refl_names))

            return img
        
        collection = collection.map(preprocess)

        return collection

    def _ensure_not_empty(self, collection, label, start, end):
        try:
            size_val = collection.size().getInfo()
        except Exception:
            size_val = 0

        if size_val == 0:
            raise ValueError(f"No images found for {label}: {start} → {end}")
        
    def _download_single_band(self, image, band_name):
        single_band = image.select([band_name])
        return self._download_geotiff_bytes(single_band)

    def _merge_bands(self, band_bytes_list):
        memfiles = [MemoryFile(b) for b in band_bytes_list]
        datasets = [m.open() for m in memfiles]

        profile = datasets[0].profile
        profile.update(count=len(datasets))

        with MemoryFile() as mem_out:
            with mem_out.open(**profile) as dst:
                for idx, ds in enumerate(datasets, start=1):
                    dst.write(ds.read(1), idx)

            return mem_out.read()

    def _generate_rgb_pre_fire(self, before_mosaic):
        """Gera RGB (B4,B3,B2) como um único GeoTIFF multibanda."""
        rgb_image = before_mosaic.select([
            'B4_refl',  # Red
            'B3_refl',  # Green
            'B2_refl'   # Blue
        ])

        # Baixa cada banda separadamente
        b4 = self._download_single_band(rgb_image, 'B4_refl')
        b3 = self._download_single_band(rgb_image, 'B3_refl')
        b2 = self._download_single_band(rgb_image, 'B2_refl')

        # Junta num único TIFF multibanda
        rgb_bytes = self._merge_bands([b4, b3, b2])

        return {
            "filename": "rgb_pre_fire_index.tif",
            "content_type": "image/tiff",
            "data": rgb_bytes
        }

    def _generate_rgb_post_fire(self, after_mosaic):
        """Gera RGB pós-fogo (B4,B3,B2) como um único GeoTIFF multibanda."""
        rgb_image = after_mosaic.select([
            'B4_refl',  # Red
            'B3_refl',  # Green
            'B2_refl'   # Blue
        ])

        # Baixa cada banda separadamente
        b4 = self._download_single_band(rgb_image, 'B4_refl')
        b3 = self._download_single_band(rgb_image, 'B3_refl')
        b2 = self._download_single_band(rgb_image, 'B2_refl')

        # Junta num único TIFF multibanda
        rgb_bytes = self._merge_bands([b4, b3, b2])

        return {
            "filename": "rgb_post_fire_index.tif",
            "content_type": "image/tiff",
            "data": rgb_bytes
        }

    def run_analysis(self):
        before_start, before_end, after_start, after_end = self._expand_dates(self.start_date, self.end_date)

        # Carrega a coleção completa apenas uma vez
        full_collection = self._load_full_collection()
        logger.info("Satellite collection loaded")

        # --- BEFORE mosaic ---
        before_col = full_collection.filterDate(before_start, before_end)
        self._ensure_not_empty(before_col, "BEFORE period", before_start, before_end)

        before_mosaic = before_col.mosaic()
        before_ndvi = before_mosaic.normalizedDifference(['B8_refl', 'B4_refl']).rename('NDVI')
        before_nbr = before_mosaic.normalizedDifference(['B8_refl', 'B12_refl']).rename('NBR')
        before_mosaic = before_mosaic.addBands([before_ndvi, before_nbr])

        logger.info("All indexes calculated for pre-fire date.")

        # --- AFTER mosaic ---
        after_col = full_collection.filterDate(after_start, after_end)
        self._ensure_not_empty(after_col, "AFTER period", after_start, after_end)

        after_mosaic = after_col.mosaic()
        after_ndvi = after_mosaic.normalizedDifference(['B8_refl', 'B4_refl']).rename('NDVI')
        after_nbr = after_mosaic.normalizedDifference(['B8_refl', 'B12_refl']).rename('NBR')
        after_mosaic = after_mosaic.addBands([after_ndvi, after_nbr])

        # Calcular RBR (temporal)
        delta_nbr = before_mosaic.select('NBR').subtract(after_mosaic.select('NBR')).rename('DeltaNBR')
        rbr = delta_nbr.divide(before_mosaic.select('NBR').add(1.001)).rename('RBR')

        logger.info("All remaining indexes calculated.")

        # Gerar binários
        rgb_pre_fire = self._generate_rgb_pre_fire(before_mosaic)
        rgb_post_fire = self._generate_rgb_post_fire(after_mosaic)

        logger.info("Binary data downloaded.")

        return {
            "rgb_pre_fire": rgb_pre_fire,
            "rgb_post_fire": rgb_post_fire
        }



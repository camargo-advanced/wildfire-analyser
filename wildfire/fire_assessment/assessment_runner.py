# assessment_runner.py
import logging
from datetime import datetime, timedelta
import ee
import os

from wildfire.fire_assessment.gee_client import GEEClient
from wildfire.fire_assessment.geometry_loader import GeometryLoader

logger = logging.getLogger(__name__)

DAYS_BEFORE_AFTER = 30
CLOUD_THRESHOLD = 100
COLLECTION_ID = "COPERNICUS/S2_SR_HARMONIZED"


class AssessmentRunner:
    def __init__(self, gee_client: GEEClient, roi: ee.Geometry):
        """
        Receives an initialized GEEClient and a Region of Interest (ROI).
        """
        self.gee = gee_client.ee
        self.roi = roi

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
            
            # qa = img.select('QA60')
            # cloud_mask = qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0))
            # return img.updateMask(cloud_mask)

            return img
        
        collection = collection.map(preprocess)

        # Debug: listar bandas da primeira imagem usando getInfo apenas para este debug
        try:
            first_image = ee.Image(collection.first())
            band_names = first_image.bandNames().getInfo()  # apenas para debug
            logger.info(f"Bands in first image: {band_names}")
        except Exception as e:
            logger.warning(f"Unable to fetch band names for debug: {e}")

        return collection

    def add_indices(mosaic: ee.Image):
        """Adiciona NDVI e NBR como bandas na imagem."""
        ndvi = mosaic.normalizedDifference(['B8_refl', 'B4_refl']).rename('NDVI')
        nbr = mosaic.normalizedDifference(['B8_refl', 'B12_refl']).rename('NBR')
        return mosaic.addBands([ndvi, nbr])

    def calculate_rbr(pre_mosaic: ee.Image, post_mosaic: ee.Image):
        """Calcula RBR a partir dos mosaicos antes e depois."""
        pre_nbr = pre_mosaic.select('NBR')
        post_nbr = post_mosaic.select('NBR')
        delta_nbr = pre_nbr.subtract(post_nbr).rename('DeltaNBR')
        rbr = delta_nbr.divide(pre_nbr.add(1.001)).rename('RBR')
        return rbr

    def save_mosaic_local(self, mosaic: ee.Image, filename: str, scale: int = 20):
        """
        Salva o mosaico como GeoTIFF local diretamente do Earth Engine para o disco.
        """
        import geemap
        
        abs_path = os.path.abspath(filename)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        logger.info(f"Downloading mosaic to {abs_path} with scale {scale}m ...")
        
        geemap.download_ee_image(
            image=mosaic.clip(self.roi),
            filename=abs_path,
            scale=scale,
            region=self.roi,
            overwrite=True,       # sobrescreve se já existir
            max_requests=5,       # limita requisições simultâneas
            max_cpus=2            # limita threads locais
        )

        logger.info(f"Mosaic saved at {abs_path}")

    def get_cloud_percentage(self, mosaic: ee.Image):
        qa = mosaic.select('QA60')
        
        cloud_mask = (
            qa.bitwiseAnd(1 << 10).gt(0)
            .Or(qa.bitwiseAnd(1 << 11).gt(0))
        )

        cloud_mean = cloud_mask.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=self.roi,
            scale=20,
            maxPixels=1e12
        ).get('QA60')

        return ee.Number(cloud_mean).multiply(100)

    def _ensure_not_empty(self, collection, label, start, end):
        try:
            size_val = collection.size().getInfo()
        except Exception:
            size_val = 0

        if size_val == 0:
            raise ValueError(f"No images found for {label}: {start} → {end}")
        
    def run_analysis(self, start_date: str, end_date: str):
        before_start, before_end, after_start, after_end = self._expand_dates(start_date, end_date)

        # Carrega a coleção completa apenas uma vez
        full_collection = self._load_full_collection()

        # --- BEFORE mosaic ---
        before_col = full_collection.filterDate(before_start, before_end)
        self._ensure_not_empty(before_col, "BEFORE period", before_start, before_end)

        # Debug: IDs das imagens BEFORE
        try:
            before_ids = before_col.aggregate_array('system:id').getInfo()
            logger.info(f"Images used for BEFORE mosaic ({before_start} → {before_end}): {before_ids}")
        except Exception as e:
            logger.warning(f"Couldn't fetch BEFORE image IDs: {e}")

        before_mosaic = before_col.mosaic()
        before_ndvi = before_mosaic.normalizedDifference(['B8_refl', 'B4_refl']).rename('NDVI')
        before_nbr = before_mosaic.normalizedDifference(['B8_refl', 'B12_refl']).rename('NBR')
        before_mosaic = before_mosaic.addBands([before_ndvi, before_nbr])

        # --- AFTER mosaic ---
        after_col = full_collection.filterDate(after_start, after_end)
        self._ensure_not_empty(after_col, "AFTER period", after_start, after_end)

        # Debug: IDs das imagens AFTER
        try:
            after_ids = after_col.aggregate_array('system:id').getInfo()
            logger.info(f"Images used for AFTER mosaic ({after_start} → {after_end}): {after_ids}")
        except Exception as e:
            logger.warning(f"Couldn't fetch AFTER image IDs: {e}")

        after_mosaic = after_col.mosaic()
        after_ndvi = after_mosaic.normalizedDifference(['B8_refl', 'B4_refl']).rename('NDVI')
        after_nbr = after_mosaic.normalizedDifference(['B8_refl', 'B12_refl']).rename('NBR')
        after_mosaic = after_mosaic.addBands([after_ndvi, after_nbr])

        # Calcula percentual de nuvens (EE Number)
        before_cloud_pct = self.get_cloud_percentage(before_mosaic)
        after_cloud_pct = self.get_cloud_percentage(after_mosaic)

        # Converte para número Python
        before_cloud_pct_val = before_cloud_pct.getInfo()
        after_cloud_pct_val = after_cloud_pct.getInfo()

        # Log com duas casas decimais
        logger.info(f"Cloud % BEFORE: {before_cloud_pct_val:.2f}%")
        logger.info(f"Cloud % AFTER: {after_cloud_pct_val:.2f}%")

        # Calcular RBR (temporal)
        delta_nbr = before_mosaic.select('NBR').subtract(after_mosaic.select('NBR')).rename('DeltaNBR')
        rbr = delta_nbr.divide(before_mosaic.select('NBR').add(1.001)).rename('RBR')

        return {
            "before": {"mosaic": before_mosaic, "cloud_percent": before_cloud_pct_val},
            "after": {"mosaic": after_mosaic, "cloud_percent": after_cloud_pct_val},
            "rbr": rbr
        }

# Main execution block
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    try:
        gee_client = GEEClient()
        logger.info("GEE Initialization complete")

        geojson_path = os.path.join("polygons", "eejatai.geojson")
        roi = GeometryLoader.load_geojson(geojson_path)

        runner = AssessmentRunner(gee_client, roi)
        result = runner.run_analysis("2025-01-01", "2025-01-01")
        #result = runner.run_analysis("2024-09-01", "2024-11-08")

        # Exportar mosaicos com bandas adicionais
        #runner.save_mosaic_local(result["before"]["mosaic"], "before_mosaic_with_indices.tif", scale=10)
        #runner.save_mosaic_local(result["after"]["mosaic"], "after_mosaic_with_indices.tif", scale=10)
        runner.save_mosaic_local(result["rbr"], "RBR.tif", scale=10)

    except Exception as e:
        logger.exception("Unexpected error during processing")

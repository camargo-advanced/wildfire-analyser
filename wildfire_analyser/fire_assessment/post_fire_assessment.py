# post_fire_assessment.py
import logging
import time

import ee
import requests

from wildfire_analyser.fire_assessment.date_utils import expand_dates
from wildfire_analyser.fire_assessment.gee_client import GEEClient
from wildfire_analyser.fire_assessment.geometry_loader import GeometryLoader
from wildfire_analyser.fire_assessment.deliverable import Deliverable
from wildfire_analyser.fire_assessment.validators import (
    validate_date,
    validate_geojson_path,
    validate_deliverables,
)
from wildfire_analyser.fire_assessment.downloaders import (
    download_single_band,
    merge_bands,
)

logger = logging.getLogger(__name__)

CLOUD_THRESHOLD = 100
COLLECTION_ID = "COPERNICUS/S2_SR_HARMONIZED"
    
class PostFireAssessment:
    def __init__(self, geojson_path: str, start_date: str, end_date: str, deliverables=None):
        # Validate input parameters
        validate_geojson_path(geojson_path)
        validate_date(start_date, "start_date")
        validate_date(end_date, "end_date")
        validate_deliverables(deliverables)
 
        # Store parameters
        self.start_date = start_date
        self.end_date = end_date
        self.deliverables = deliverables or []

        # Check chronological order
        if start_date > end_date:
            raise ValueError(f"'start_date' must be earlier than 'end_date'. Received: {start_date} > {end_date}")
 
        # Initialize and Autenticate to GEE
        self.gee = GEEClient().ee
        self.roi = GeometryLoader.load_geojson(geojson_path)
        
        # Registro de todos os tipos de imagens possíveis
        self._deliverable_registry = {
            Deliverable.RGB_PRE_FIRE: self._generate_rgb_pre_fire,
            Deliverable.RGB_POST_FIRE: self._generate_rgb_post_fire,
            Deliverable.NDVI_PRE_FIRE: self._generate_ndvi_pre_fire,
            Deliverable.NDVI_POST_FIRE: self._generate_ndvi_post_fire,
            Deliverable.RBR: self._generate_rbr,
        }

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

    def _ensure_not_empty(self, collection, start, end):
        try:
            size_val = collection.size().getInfo()
        except Exception:
            size_val = 0

        if size_val == 0:
            raise ValueError(f"No images found in date range {start} → {end}")
        
    def _generate_rgb_pre_fire(self, mosaic):
        return self._generate_rgb(mosaic, Deliverable.RGB_PRE_FIRE.value)

    def _generate_rgb_post_fire(self, mosaic):
        return self._generate_rgb(mosaic, Deliverable.RGB_POST_FIRE.value)

    def _generate_rgb(self, mosaic, filename_prefix):
        """
        Gera um RGB (B4,B3,B2) como um único GeoTIFF multibanda.
        Pode ser usado tanto para PRE FIRE quanto POST FIRE.
        
        Params:
            mosaic: ee.Image mosaic (antes ou depois)
            filename_prefix: string sem extensão (ex: "rgb_pre_fire" ou "rgb_post_fire")
        """
        
        rgb_image = mosaic.select([
            'B4_refl',  # Red
            'B3_refl',  # Green
            'B2_refl'   # Blue
        ])

        # Baixa cada banda separadamente
        b4 = download_single_band(rgb_image, 'B4_refl', region=self.roi, scale=10)
        b3 = download_single_band(rgb_image, 'B3_refl', region=self.roi, scale=10)
        b2 = download_single_band(rgb_image, 'B2_refl', region=self.roi, scale=10)

        # Junta num único TIFF multibanda
        rgb_bytes = merge_bands({
            "B4_refl": b4,
            "B3_refl": b3,
            "B2_refl": b2,
        })

        return {
            "filename": f"{filename_prefix}.tif", 
            "content_type": "image/tiff",
            "data": rgb_bytes
        }

    def _generate_ndvi_pre_fire(self, mosaic):
        img = mosaic.normalizedDifference(['B8_refl', 'B4_refl']).rename('ndvi')
        data = download_single_band(img, 'ndvi', region=self.roi, scale=10)
        return {
            "filename": f"{Deliverable.NDVI_PRE_FIRE.value}.tif",
            "content_type": "image/tiff",
            "data": data
        }

    def _generate_ndvi_post_fire(self, mosaic):
        img = mosaic.normalizedDifference(['B8_refl', 'B4_refl']).rename('ndvi')
        data = download_single_band(img, 'ndvi', region=self.roi, scale=10)
        return {
            "filename": f"{Deliverable.NDVI_POST_FIRE.value}.tif",
            "content_type": "image/tiff",
            "data": data
        }

    def _generate_rbr(self, rbr_img):
        """
        Gera apenas o RBR puro como GeoTIFF.
        """
        rbr_bytes = download_single_band(
            rbr_img,
            'rbr',
            region=self.roi,
            scale=10
        )

        return [
            {
                "filename": "rbr.tif",
                "content_type": "image/tiff",
                "data": rbr_bytes
            }
        ]

    def _generate_severity_visual(self, severity_img):
        """
        Gera o JPEG colorido da severidade usando exatamente
        a mesma paleta e parâmetros do JavaScript GEE.
        """
        # Mesmas cores, min, max do JS
        palette = [
            '00FF00',  # Unburned - verde
            'FFFF00',  # Low - amarelo
            'FFA500',  # Moderate - laranja
            'FF0000',  # High - vermelho
            '8B4513'   # Very High - marrom
        ]

        vis = severity_img.visualize(
            min=0,
            max=4,
            palette=palette
        )

        # Baixa como JPEG igual ao JS
        url = vis.getDownloadURL({
            "format": "JPEG",
            "region": self.roi,
            "scale": 10
        })

        response = requests.get(url, stream=True)
        response.raise_for_status()

        return {
            "filename": "severity.jpg",
            "content_type": "image/jpeg",
            "data": response.content
        }

    def _build_mosaic_with_indexes(self, collection):
        """
        Recebe uma coleção filtrada → gera mosaic → calcula NDVI, NBR → devolve mosaic com bandas extras.
        """
        mosaic = collection.mosaic()
        ndvi = mosaic.normalizedDifference(["B8_refl", "B4_refl"]).rename("ndvi")
        nbr  = mosaic.normalizedDifference(["B8_refl", "B12_refl"]).rename("nbr")
        return mosaic.addBands([ndvi, nbr])

    def _compute_rbr(self, before_mosaic, after_mosaic):
        """
        Computes RBR (Relative Burn Ratio) from BEFORE and AFTER mosaics.
        Assumes both mosaics already include band 'nbr'.
        """
        delta_nbr = before_mosaic.select('nbr').subtract(after_mosaic.select('nbr')).rename('dnbr')
        rbr = delta_nbr.divide(before_mosaic.select('nbr').add(1.001)).rename('rbr')
        return rbr

    def _compute_area_by_severity(self, severity_img):
        """
        Calcula a área por classe (hectares) dentro da ROI de forma otimizada.
        """
        # 1 pixel Sentinel-2 = 10 m → pixel area = 100 m² = 0.01 ha
        pixel_area_ha = ee.Image.pixelArea().divide(10000)

        # Cria uma imagem com 'severity' como máscara para cada classe
        def area_per_class(c):
            mask = severity_img.eq(c)
            return pixel_area_ha.updateMask(mask).rename('area_' + str(c))
        
        class_images = [area_per_class(c) for c in range(5)]
        stacked = ee.Image.cat(class_images)

        # Reduz todas as bandas ao mesmo tempo
        areas = stacked.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=self.roi,
            scale=10,
            maxPixels=1e12
        ).getInfo()

        return { c: float(areas.get(f'area_{c}', 0) or 0) for c in range(5) }

    def _classify_rbr_severity(self, rbr_img):
        """
        Classifica o RBR em classes de severidade.
        Classes típicas:
            0 = Unburned        (RBR < 0.1)
            1 = Low             (0.1 ≤ RBR < 0.27)
            2 = Moderate        (0.27 ≤ RBR < 0.44)
            3 = High            (0.44 ≤ RBR < 0.66)
            4 = Very High       (RBR ≥ 0.66)
        """

        severity = rbr_img.expression(
            """
            (b('rbr') < 0.10) ? 0 :
            (b('rbr') < 0.27) ? 1 :
            (b('rbr') < 0.44) ? 2 :
            (b('rbr') < 0.66) ? 3 :
                                4
            """
        ).rename("severity")

        return severity

    def run_analysis(self):
        timings = {}

        # Carrega a coleção completa apenas uma vez
        t0 = time.time()
        full_collection = self._load_full_collection()
        timings["Sat collection loaded"] = time.time() - t0

        before_start, before_end, after_start, after_end = expand_dates(
            self.start_date, self.end_date
        )

        # BEFORE
        t1 = time.time()
        before_collection = full_collection.filterDate(before_start, before_end)
        self._ensure_not_empty(before_collection, before_start, before_end)
        before_mosaic = self._build_mosaic_with_indexes(before_collection)

        # AFTER
        after_collection = full_collection.filterDate(after_start, after_end)
        self._ensure_not_empty(after_collection, after_start, after_end)
        after_mosaic = self._build_mosaic_with_indexes(after_collection)

        # Compute RBR
        rbr = self._compute_rbr(before_mosaic, after_mosaic)
        
        # Classificar e Calcular áreas por severidade
        severity = self._classify_rbr_severity(rbr)
        area_stats = self._compute_area_by_severity(severity)
        timings["Indexes calculated"] = time.time() - t1

        # Download dos binários
        t2 = time.time()
        images = {} 
        
        for d in self.deliverables:
            gen_fn = self._deliverable_registry.get(d)
                    
            if d == Deliverable.RBR:
                rbr_outputs = gen_fn(rbr)
                for out in rbr_outputs:
                    images[out["filename"]] = out

                # adiciona a visualização colorida
                images["severity_visual"] = self._generate_severity_visual(severity)
                continue

            if "pre" in d.value:
                images[d.value] = gen_fn(before_mosaic)
            else:
                images[d.value] = gen_fn(after_mosaic)
        timings["Images downloaded"] = time.time() - t2

        return {
            "images": images,
            "timings": timings,
            "area_by_severity": area_stats

        }


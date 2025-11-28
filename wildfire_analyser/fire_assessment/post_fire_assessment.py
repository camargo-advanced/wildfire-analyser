# post_fire_assessment.py
import logging
import json
from pathlib import Path
import time

import ee
import requests
from rasterio.io import MemoryFile

from wildfire_analyser.fire_assessment.date_utils import expand_dates
from wildfire_analyser.fire_assessment.gee_client import GEEClient
from wildfire_analyser.fire_assessment.deliverable import Deliverable
from wildfire_analyser.fire_assessment.validators import (
    validate_date,
    validate_geojson_path,
    validate_deliverables,
    ensure_not_empty
)
from wildfire_analyser.fire_assessment.downloaders import download_single_band

CLOUD_THRESHOLD = 100
COLLECTION_ID = "COPERNICUS/S2_SR_HARMONIZED"
DAYS_BEFORE_AFTER = 30

logger = logging.getLogger(__name__)


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
        self.roi = self.load_geojson(geojson_path)

    def load_geojson(self, path: str) -> ee.Geometry:
        """Load a GeoJSON file and return an Earth Engine Geometry."""
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"GeoJSON not found: {path}")

        with open(file_path, 'r') as f:
            geojson = json.load(f)

        # Converts GeoJSON to EE geometry
        try:
            geometry = ee.Geometry(geojson['features'][0]['geometry'])
        except Exception as e:
            raise ValueError(f"Invalid GeoJSON geometry: {e}")
        
        return geometry
    
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
        
        # Function to add reflectance (_refl).
        def preprocess(img):
            refl_bands = img.select('B.*').multiply(0.0001)
            refl_names = refl_bands.bandNames().map(lambda b: ee.String(b).cat('_refl'))
            img = img.addBands(refl_bands.rename(refl_names))
            return img
        
        collection = collection.map(preprocess)

        return collection

    def merge_bands(self, band_tiffs: dict[str, bytes]) -> bytes:
        """
        Merge multiple single-band GeoTIFFs (raw bytes) into a single multi-band GeoTIFF.
        """
        memfiles = {b: MemoryFile(tiff_bytes) for b, tiff_bytes in band_tiffs.items()}
        datasets = {b: memfiles[b].open() for b in memfiles}

        # Reference band to copy metadata
        first = next(iter(datasets.values()))
        profile = first.profile.copy()
        profile.update(count=len(datasets))

        # Merge bands
        with MemoryFile() as merged_mem:
            with merged_mem.open(**profile) as dst:
                for idx, (band, ds) in enumerate(datasets.items(), start=1):
                    dst.write(ds.read(1), idx)

            return merged_mem.read()
        
    def _generate_rgb_pre_fire(self, mosaic: ee.Image) -> dict:
        """
        Generates two GeoTIFF and JPEG images.
        """
        # Generate the technical multi-band RGB GeoTIFF
        tiff = self._generate_rgb(mosaic, Deliverable.RGB_PRE_FIRE.value)
        
        # Generate the visual RGB JPEG (with overlay)
        rgb_img = mosaic.select(['B4_refl', 'B3_refl', 'B2_refl'])
        vis_params = {"min": 0.0, "max": 0.3}
        jpeg = self._generate_visual_image(rgb_img, "rgb_pre_fire_visual", vis_params)
    
        return tiff, jpeg

    def _generate_rgb_post_fire(self, mosaic: ee.Image) -> dict:
        """
        Generates two GeoTIFF and JPEG images.
        """
        # Generate the technical multi-band RGB GeoTIFF
        tiff = self._generate_rgb(mosaic, Deliverable.RGB_POST_FIRE.value)

        # Generate the visual RGB JPEG (with overlay)
        rgb_img = mosaic.select(['B4_refl', 'B3_refl', 'B2_refl'])
        vis_params = {"min": 0.0, "max": 0.3}
        jpeg = self._generate_visual_image(rgb_img, "rgb_post_fire_visual", vis_params)

        return tiff, jpeg

    def _generate_rgb(self, mosaic, filename_prefix):
        """
        Generates an RGB (B4, B3, B2) as a single multiband GeoTIFF.
        """
        # Merges into a single multiband TIFF.
        image_bytes = self.merge_bands({
            "B4_refl": download_single_band(mosaic, 'B4_refl', region=self.roi),
            "B3_refl": download_single_band(mosaic, 'B3_refl', region=self.roi),
            "B2_refl": download_single_band(mosaic, 'B2_refl', region=self.roi),
        })

        return {
            "filename": f"{filename_prefix}.tif", 
            "content_type": "image/tiff",
            "data": image_bytes
        }

    def _generate_visual_image(self, img: ee.Image, filename: str, vis_params: dict) -> dict:
        """
        Generates a JPEG of an Earth Engine image with styled ROI overlay.
        """
        vis = img.visualize(**vis_params)
        overlay = self._styled_roi_overlay().visualize()
        final = vis.blend(overlay)

        url = final.getDownloadURL({
            "format": "JPEG",
            "region": self.roi,
            "scale": 10
        })

        response = requests.get(url, stream=True)
        response.raise_for_status()

        return {
            "filename": f"{filename}.jpg",
            "content_type": "image/jpeg",
            "data": response.content
        }
    
    def _generate_ndvi(self, mosaic: ee.Image, filename: str) -> dict:
        """
        Computes NDVI from a mosaic using reflectance bands (B8_refl and B4_refl).
        Downloads the resulting index as a single-band GeoTIFF and returns it as a
        deliverable object. 
        """
        data = download_single_band(mosaic, 'ndvi', region=self.roi)
        return {
            "filename": f"{filename}.tif",
            "content_type": "image/tiff",
            "data": data
        }

    def _generate_rbr(self, rbr_img: ee.Image, severity_img: ee.Image) -> tuple[dict, dict, dict]:
        """
        Computes RBR and generates deliverables:
            - rbr.tif (GeoTIFF)
            - rbr_severity_visual.jpg (RBR class color)
            - rbr_visual.jpg (RBR color JPEG with rbrVis palette)
        """
        # GeoTIFF
        image_bytes = download_single_band(rbr_img, 'rbr', region=self.roi, scale=10)
        tiff_deliverable = {
            "filename": "rbr.tif",
            "content_type": "image/tiff",
            "data": image_bytes
        }

        # Visual JPEG
        vis_params = {"min": -0.5, "max": 0.6, "palette": ["black", "yellow", "red"]}
        visual_deliverable = self._generate_visual_image(rbr_img, "rbr_visual", vis_params)

        # Severity visual JPEG
        severity_vis_params = {
            "min": 0,
            "max": 4,
            "palette": ["00FF00","FFFF00","FFA500","FF0000","8B4513"]
        }
        severity_visual_deliverable = self._generate_visual_image(severity_img, "rbr_severity_visual", severity_vis_params)

        return tiff_deliverable, severity_visual_deliverable, visual_deliverable

    def _styled_roi_overlay(self):
        """Creates a styled overlay of the ROI polygon (purple outline, no fill)."""
        fc = ee.FeatureCollection([ee.Feature(self.roi)])
        styled = fc.style(
            color='#800080',     # purple border
            fillColor='00000000',  # transparent fill
            width=3
        )
        return styled

    def _build_mosaic_with_indexes(self, collection: ee.ImageCollection) -> ee.Image:
        """
        Takes a filtered collection → builds a mosaic → computes NDVI and 
        NBR → returns a mosaic with the additional bands.
        """
        mosaic = collection.mosaic()
        ndvi = mosaic.normalizedDifference(["B8_refl", "B4_refl"]).rename("ndvi")
        nbr  = mosaic.normalizedDifference(["B8_refl", "B12_refl"]).rename("nbr")
        return mosaic.addBands([ndvi, nbr])

    def _compute_rbr(self, before_mosaic: ee.Image, after_mosaic: ee.Image) -> ee.Image:
        """
        Computes RBR (Relative Burn Ratio) from BEFORE and AFTER mosaics.
        Assumes both mosaics already include band 'nbr'.
        """
        delta_nbr = before_mosaic.select('nbr').subtract(after_mosaic.select('nbr')).rename('dnbr')
        rbr = delta_nbr.divide(before_mosaic.select('nbr').add(1.001)).rename('rbr')
        return rbr

    def _compute_area_by_severity(self, severity_img: ee.Image) -> dict[int, float]:
        """
        Calculates the area per class (in hectares) within the ROI in an optimized way.
        """
        # 1 Sentinel-2 pixel = 10 m → pixel area = 100 m² = 0.01 ha
        pixel_area_ha = ee.Image.pixelArea().divide(10000)

        # Creates an image using 'severity' as a mask for each class
        def area_per_class(c):
            mask = severity_img.eq(c)
            return pixel_area_ha.updateMask(mask).rename('area_' + str(c))
        
        class_images = [area_per_class(c) for c in range(5)]
        stacked = ee.Image.cat(class_images)

        # Reduces all bands simultaneously
        areas = stacked.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=self.roi,
            scale=10,
            maxPixels=1e12
        ).getInfo()

        return { c: float(areas.get(f'area_{c}', 0) or 0) for c in range(5) }

    def _classify_rbr_severity(self, rbr_img: ee.Image) -> ee.Image:
        """
        Classify RBR by severity:
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

    def format_severity_table(self, area_dict: dict[int, float]) -> list[dict]:
        """
        Converts the raw {severity: hectares} dict into a structured JSON
        with severity, severity_name, ha, percent, and color.
        """

        severity_names = {
            0: "Unburned",
            1: "Low",
            2: "Moderate",
            3: "High",
            4: "Very High",
        }

        severity_colors = {
            0: "Green",
            1: "Yellow",
            2: "Orange",
            3: "Red",
            4: "Maroon",
        }

        total_ha = sum(area_dict.values()) or 1  # avoid division by zero

        table = []
        for s in range(5):
            ha = float(area_dict.get(s, 0))
            pct = (ha / total_ha) * 100

            table.append({
                "severity": s,
                "severity_name": severity_names[s],
                "ha": round(ha, 2),
                "percent": round(pct, 2),
                "color": severity_colors[s]
            })

        return table

    def run_analysis(self):
        timings = {}

        # Load satellite collection
        t0 = time.time()
        full_collection = self._load_full_collection()
        timings["Sat collection loaded"] = time.time() - t0

        before_start, before_end, after_start, after_end = expand_dates(
            self.start_date, self.end_date, DAYS_BEFORE_AFTER 
        )

        # Build pre fire mosaic
        t1 = time.time()
        before_collection = full_collection.filterDate(before_start, before_end)
        ensure_not_empty(before_collection, before_start, before_end)
        before_mosaic = self._build_mosaic_with_indexes(before_collection)

        # Build post fire mosaic
        after_collection = full_collection.filterDate(after_start, after_end)
        ensure_not_empty(after_collection, after_start, after_end)
        after_mosaic = self._build_mosaic_with_indexes(after_collection)

        # Compute RBR
        rbr = self._compute_rbr(before_mosaic, after_mosaic)
        
        # Classification and severity extension calculation
        severity = self._classify_rbr_severity(rbr)
        area_stats = self._compute_area_by_severity(severity)
        timings["Indexes calculated"] = time.time() - t1

        deliverable_registry = {
            Deliverable.RGB_PRE_FIRE: lambda ctx: self._generate_rgb_pre_fire(before_mosaic),
            Deliverable.RGB_POST_FIRE: lambda ctx: self._generate_rgb_post_fire(after_mosaic),
            Deliverable.NDVI_PRE_FIRE: lambda ctx: [self._generate_ndvi(before_mosaic, Deliverable.NDVI_PRE_FIRE.value)],
            Deliverable.NDVI_POST_FIRE: lambda ctx: [self._generate_ndvi(after_mosaic, Deliverable.NDVI_POST_FIRE.value)],
            Deliverable.RBR: lambda ctx: self._generate_rbr(rbr, severity),
        }

        # Download binaries
        t2 = time.time()
        images = {} 

        for d in self.deliverables:
            gen_fn = deliverable_registry.get(d)
            outputs = gen_fn({})
            if isinstance(outputs, tuple) or isinstance(outputs, list):
                for out in outputs:
                    images[out["filename"]] = out
            else:
                images[outputs["filename"]] = outputs

        timings["Images downloaded"] = time.time() - t2

        return {
            "images": images,
            "timings": timings,
            "area_by_severity": self.format_severity_table(area_stats)
        }


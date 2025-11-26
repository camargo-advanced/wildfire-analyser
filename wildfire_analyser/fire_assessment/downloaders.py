# downloaders.py
import logging
import ee
from rasterio.io import MemoryFile
import numpy as np

logger = logging.getLogger(__name__)


def download_single_band(image: ee.Image, band_name: str, region, scale: int = 10) -> bytes:
    """
    Downloads a single band from an Earth Engine ee.Image.
    Returns the raw GeoTIFF bytes.
    """
    try:
        url = image.select(band_name).getDownloadURL({
            "scale": scale,
            "region": region,
            "format": "GEO_TIFF"
        })

        import requests
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.content

    except Exception as e:
        logger.error(f"Failed to download band '{band_name}': {e}")
        raise

def merge_bands(band_tiffs: dict[str, bytes]) -> bytes:
    """
    Merge multiple single-band GeoTIFFs (raw bytes) into a single multi-band GeoTIFF.
    band_tiffs → dict: {"red": b"...", "green": b"..."}
    Returns merged GeoTIFF bytes.
    """
    try:
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

    except Exception as e:
        logger.error(f"Failed to merge GeoTIFF bands: {e}")
        raise


def download_geotiff_bytes(image: ee.Image, region, scale: int = 10) -> bytes:
    """
    Downloads a full RGB (multi-band) GeoTIFF from GEE as bytes.
    """
    try:
        url = image.getDownloadURL({
            "scale": scale,
            "region": region,
            "format": "GEO_TIFF"
        })

        import requests
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.content

    except Exception as e:
        logger.error(f"Failed to download multi-band GeoTIFF: {e}")
        raise

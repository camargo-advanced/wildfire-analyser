# downloaders.py
import logging
import ee

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

# downloaders.py
import logging
import ee
import requests

logger = logging.getLogger(__name__)


def download_single_band(
    image: ee.Image, 
    band_name: str, 
    region: ee.Geometry, 
    scale: int = 10
) -> bytes:
    """
    Downloads a single band from an Earth Engine ee.Image.
    Returns the raw GeoTIFF bytes.
    """
    try:
        MAX_MB = 50
        MAX_BYTES = MAX_MB * 1024 * 1024

        # Estimate number of pixels using reduceRegion
        pixel_count = image.select(band_name) \
            .reduceRegion(
                reducer=ee.Reducer.count(),
                geometry=region,
                scale=scale,
                maxPixels=1e13
            ) \
            .get(band_name) \
            .getInfo()

        if pixel_count is None:
            raise RuntimeError("Could not estimate pixel count (region too small?)")

        # 4 bytes per pixel for float32 GeoTIFF
        est_bytes = pixel_count * 4

        # If too large, switch to 50 m 
        if est_bytes > MAX_BYTES and scale == 10:
            scale = 50
            logger.warning(
                f"Image too large at 10 m ({est_bytes/1e6:.1f} MB). "
                f"Switching to {scale} m resolution."
            )

        # Download image
        url = image.select(band_name).getDownloadURL({
            "scale": scale,
            "region": region,
            "format": "GEO_TIFF"
        })

        resp = requests.get(url)
        resp.raise_for_status()
        return resp.content

    except Exception as e:
        logger.error(f"Failed to download band '{band_name}': {e}")
        raise

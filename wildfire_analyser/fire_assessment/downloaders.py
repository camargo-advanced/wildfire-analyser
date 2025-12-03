# downloaders.py
import logging
import ee
import requests

logger = logging.getLogger(__name__)

# Local cache:  { (bbox_key) → best_scale }
scale_cache = {}


def bbox_key(region: ee.Geometry):
    """
    Compute a stable and compact key for a geometry.

    - Uses the bounding box
    - Rounds coordinates to 3 decimal places
    - Output: tuple usable as dict key
    """
    coords = region.bounds().coordinates().getInfo()
    flat = [round(c, 3) for pair in coords[0] for c in pair]
    return tuple(flat)

def download_image(
    image: ee.Image,
    region: ee.Geometry,
    scale: int = 10,
    format: str = "GEO_TIFF",
    bands: list | None = None,
) -> bytes:
    """
    Generic and robust Earth Engine image downloader with caching.

    - If a successful scale was already found for this region, reuses it directly.
    - Otherwise tries scales: scale → scale+15 → ... → 150.
    - Caches the first scale that works for future downloads.
    - Works for both single-band (TIFF) and multi-band images.
    """

    region_id = bbox_key(region)

    # Select band(s) if needed
    img = image.select(bands) if bands else image

    # Try using cached scale first (fast path)
    if region_id in scale_cache:
        cached_scale = scale_cache[region_id]

        try:
            logger.info(f"Using cached scale {cached_scale} m for region {region_id}")
            url = img.getDownloadURL({
                "scale": cached_scale,
                "region": region,
                "format": format
            })

            resp = requests.get(url, stream=True)
            resp.raise_for_status()

            logger.info(f"Downloaded successfully with cached scale {cached_scale} m")
            return resp.content

        except Exception as e:
            logger.warning(
                f"Cached scale {cached_scale} m failed ({e}). Will try fallback loop."
            )
            # continue to fallback progressive search

    # Progressive search for a working scale (slow path)
    for attempt_scale in range(scale, 151, 15):

        try:
            url = img.getDownloadURL({
                "scale": attempt_scale,
                "region": region,
                "format": format
            })

            resp = requests.get(url, stream=True)
            resp.raise_for_status()

            logger.info(f"Downloaded successfully at {attempt_scale} m")

            # SAVE the working scale in cache for future images
            scale_cache[region_id] = attempt_scale
            logger.info(
                f"Caching scale {attempt_scale} m for region {region_id}"
            )

            return resp.content

        except Exception as e:
            # classic GEE “too large” error
            if "Total request size" in str(e):
                logger.info(
                    f"Scale {attempt_scale} m rejected (too large). Trying next..."
                )
                continue

            # other error → raise immediately
            raise

    # No scale worked up to 150 m
    raise RuntimeError(
        "Unable to download image even at 150 m — region too large."
    )

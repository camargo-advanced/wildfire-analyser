# downloaders.py
import logging
import ee
import requests

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# Função ÚNICA — genérica para TIFF/JPEG/whatever
# -------------------------------------------------------------------------
def download_image(
    image: ee.Image,
    region: ee.Geometry,
    scale: int = 10,
    format: str = "GEO_TIFF",
    bands: list | None = None,
) -> bytes:
    """
    Generic and robust Earth Engine downloader.
    
    - Tenta automaticamente: 10 → 20 → ... → 150 m
    - Aumenta scale SOMENTE quando o GEE retornar erro real de tamanho
    - Serve para TIFF (single-band) ou JPEG/PNG (visual)
    - Retorna sempre bytes
    """
    try:
        # Select band(s) if needed
        img = image
        if bands:
            img = image.select(bands)

        # LOOP: 10 → 20 → ... → 150
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
                return resp.content

            except Exception as e:
                # erro clássico de tamanho do GEE
                if "Total request size" in str(e):
                    logger.info(
                        f"Scale {attempt_scale} m rejected by EE (too large). "
                        f"Trying a larger scale..."
                    )
                    continue  # tenta próximo scale

                # outro erro → levantar
                raise

        raise RuntimeError(
            "Unable to download image even at 150 m — region too large."
        )

    except Exception as e:
        logger.error(f"download_image failed: {e}")
        raise

# -------------------------------------------------------------------------
# Wrappers → API igual à sua versão anterior
# -------------------------------------------------------------------------

def download_single_band(
    image: ee.Image,
    band_name: str,
    region: ee.Geometry,
    scale: int = 10
) -> bytes:
    """
    Wrapper for downloading a single band TIFF.
    """
    return download_image(
        image=image,
        region=region,
        scale=scale,
        format="GEO_TIFF",
        bands=[band_name]
    )

def download_visual_image(
    img: ee.Image,
    region: ee.Geometry,
    scale: int = 10,
    format: str = "JPEG"
) -> bytes:
    """
    Wrapper for multi-band (usually RGB) visualization downloads.
    """
    return download_image(
        image=img,
        region=region,
        scale=scale,
        format=format,
        bands=None
    )
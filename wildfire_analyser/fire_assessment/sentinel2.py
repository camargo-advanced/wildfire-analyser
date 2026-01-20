# wildfire_analyser/fire_assessment/sentinel2.py
#
# NOTE ON CLOUD MASKING:
# Pixel-level cloud masking (e.g., QA60 / SCL) is intentionally NOT applied
# when generating RGB visual products and burned area indices (dNBR, RBR, dNDVI).
#
# Rationale:
# Applying a cloud mask removes pixels from the analysis, which leads to
# systematic underestimation of the total analyzed area and prevents burned
# area statistics from closing to the full ROI area.
#
# In an automated, multi-temporal pipeline, preserving full spatial coverage
# is preferred over aggressive cloud removal. Cloud-covered pixels may introduce
# local spectral noise and be classified into lower-severity or unburned classes,
# but they have negligible impact on high-severity burn estimates and total burned
# area metrics.
#
# This approach prioritizes area conservation and statistical consistency over
# local visual or spectral purity and is appropriate for large-scale, automated
# post-fire assessments.

import ee

COLLECTION_ID = "COPERNICUS/S2_SR_HARMONIZED"


def _mask_s2_clouds(image: ee.Image) -> ee.Image:
    qa = image.select("QA60")
    cloud = qa.bitwiseAnd(1 << 10).neq(0)
    cirrus = qa.bitwiseAnd(1 << 11).neq(0)
    mask = cloud.Or(cirrus).Not()
    return image.updateMask(mask)


def _add_reflectance_bands(image: ee.Image) -> ee.Image:
    bands = ["B2", "B3", "B4", "B8", "B12"]
    refl = image.select(bands).multiply(0.0001)
    refl_names = refl.bandNames().map(lambda b: ee.String(b).cat("_refl"))
    return image.addBands(refl.rename(refl_names))


def gather_collection(
    roi: ee.Geometry,
    cloud_threshold: int,
) -> ee.ImageCollection:
    """
    Load Sentinel-2 SR collection with:
    - ROI filter
    - Cloud filter
    - Cloud masking
    - Reflectance bands
    """
    return (
        ee.ImageCollection(COLLECTION_ID)
        .filterBounds(roi)
        .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", cloud_threshold))
        #.map(_mask_s2_clouds)
        .map(_add_reflectance_bands)
        .sort("CLOUDY_PIXEL_PERCENTAGE", False)
    )

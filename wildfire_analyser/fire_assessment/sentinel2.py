# SPDX-License-Identifier: MIT
#
# Sentinel-2 data access and preprocessing utilities.
#
# This module provides helper functions for loading and preparing Sentinel-2
# Surface Reflectance imagery for use in the fire assessment pipeline. It
# encapsulates dataset selection, spatial and cloud filtering, and band
# normalization.
#
# NOTE ON CLOUD MASKING
# --------------------
# Pixel-level cloud masking (e.g., QA60 or SCL-based masks) is intentionally
# NOT applied when generating RGB visual products and burned area indices
# (dNBR, RBR, dNDVI).
#
# Rationale:
# Applying a cloud mask removes pixels from the analysis, which leads to
# systematic underestimation of the total analyzed area and prevents burned
# area statistics from closing to the full ROI area.
#
# In an automated, multi-temporal pipeline, preserving full spatial coverage
# is preferred over aggressive cloud removal. Cloud-covered pixels may
# introduce local spectral noise and be classified into lower-severity or
# unburned classes, but they have negligible impact on high-severity burn
# estimates and total burned area metrics.
#
# This approach prioritizes area conservation and statistical consistency over
# local visual or spectral purity and is appropriate for large-scale,
# automated post-fire assessments.
#
# Responsibilities of this module:
# - Define the Sentinel-2 collection used by the pipeline.
# - Apply spatial and metadata-based filtering.
# - Normalize reflectance bands for downstream processing.
#
# This module does NOT:
# - Implement burn indices or statistics.
# - Perform DAG execution or dependency resolution.
# - Define user-facing deliverables.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


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
        # .map(_mask_s2_clouds)
        .map(_add_reflectance_bands)
        .sort("CLOUDY_PIXEL_PERCENTAGE", False)
    )

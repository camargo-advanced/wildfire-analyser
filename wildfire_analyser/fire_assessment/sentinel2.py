# SPDX-License-Identifier: MIT
#
# Sentinel-2 data access and preprocessing utilities.
#
# This module provides helper functions for loading and preparing Sentinel-2
# Surface Reflectance imagery for use in the fire assessment pipeline. It
# encapsulates dataset selection, spatial and cloud filtering, and band
# normalization.
#
# Responsibilities of this module:
# - Define the Sentinel-2 collection used by the pipeline.
# - Apply spatial and metadata-based filtering.
# - Normalize reflectance bands for downstream processing.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


import ee

COLLECTION_ID = "COPERNICUS/S2_SR_HARMONIZED"


def _add_reflectance_bands(image: ee.Image) -> ee.Image:
    bands = ["B2", "B3", "B4", "B8", "B12"]
    refl = image.select(bands).multiply(0.0001)
    refl_names = refl.bandNames().map(lambda b: ee.String(b).cat("_refl"))
    return image.addBands(refl.rename(refl_names))


def gather_collection(
    roi: ee.Geometry,
) -> ee.ImageCollection:
    """
    Load Sentinel-2 SR collection.
    - Select dataset
    - Filter by ROI
    - Add normalized reflectance bands
    """
    return (
        ee.ImageCollection(COLLECTION_ID)
        .filterBounds(roi)
        .map(_add_reflectance_bands)
    )

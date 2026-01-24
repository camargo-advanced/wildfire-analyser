# SPDX-License-Identifier: MIT
#
# dNDVI discrete classification and visualization renderer.
#
# This module implements a paper-style discrete classification for the
# Differenced Normalized Difference Vegetation Index (dNDVI) and applies a
# standardized color palette for qualitative burn severity visualization.
#
# Design notes:
# - Continuous dNDVI values are mapped to discrete integer severity classes
#   to support consistent visual interpretation and reporting.
# - Visualization logic is strictly separated from scientific computation;
#   this renderer does not modify or validate the underlying dNDVI data.
# - The region of interest (ROI) is rendered as a vector outline to provide
#   spatial context while preserving surrounding imagery.
#
# Responsibilities of this module:
# - Classify continuous dNDVI values into discrete severity classes.
# - Apply a fixed burn severity color palette.
# - Overlay the ROI boundary for contextual visualization.
# - Return an Earth Engine Image suitable for thumbnail generation.
#
# This module does NOT:
# - Compute NDVI or dNDVI values.
# - Perform quantitative analysis or area statistics.
# - Trigger Earth Engine execution or data export by itself.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


import ee


def dndvi_visual(image: ee.Image, roi: ee.Geometry) -> ee.Image:
    # Tabela 5 — dNDVI (paper)
    classified = (
        ee.Image(0)  # Unburned (< 0.07)
        .where(image.gte(0.10).And(image.lt(0.20)), 1)   # Low
        .where(image.gte(0.20).And(image.lt(0.33)), 2)   # Moderate
        .where(image.gte(0.33).And(image.lt(0.44)), 3)   # High
        .where(image.gte(0.45), 4)                       # Very High
    )

    styled = classified.visualize(
        min=0,
        max=4,
        palette=[
            "36a402",  # Unburned
            "fbfb01",  # Low
            "feb012",  # Moderate
            "f50003",  # High
            "6a044d",  # Very High
        ],
    )

    outline = ee.Image().byte().paint(
        ee.FeatureCollection(roi),
        color=1,
        width=2,
    )

    return styled.blend(outline.visualize(palette=["000000"]))

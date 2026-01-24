# SPDX-License-Identifier: MIT
#
# dNBR discrete classification and visualization renderer.
#
# This module implements a paper-style discrete classification for the
# Differenced Normalized Burn Ratio (dNBR) and applies a fixed color palette
# for qualitative burn severity visualization. 
#
# Design notes:
# - Classification is performed using discrete integer classes to match
#   scientific reporting conventions.
# - Visualization is strictly separated from scientific computation; this
#   renderer does not alter the original continuous dNBR values.
# - The region of interest (ROI) is overlaid as a vector outline to provide
#   spatial context without masking surrounding areas.
#
# Responsibilities of this module:
# - Classify continuous dNBR values into discrete severity classes.
# - Apply a standardized burn severity color palette.
# - Overlay the ROI boundary for contextual visualization.
# - Return an Earth Engine Image suitable for thumbnail generation.
#
# This module does NOT:
# - Compute dNBR from pre- and post-fire imagery.
# - Perform area statistics or quantitative analysis.
# - Trigger Earth Engine execution or data export by itself.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


import ee

def dnbr_visual(image: ee.Image, roi: ee.Geometry) -> ee.Image:
    # Classificação discreta (paper-style)
    classified = (
        ee.Image(0)  # Unburned
        .where(image.gte(0.10).And(image.lt(0.27)), 1)   # Low
        .where(image.gte(0.27).And(image.lt(0.44)), 2)  # Moderate
        .where(image.gte(0.44).And(image.lt(0.66)), 3)  # High
        .where(image.gte(0.66), 4)                      # Very High
    )

    styled = classified.visualize(
        min=0.0,
        max=4.0,
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

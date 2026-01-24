# SPDX-License-Identifier: MIT
#
# RBR discrete classification and visualization renderer.
#
# This module implements a paper-style discrete classification for the
# Relativized Burn Ratio (RBR) and applies a standardized color palette for
# qualitative burn severity visualization. Classification thresholds follow
# commonly adopted ranges in wildfire severity assessment literature.
#
# Design notes:
# - Continuous RBR values are mapped to discrete integer severity classes to
#   support consistent visual interpretation and reporting.
# - Visualization logic is strictly separated from scientific computation;
#   this renderer does not modify or validate the underlying RBR data.
# - The region of interest (ROI) is rendered as a vector outline to provide
#   spatial context while preserving surrounding imagery.
#
# Responsibilities of this module:
# - Classify continuous RBR values into discrete severity classes.
# - Apply a fixed burn severity color palette.
# - Overlay the ROI boundary for contextual visualization.
# - Return an Earth Engine Image suitable for thumbnail generation.
#
# This module does NOT:
# - Compute RBR or dNBR values.
# - Perform quantitative analysis or area statistics.
# - Trigger Earth Engine execution or data export by itself.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


import ee


def rbr_visual(image: ee.Image, roi: ee.Geometry) -> ee.Image:
    # Classificação por faixas (paper-style)
    classified = (
        ee.Image(0)  # Unburned
        .where(image.gte(0.10).And(image.lt(0.27)), 1)   # Low
        .where(image.gte(0.27).And(image.lt(0.44)), 2)  # Moderate
        .where(image.gte(0.44).And(image.lt(0.66)), 3)  # High
        .where(image.gte(0.66), 4)                      # Very High
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

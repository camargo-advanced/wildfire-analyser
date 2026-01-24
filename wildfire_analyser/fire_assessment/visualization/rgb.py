# SPDX-License-Identifier: MIT
#
# RGB pre- and post-fire visualization renderers.
#
# This module defines RGB visualization helpers for pre-fire and post-fire
# imagery using standard Sentinel-2 reflectance bands. The renderers apply
# consistent visualization parameters to enable qualitative visual comparison
# of surface conditions before and after a wildfire event.
#
# Design notes:
# - Visualization parameters (bands, min/max stretch, gamma) are fixed to
#   ensure consistent appearance across pre- and post-fire scenes.
# - Visualization logic is strictly separated from scientific processing;
#   these functions do not alter or validate the underlying spectral data.
# - The region of interest (ROI) is rendered as a vector outline to provide
#   spatial context without masking surrounding areas.
#
# Responsibilities of this module:
# - Apply RGB visualization to pre-fire and post-fire images.
# - Ensure visual consistency between temporal scenes.
# - Overlay the ROI boundary for contextual interpretation.
# - Return Earth Engine Images suitable for thumbnail generation.
#
# This module does NOT:
# - Perform atmospheric correction or spectral analysis.
# - Compute burn indices or severity metrics.
# - Trigger Earth Engine execution or data export by itself.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


import ee


def _outline(roi):
    return ee.Image().byte().paint(
        featureCollection=ee.FeatureCollection(roi),
        color=1,
        width=2,
    )


def rgb_pre_fire_visual(image: ee.Image, roi: ee.Geometry) -> ee.Image:
    vis = image.visualize(
        bands=["red", "green", "blue"],
        min=0.02,
        max=0.30,
        gamma=1.2,
    )
    return vis.blend(_outline(roi).visualize(palette=["000000"]))


def rgb_post_fire_visual(image: ee.Image, roi: ee.Geometry) -> ee.Image:
    vis = image.visualize(
        bands=["red", "green", "blue"],
        min=0.02,
        max=0.30,
        gamma=1.2,
    )
    return vis.blend(_outline(roi).visualize(palette=["000000"]))

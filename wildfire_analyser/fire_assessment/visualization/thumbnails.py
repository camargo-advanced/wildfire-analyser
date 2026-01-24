# SPDX-License-Identifier: MIT
#
# Earth Engine thumbnail generation helpers.
#
# This module provides a lightweight helper for generating visualization
# thumbnails from Earth Engine Images. Thumbnails are intended for preview
# and reporting purposes only and are generated using the Earth Engine
# thumbnail service.
#
# Design notes:
# - Earth Engine objects are evaluated lazily until getThumbURL() is called.
# - Thumbnail generation triggers server-side execution but returns
#   immediately with a signed URL.
# - Images are clipped to the bounding box of the region of interest (ROI)
#   to preserve spatial context while limiting request size.
# - Fixed dimensions are used instead of scale to avoid Earth Engine pixel
#   grid and request size limitations.
#
# Responsibilities of this module:
# - Generate stable thumbnail URLs for visual deliverables.
# - Apply spatial clipping to the ROI bounding box.
# - Define thumbnail rendering parameters (dimensions, format).
#
# This module does NOT:
# - Perform scientific computation or validation.
# - Export or persist imagery to storage backends.
# - Block execution waiting for server-side processing.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


import ee


def get_visual_thumbnail_url(
    image: ee.Image,
    roi: ee.Geometry,
) -> str:
    image = image.clip(roi.bounds())
    return image.getThumbURL({
        "dimensions": 1024,
        "format": "jpg",
    })

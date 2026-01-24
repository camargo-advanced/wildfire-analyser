# SPDX-License-Identifier: MIT
#
# Visual rendering registry for fire assessment deliverables.
#
# This module defines the mapping between visual deliverables and their
# corresponding rendering functions. Visual renderers transform scientific
# Earth Engine images into styled, human-readable visual representations
# (e.g. RGB composites and burn severity maps).
#
# Visual deliverables reuse the same underlying scientific data and differ
# only in presentation. They are intended for preview, reporting, and
# qualitative inspection, not for quantitative analysis.
#
# Design notes:
# - Each visual deliverable maps to exactly one renderer.
# - Renderers must be pure functions (image + ROI → styled image).
# - Rendering is decoupled from thumbnail generation and I/O.
#
# Responsibilities of this module:
# - Register visual renderers for each visual deliverable.
# - Serve as the single source of truth for visual rendering selection.
#
# This module does NOT:
# - Execute Earth Engine computations eagerly.
# - Export images or generate files.
# - Define scientific or statistical deliverables.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


from wildfire_analyser.fire_assessment.deliverables import Deliverable
from wildfire_analyser.fire_assessment.visualization.rgb import (
    rgb_pre_fire_visual,
    rgb_post_fire_visual,
)

from wildfire_analyser.fire_assessment.visualization.dnbr import dnbr_visual
from wildfire_analyser.fire_assessment.visualization.rbr import rbr_visual
from wildfire_analyser.fire_assessment.visualization.dndvi import dndvi_visual
from .thumbnails import get_visual_thumbnail_url

VISUAL_RENDERERS = {
    Deliverable.RGB_PRE_FIRE_VISUAL: rgb_pre_fire_visual,
    Deliverable.RGB_POST_FIRE_VISUAL: rgb_post_fire_visual,
    Deliverable.DNDVI_VISUAL: dndvi_visual,
    Deliverable.DNBR_VISUAL: dnbr_visual,
    Deliverable.RBR_VISUAL: rbr_visual,
}

__all__ = [
    "get_visual_thumbnail_url",
]

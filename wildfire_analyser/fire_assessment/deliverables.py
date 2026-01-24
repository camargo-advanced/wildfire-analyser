# SPDX-License-Identifier: MIT
#
# Deliverable definitions for the fire assessment pipeline.
#
# This module defines the canonical set of deliverables supported by the
# wildfire-analyser pipeline. Deliverables represent the public outputs
# that can be requested by users via the CLI or programmatic interfaces.
#
# Deliverables are grouped into three conceptual categories:
#
# - Scientific deliverables:
#   Quantitative analytical products derived from Earth Engine processing,
#   typically exported as GeoTIFF files for further analysis and reuse.
#
# - Statistical deliverables:
#   Aggregated summaries computed from scientific products (e.g. burned
#   area by severity class). These deliverables usually trigger immediate
#   Earth Engine execution via getInfo().
#
# - Visual deliverables:
#   Qualitative representations intended for preview and reporting, such
#   as RGB composites and classified severity maps rendered as thumbnails.
#
# Design notes:
# - This enum defines the public API of the pipeline; adding a new deliverable
#   here makes it addressable by the DAG resolver and CLI.
# - Deliverables are intentionally decoupled from their implementation and
#   dependency graph, which are defined elsewhere.
# - Enumeration values are auto-generated to avoid coupling to serialized
#   representations.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


from enum import Enum, auto


class Deliverable(Enum):
    # ─────────────────────────────
    # Scientific deliverables (GeoTIFF)
    #
    # Quantitative analytical products derived directly from Earth Engine
    # processing. These deliverables represent scientific data intended for
    # export, archival, and downstream quantitative analysis.
    #
    # They are typically materialized as GeoTIFF files and preserve the
    # original numerical values of the computed indices or composites.
    # ─────────────────────────────
    RGB_PRE_FIRE = auto()
    RGB_POST_FIRE = auto()

    NDVI_PRE_FIRE = auto()
    NDVI_POST_FIRE = auto()
    DNDVI = auto()

    NBR_PRE_FIRE = auto()
    NBR_POST_FIRE = auto()
    DNBR = auto()

    RBR = auto()

    # ─────────────────────────────
    # Statistical deliverables
    #
    # Aggregated summaries computed from scientific deliverables, such as
    # burned area by severity class. These deliverables usually trigger
    # immediate Earth Engine execution via getInfo() and return structured
    # numerical results rather than raster data.
    # ─────────────────────────────
    DNBR_AREA_STATISTICS = auto()
    DNDVI_AREA_STATISTICS = auto()
    RBR_AREA_STATISTICS = auto()

    # ─────────────────────────────
    # Visual deliverables (JPEG / Thumbnail)
    #
    # Qualitative representations derived from scientific deliverables.
    # Visual deliverables reuse the same underlying data but differ only in
    # presentation, using color palettes and styling for preview and
    # reporting purposes.
    #
    # These deliverables are not intended for quantitative analysis.
    # ─────────────────────────────
    RGB_PRE_FIRE_VISUAL = auto()
    RGB_POST_FIRE_VISUAL = auto()
    DNDVI_VISUAL = auto()
    DNBR_VISUAL = auto()
    RBR_VISUAL = auto()

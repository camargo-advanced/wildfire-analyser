# SPDX-License-Identifier: MIT
#
# Processing dependency definitions for the fire assessment DAG.
#
# This module defines the internal processing dependencies used to construct
# and execute the fire assessment pipeline as a directed acyclic graph (DAG).
# Each dependency represents a concrete processing step or intermediate
# product within the Earth Engine workflow.
#
# Dependencies are internal execution units and are distinct from public
# deliverables. Multiple deliverables may share the same dependencies to
# ensure consistent reuse of intermediate results and to avoid redundant
# computation.
#
# Design notes:
# - Dependencies model the logical execution graph of the pipeline.
# - Each dependency corresponds to a well-defined processing stage
#   (e.g. collection gathering, mosaic generation, index computation).
# - Dependencies may be reused across scientific, statistical, and visual
#   deliverables.
#
# Responsibilities of this module:
# - Define the canonical set of processing steps in the pipeline.
# - Serve as the internal nodes of the DAG executed by the resolver.
# - Provide a stable contract between deliverables and processing logic.
#
# This module does NOT:
# - Expose user-facing outputs or results.
# - Implement processing logic for any dependency.
# - Perform Earth Engine execution directly.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


from enum import Enum, auto


class Dependency(Enum):
    # ─────────────────────────────────────────────
    # Data ingestion and scene selection
    #
    # Initial gathering of satellite imagery and
    # filtering by date, cloud coverage, and ROI.
    # ─────────────────────────────────────────────
    COLLECTION_GATHERING = auto()

    # ─────────────────────────────────────────────
    # Temporal image collections
    #
    # Pre- and post-fire image collections built
    # from the ingestion step.
    # ─────────────────────────────────────────────
    PRE_FIRE_COLLECTION = auto()
    POST_FIRE_COLLECTION = auto()

    # ─────────────────────────────────────────────
    # Temporal mosaics
    #
    # Cloud-filtered mosaics generated from the
    # pre- and post-fire collections.
    # ─────────────────────────────────────────────
    PRE_FIRE_MOSAIC = auto()
    POST_FIRE_MOSAIC = auto()

    # ─────────────────────────────────────────────
    # RGB composites
    #
    # True-color composites derived from mosaics,
    # primarily for visual inspection.
    # ─────────────────────────────────────────────
    RGB_PRE_FIRE = auto()
    RGB_POST_FIRE = auto()

    # ─────────────────────────────────────────────
    # Spectral indices (continuous values)
    #
    # Burn and vegetation indices computed from
    # pre- and post-fire mosaics.
    # ─────────────────────────────────────────────
    NBR_PRE_FIRE = auto()
    NBR_POST_FIRE = auto()
    DNBR = auto()

    NDVI_PRE_FIRE = auto()
    NDVI_POST_FIRE = auto()
    DNDVI = auto()

    RBR = auto()

    # ─────────────────────────────────────────────
    # Fire severity metrics (aggregated statistics)
    #
    # Area-based summaries derived from classified
    # burn severity indices.
    # ─────────────────────────────────────────────
    DNBR_AREA_STATISTICS = auto()
    DNDVI_AREA_STATISTICS = auto()
    RBR_AREA_STATISTICS = auto()

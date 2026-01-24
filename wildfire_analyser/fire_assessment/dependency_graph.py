# SPDX-License-Identifier: MIT
#
# Dependency graph definition for the fire assessment pipeline.
#
# This module defines the directed acyclic graph (DAG) that governs execution
# order within the fire assessment pipeline. The graph maps each internal
# dependency to the set of dependencies that must be completed beforehand.
#
# Dependencies represent internal processing steps (not user-facing outputs)
# and are executed lazily until a terminal operation is reached.
#
# Design notes:
# - The graph is declarative and free of execution logic.
# - Dependencies are organized to reflect the logical stages of the pipeline:
#   ingestion, collection building, mosaicking, index computation, and
#   statistical aggregation.
# - Multiple downstream steps may reuse the same intermediate dependency
#   to avoid redundant Earth Engine computation.
#
# Responsibilities of this module:
# - Define execution order constraints between processing steps.
# - Serve as the canonical DAG consumed by the resolver.
# - Ensure deterministic and reproducible pipeline execution.
#
# This module does NOT:
# - Execute any Earth Engine operation.
# - Define user-facing deliverables.
# - Perform validation or error handling.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.
#

from wildfire_analyser.fire_assessment.dependencies import Dependency


DEPENDENCY_GRAPH = {
    # ─────────────────────────────────────────────
    # Data ingestion and scene gathering
    #
    # Initial retrieval of satellite imagery and
    # metadata filtering (dates, ROI, cloud cover).
    # ─────────────────────────────────────────────
    Dependency.COLLECTION_GATHERING: set(),

    # ─────────────────────────────────────────────
    # Temporal image collections
    #
    # Pre- and post-fire collections built from
    # the ingestion step.
    # ─────────────────────────────────────────────
    Dependency.PRE_FIRE_COLLECTION: {
        Dependency.COLLECTION_GATHERING,
    },
    Dependency.POST_FIRE_COLLECTION: {
        Dependency.COLLECTION_GATHERING,
    },

    # ─────────────────────────────────────────────
    # Temporal mosaics
    #
    # Cloud-filtered mosaics generated from the
    # corresponding temporal collections.
    # ─────────────────────────────────────────────
    Dependency.PRE_FIRE_MOSAIC: {
        Dependency.PRE_FIRE_COLLECTION,
    },
    Dependency.POST_FIRE_MOSAIC: {
        Dependency.POST_FIRE_COLLECTION,
    },

    # ─────────────────────────────────────────────
    # RGB composites
    #
    # True-color composites derived from mosaics,
    # primarily intended for visual inspection.
    # ─────────────────────────────────────────────
    Dependency.RGB_PRE_FIRE: {
        Dependency.PRE_FIRE_MOSAIC,
    },
    Dependency.RGB_POST_FIRE: {
        Dependency.POST_FIRE_MOSAIC,
    },

    # ─────────────────────────────────────────────
    # NDVI-based indices
    #
    # Vegetation condition indices computed from
    # pre- and post-fire mosaics.
    # ─────────────────────────────────────────────
    Dependency.NDVI_PRE_FIRE: {
        Dependency.PRE_FIRE_MOSAIC,
    },
    Dependency.NDVI_POST_FIRE: {
        Dependency.POST_FIRE_MOSAIC,
    },
    Dependency.DNDVI: {
        Dependency.NDVI_PRE_FIRE,
        Dependency.NDVI_POST_FIRE,
    },

    # ─────────────────────────────────────────────
    # NBR-based indices
    #
    # Burn severity indices computed from
    # pre- and post-fire mosaics.
    # ─────────────────────────────────────────────
    Dependency.NBR_PRE_FIRE: {
        Dependency.PRE_FIRE_MOSAIC,
    },
    Dependency.NBR_POST_FIRE: {
        Dependency.POST_FIRE_MOSAIC,
    },
    Dependency.DNBR: {
        Dependency.NBR_PRE_FIRE,
        Dependency.NBR_POST_FIRE,
    },

    # ─────────────────────────────────────────────
    # Fire severity indices
    #
    # Derived indices that combine or normalize
    # burn-related metrics.
    # ─────────────────────────────────────────────
    Dependency.RBR: {
        Dependency.DNBR,
        Dependency.NBR_PRE_FIRE,
    },

    # ─────────────────────────────────────────────
    # Fire severity statistics
    #
    # Area-based summaries derived from classified
    # burn severity indices.
    # ─────────────────────────────────────────────
    Dependency.DNBR_AREA_STATISTICS: {
        Dependency.DNBR,
    },
    Dependency.DNDVI_AREA_STATISTICS: {
        Dependency.DNDVI,
    },
    Dependency.RBR_AREA_STATISTICS: {
        Dependency.RBR,
    },
}

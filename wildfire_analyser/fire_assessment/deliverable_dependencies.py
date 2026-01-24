# SPDX-License-Identifier: MIT
#
# Deliverable-to-dependency mapping for the fire assessment DAG.
#
# This module defines the explicit dependency graph between high-level
# deliverables and their underlying processing steps. Each deliverable
# declares the minimal set of dependencies required for its computation,
# enabling deterministic and reproducible DAG execution.
#
# Design notes:
# - Dependencies are expressed declaratively using enums to avoid implicit
#   coupling between deliverables and processing logic.
# - Visual deliverables reuse the same scientific dependencies as their
#   corresponding analytical products, differing only in representation.
# - This mapping is consumed by the DAG resolver to determine execution
#   order and to avoid redundant computation.
#
# Responsibilities of this module:
# - Define the dependency contract for each supported deliverable.
# - Serve as the single source of truth for DAG construction.
# - Ensure consistent reuse of intermediate products across deliverables.
#
# This module does NOT:
# - Implement processing logic for any dependency.
# - Execute Earth Engine operations directly.
# - Perform validation or error handling.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


from wildfire_analyser.fire_assessment.deliverables import Deliverable
from wildfire_analyser.fire_assessment.dependencies import Dependency

DELIVERABLE_DEPENDENCIES = {
    # ------------------------------------------------------------------
    # Scientific deliverables (raw analytical products)
    #
    # These deliverables represent scientific outputs derived directly
    # from Earth Engine processing. They are intended for quantitative
    # analysis, export, and downstream reuse.
    # ------------------------------------------------------------------

    Deliverable.RGB_PRE_FIRE: {Dependency.RGB_PRE_FIRE},
    Deliverable.RGB_POST_FIRE: {Dependency.RGB_POST_FIRE},

    Deliverable.NDVI_PRE_FIRE: {Dependency.NDVI_PRE_FIRE},
    Deliverable.NDVI_POST_FIRE: {Dependency.NDVI_POST_FIRE},
    Deliverable.DNDVI: {Dependency.DNDVI},

    Deliverable.NBR_PRE_FIRE: {Dependency.NBR_PRE_FIRE},
    Deliverable.NBR_POST_FIRE: {Dependency.NBR_POST_FIRE},
    Deliverable.DNBR: {Dependency.DNBR},
    Deliverable.RBR: {Dependency.RBR},

    # ------------------------------------------------------------------
    # Statistical deliverables (derived summaries)
    #
    # These deliverables perform statistical aggregation over scientific
    # products (e.g. area by severity class). They typically trigger
    # immediate Earth Engine execution via getInfo().
    # ------------------------------------------------------------------

    Deliverable.DNBR_AREA_STATISTICS: {Dependency.DNBR_AREA_STATISTICS},
    Deliverable.DNDVI_AREA_STATISTICS: {Dependency.DNDVI_AREA_STATISTICS},
    Deliverable.RBR_AREA_STATISTICS: {Dependency.RBR_AREA_STATISTICS},

    # ------------------------------------------------------------------
    # Visual deliverables (qualitative representations)
    #
    # Visual deliverables reuse the same scientific dependencies as their
    # analytical counterparts but differ only in representation. They are
    # intended for preview, reporting, and qualitative inspection.
    # ------------------------------------------------------------------

    Deliverable.RGB_PRE_FIRE_VISUAL: {Dependency.RGB_PRE_FIRE},
    Deliverable.RGB_POST_FIRE_VISUAL: {Dependency.RGB_POST_FIRE},
    Deliverable.DNDVI_VISUAL: {Dependency.DNDVI},
    Deliverable.RBR_VISUAL: {Dependency.RBR},
    Deliverable.DNBR_VISUAL: {Dependency.DNBR},
}

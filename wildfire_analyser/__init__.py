# SPDX-License-Identifier: MIT
#
# Public API exports for the fire assessment module.
#
# This module defines the public-facing symbols exposed by the
# fire_assessment package. It acts as a controlled interface layer,
# re-exporting selected enums, utilities, and helper functions that are
# intended for external consumption.
#
# Design notes:
# - Only stable, documented components should be exported here.
# - Internal implementation details are intentionally excluded.
# - This file defines the conceptual boundary between the internal
#   pipeline architecture and external users of the library.
#
# Responsibilities of this module:
# - Expose the canonical public API of fire_assessment.
# - Provide a single import point for commonly used symbols.
#
# This module does NOT:
# - Implement processing logic or pipeline execution.
# - Define dependency relationships or DAG behavior.
# - Perform authentication or I/O directly.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


from wildfire_analyser.fire_assessment.deliverables import Deliverable
from wildfire_analyser.fire_assessment.dependencies import Dependency


__all__ = [
    "Deliverable",
    "Dependency",
]

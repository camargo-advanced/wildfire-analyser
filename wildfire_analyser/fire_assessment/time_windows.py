# SPDX-License-Identifier: MIT
#
# Date and time window utilities for fire assessment workflows.
#
# This module provides helper functions for computing temporal windows
# used throughout the fire assessment pipeline. It encapsulates all
# date arithmetic required to derive pre-fire and post-fire analysis
# periods from user-supplied event dates.
#
# Design notes:
# - Time windows are computed inclusively to avoid off-by-one errors.
# - Buffer periods are applied symmetrically around the event interval.
# - All dates are normalized to ISO 8601 (YYYY-MM-DD) string format.
#
# Responsibilities of this module:
# - Compute analysis time windows relative to fire events.
# - Centralize date arithmetic logic used by collection builders.
#
# This module does NOT:
# - Perform any Earth Engine operations.
# - Validate user input beyond basic date parsing.
# - Define processing dependencies or deliverables.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def compute_fire_time_windows(
    start_date: str,
    end_date: str,
    buffer_days: int,
) -> tuple[str, str, str, str]:
    sd = datetime.strptime(start_date, "%Y-%m-%d")
    ed = datetime.strptime(end_date, "%Y-%m-%d")

    before_start = (sd - timedelta(days=buffer_days)).strftime("%Y-%m-%d")
    before_end = (sd + timedelta(days=1)).strftime("%Y-%m-%d")  # INCLUI sd

    after_start = ed.strftime("%Y-%m-%d")
    after_end = (ed + timedelta(days=buffer_days + 1)
                 ).strftime("%Y-%m-%d")  # INCLUI ed

    return before_start, before_end, after_start, after_end

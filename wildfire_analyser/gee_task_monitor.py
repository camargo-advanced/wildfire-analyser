# SPDX-License-Identifier: MIT
#
# Google Earth Engine task monitoring CLI.
#
# This module implements a lightweight command-line utility for monitoring
# asynchronous Google Earth Engine (GEE) tasks, such as image exports, until
# completion.
#
# It is intended to be used as a companion tool to the main wildfire-analyser
# pipeline, allowing users to track long-running Earth Engine jobs executed
# outside the interactive CLI flow.
#
# Design notes:
# - This module operates purely as a polling client for GEE task status.
# - It does not submit, cancel, or modify Earth Engine tasks.
# - Polling is performed at a fixed interval to balance responsiveness
#   and API usage.
#
# Responsibilities of this module:
# - Authenticate with Google Earth Engine.
# - Poll task status until completion or failure.
# - Report task state transitions to the user.
#
# This module does NOT:
# - Execute scientific processing or pipeline logic.
# - Interact with Google Cloud Storage directly.
# - Send notifications or emails (future extension).
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


import argparse
import time
import ee

from wildfire_analyser.fire_assessment.auth import authenticate_gee

POLL_INTERVAL_SECONDS = 15


def wait_for_task(gee_task_id: str):
    while True:
        statuses = ee.data.getTaskStatus(gee_task_id)

        if not statuses:
            raise RuntimeError(f"Task {gee_task_id} not found")

        status = statuses[0]
        state = status["state"]

        print(f"[GEE] task={gee_task_id} state={state}")

        if state == "COMPLETED":
            return

        if state in ("FAILED", "CANCELLED"):
            error = status.get("error_message", "Unknown error")
            raise RuntimeError(f"Task failed: {error}")

        time.sleep(POLL_INTERVAL_SECONDS)


def main():
    parser = argparse.ArgumentParser(
        description="Monitor a Google Earth Engine task until completion"
    )
    parser.add_argument("--gee-task-id", required=True)
    args = parser.parse_args()

    authenticate_gee()
    wait_for_task(args.gee_task_id)
    print(f"Deliverable '{args.deliverable}' completed.")


if __name__ == "__main__":
    main()

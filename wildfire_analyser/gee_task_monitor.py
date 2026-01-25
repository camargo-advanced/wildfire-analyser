# SPDX-License-Identifier: MIT
#
# Google Earth Engine (GEE) task monitoring utility.
#
# This module provides a small command-line utility to monitor the execution
# state of a Google Earth Engine task until it completes, fails, or is cancelled.
#
# It is intended to be used in automated workflows where GEE export tasks
# (e.g. Export.image.toCloudStorage) are triggered asynchronously and their
# completion must be tracked before proceeding to the next pipeline step.
#
# Design notes:
# - Authentication is handled via a service account JSON provided through
#   the GEE_PRIVATE_KEY_JSON environment variable.
# - Task monitoring uses ee.data.getTaskStatus and assumes a single task ID.
# - Polling is time-based and does not rely on callbacks or webhooks.
#
# Responsibilities of this module:
# - Authenticate against Google Earth Engine using non-interactive credentials.
# - Monitor the lifecycle of a single GEE task.
# - Provide a simple CLI interface for integration into scripts and pipelines.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.

import argparse
import json
import os
import sys
import time
import ee
from dotenv import load_dotenv

POLL_INTERVAL_SECONDS = 15

ERROR_MSG = (
    "ERROR: Unable to monitor the Google Earth Engine task.\n"
    "Please check your GEE credentials and the provided task ID, then try again."
)

SUCCESS_MSG = (
    "\nSUCCESS: Google Earth Engine task completed successfully.\n"
)


def init_gee() -> None:
    load_dotenv()

    gee_key_json = os.getenv("GEE_PRIVATE_KEY_JSON")
    if not gee_key_json:
        raise RuntimeError("GEE_PRIVATE_KEY_JSON not set")

    key_dict = json.loads(gee_key_json)

    credentials = ee.ServiceAccountCredentials(
        key_dict["client_email"],
        key_data=json.dumps(key_dict),
    )

    ee.Initialize(credentials)


def wait_for_task(gee_task_id: str) -> None:
    while True:
        statuses = ee.data.getTaskStatus(gee_task_id)

        if not statuses:
            raise RuntimeError(f"Task '{gee_task_id}' not found")

        status = statuses[0]
        state = status.get("state")

        print(f"[GEE] task={gee_task_id} state={state}")

        if state == "COMPLETED":
            return

        if state in ("FAILED", "CANCELLED"):
            error = status.get("error_message", "Unknown error")
            raise RuntimeError(f"Task failed: {error}")

        time.sleep(POLL_INTERVAL_SECONDS)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Monitor a Google Earth Engine task until completion"
    )
    parser.add_argument("--gee-task-id", required=True)
    args = parser.parse_args()

    init_gee()

    wait_for_task(args.gee_task_id)

    print(SUCCESS_MSG)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(ERROR_MSG, file=sys.stderr)
        sys.exit(2)

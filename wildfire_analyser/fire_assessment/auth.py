# SPDX-License-Identifier: MIT
#
# Google Earth Engine authentication helpers.
#
# This module provides authentication utilities for initializing access to
# Google Earth Engine (GEE) using a service account. Credentials are loaded
# from environment variables to support non-interactive execution in CLI,
# batch, and server environments.
#
# Design notes:
# - Authentication is performed using a service account JSON key provided
#   via the GEE_PRIVATE_KEY_JSON environment variable.
# - The service account key is written to a temporary file only for the
#   duration required by the Earth Engine client library.
# - This module intentionally avoids interactive authentication flows
#   (e.g., OAuth browser login).
#
# Responsibilities of this module:
# - Load environment variables from an optional .env file.
# - Validate and parse the service account JSON credentials.
# - Initialize the Earth Engine client with service account credentials.
#
# This module does NOT:
# - Manage Google Cloud IAM permissions.
# - Register or configure GCP projects for Earth Engine usage.
# - Perform any Earth Engine computation or data access beyond initialization.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


import ee
import os
import json
from dotenv import load_dotenv
from tempfile import NamedTemporaryFile


def authenticate_gee(gee_key_json: str | None = None) -> None:
    """
    Authenticate Google Earth Engine using a service account JSON
    stored in the GEE_PRIVATE_KEY_JSON environment variable.
    """

    try:
        key_dict = json.loads(gee_key_json)
    except json.JSONDecodeError as e:
        raise ValueError("Invalid GEE_PRIVATE_KEY_JSON format") from e

    try:
        with NamedTemporaryFile(mode="w+", suffix=".json") as f:
            json.dump(key_dict, f)
            f.flush()
            credentials = ee.ServiceAccountCredentials(
                key_dict["client_email"], f.name
            )
            ee.Initialize(credentials)
    except Exception as e:
        raise RuntimeError(
            "Failed to authenticate with Google Earth Engine") from e

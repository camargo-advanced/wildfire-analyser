# SPDX-License-Identifier: MIT
#
# Google Cloud Storage (GCS) export helpers for Earth Engine products.
#
# This module provides helper functions to export Earth Engine images as
# persistent artifacts to Google Cloud Storage. Exports are submitted as
# asynchronous Earth Engine tasks and return immediately after task creation.
#
# Design notes:
# - Earth Engine execution is triggered when the export task is started.
# - Export operations are asynchronous; completion must be monitored
#   separately via the Earth Engine task API or console.
# - This module is intentionally limited to storage concerns and does not
#   perform scientific processing or visualization logic.
#
# Responsibilities of this module:
# - Submit GeoTIFF export tasks to Google Cloud Storage.
# - Define export parameters (region, scale, maxPixels, format).
# - Return stable references (GCS URL and task ID) for downstream consumers.
#
# This module does NOT:
# - Validate scientific correctness of the image.
# - Perform visualization or thumbnail generation.
# - Block execution waiting for task completion.
#
# Copyright (C) 2025
# Marcelo Camargo
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


import ee


def export_geotiff_to_gcs(
    image: ee.Image,
    roi: ee.Geometry,
    bucket: str,
    object_name: str,
    scale: int
) -> dict:
    task = ee.batch.Export.image.toCloudStorage(
        image=image,
        description=object_name,
        bucket=bucket,
        fileNamePrefix=object_name,
        region=roi,
        scale=scale,
        maxPixels=1e13,
        fileFormat="GeoTIFF",
    )
    task.start()

    return {
        "url": f"https://storage.googleapis.com/{bucket}/{object_name}.tif",
        "gee_task_id": task.id,
    }

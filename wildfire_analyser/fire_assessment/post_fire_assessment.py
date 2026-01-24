# SPDX-License-Identifier: MIT
#
# Post-fire assessment pipeline orchestration.
#
# This module implements the high-level orchestration logic for post-fire
# assessment workflows using Google Earth Engine (GEE). It coordinates the
# execution of a dependency-based processing DAG, collects scientific,
# statistical, and visualization deliverables, and exposes results in a
# structured form suitable for CLI and programmatic use.
#
# Responsibilities of this module:
# - Authenticate and initialize Earth Engine access.
# - Validate user inputs (dates, ROI).
# - Execute the processing DAG for requested deliverables.
# - Dispatch results to visualization, statistics, or export paths.
# - Aggregate provenance metadata for traceability.
#
# This module does NOT:
# - Implement scientific algorithms (see products.py).
# - Perform visualization rendering logic (see visualization/).
# - Handle storage backends beyond dispatching exports.
#
# Copyright (C) 2025
# Marcelo Camargo
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.
 

import ee
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, date
import uuid

from wildfire_analyser.fire_assessment.auth import authenticate_gee
from wildfire_analyser.fire_assessment.resolver import (
    DAGExecutionContext,
    execute_dag,
)
from wildfire_analyser.fire_assessment.deliverables import Deliverable
from wildfire_analyser.fire_assessment.visualization import VISUAL_RENDERERS
from wildfire_analyser.fire_assessment.exporters.gcs import (
    export_geotiff_to_gcs,
)
from wildfire_analyser.fire_assessment.visualization import (
    get_visual_thumbnail_url,
)
from wildfire_analyser.fire_assessment.dependencies import Dependency

import logging


class PostFireAssessment:

    DEFAULT_SCALE = 10

    def __init__(
        self,
        gee_key_json: str,
        geojson_path: str,
        start_date: str,
        end_date: str,
        deliverables: List[Deliverable],
        cloud_threshold: int = 70,
        days_before_after: int = 30,
        gcs_bucket: str | None = None,
        verbose: bool = False,
    ):
        level = logging.INFO if verbose else logging.WARNING
        logging.getLogger("wildfire_analyser").setLevel(level)

        authenticate_gee(gee_key_json)

        start = self._parse_date(start_date, "start_date")
        end = self._parse_date(end_date, "end_date")
        if start > end:
            raise ValueError(
                f"start_date must be <= end_date "
                f"(got {start_date} > {end_date})"
            )

        self.roi = self._load_geojson(Path(geojson_path))
        self.deliverables = deliverables
        self.bucket = gcs_bucket

        self.context = DAGExecutionContext(
            roi=self.roi,
            start_date=start_date,
            end_date=end_date,
            cloud_threshold=cloud_threshold,
            days_before_after=days_before_after,
        )

    def run(self) -> Dict[str, Any]:
        outputs = execute_dag(self.deliverables, self.context)

        result = {
            "scientific": {},
            "visual": {},
            "statistics": {},
            "provenance": {},
        }

        for d, value in outputs.items():

            if d.name.endswith("_AREA_STATISTICS"):
                result["statistics"][d.name] = value
                continue

            if d in VISUAL_RENDERERS:
                vis = VISUAL_RENDERERS[d](value, self.roi)
                result["visual"][d.name] = {
                    "url": get_visual_thumbnail_url(vis, self.roi)
                }
                continue

            if self.bucket:
                object_name = self._generate_object_name(
                    deliverable=d.name.lower(),
                    start_date=self.context.inputs["start_date"],
                    end_date=self.context.inputs["end_date"],
                )

                export_result = export_geotiff_to_gcs(
                    image=value,
                    roi=self.roi,
                    bucket=self.bucket,
                    object_name=object_name,
                    scale=self.DEFAULT_SCALE,
                )

                result["scientific"][d.name] = {
                    "url": export_result["url"],
                    "gee_task_id": export_result["gee_task_id"],
                }

        # Provenance (image IDs, dates, cloud %)
        pre_collection = self.context.get(Dependency.PRE_FIRE_COLLECTION)
        post_collection = self.context.get(Dependency.POST_FIRE_COLLECTION)

        result["provenance"] = {
            "pre_fire": {
                "images": self._extract_collection_provenance(pre_collection)
                if pre_collection is not None else []
            },
            "post_fire": {
                "images": self._extract_collection_provenance(post_collection)
                if post_collection is not None else []
            },
        }

        return result

    @staticmethod
    def _load_geojson(path: Path) -> ee.Geometry:
        import json
        with open(path) as f:
            geojson = json.load(f)
        return ee.Geometry(geojson["features"][0]["geometry"])
    
    @staticmethod
    def _generate_object_name(
        deliverable: str,
        start_date: str,
        end_date: str,
    ) -> str:
        """
        Generate a unique object name for exports.
        """
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        uid = uuid.uuid4().hex[:8]

        start_norm = start_date.replace("-", "_")
        end_norm = end_date.replace("-", "_")

        return f"{deliverable}_{start_norm}_{end_norm}_{ts}_{uid}"
        
    @staticmethod
    def _parse_date(value: str, field_name: str) -> date:
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValueError(
                f"{field_name} must be in YYYY-MM-DD format (got '{value}')"
            ) from e

    @staticmethod
    def _extract_collection_provenance(
        collection: ee.ImageCollection,
    ) -> List[Dict[str, Any]]:
        """
        Extract ordered image provenance from an ImageCollection.

        The order reflects the ImageCollection internal ordering
        (i.e., sorted by CLOUDY_PIXEL_PERCENTAGE).
        """
        def to_feature(img):
            return ee.Feature(
                None,
                {
                    "id": img.get("system:id"),
                    "date": ee.Date(
                        img.get("system:time_start")
                    ).format("YYYY-MM-dd"),
                    "cloud_percent": img.get("CLOUDY_PIXEL_PERCENTAGE"),
                },
            )

        feature_collection = ee.FeatureCollection(collection.map(to_feature))
        features = feature_collection.getInfo()["features"]

        return [f["properties"] for f in features]

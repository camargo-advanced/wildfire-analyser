# SPDX-License-Identifier: MIT
#
# Processing node implementations for the fire assessment pipeline.
#
# This module defines the concrete execution logic for each internal pipeline
# dependency. Each function registered here represents a processing node in
# the dependency graph and corresponds to a single, well-defined computation
# step executed on Google Earth Engine.
#
# Nodes are registered via the @register decorator and are executed lazily
# according to the dependency resolution performed by the DAG resolver.
#
# Design notes:
# - Each node consumes inputs from the DAG execution context.
# - Nodes must be deterministic and free of side effects.
# - Earth Engine execution is deferred until a terminal operation
#   (e.g. getInfo(), export, or thumbnail generation) is triggered.
#
# Responsibilities of this module:
# - Implement all pipeline processing steps.
# - Register execution functions for each Dependency.
# - Encapsulate Earth Engine computation logic.
#
# This module does NOT:
# - Define dependency relationships (see dependency_graph.py).
# - Define user-facing deliverables (see deliverables.py).
# - Control execution order or scheduling.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


from typing import Callable, Dict, Any
import ee

from wildfire_analyser.fire_assessment.dependencies import Dependency
from wildfire_analyser.fire_assessment.time_windows import compute_fire_time_windows
from wildfire_analyser.fire_assessment.sentinel2 import gather_collection

ProductExecutor = Callable[[Any], Any]
PRODUCT_REGISTRY: Dict[Dependency, ProductExecutor] = {}


def register(dep: Dependency):
    def decorator(func: ProductExecutor):
        PRODUCT_REGISTRY[dep] = func
        return func
    return decorator


# ─────────────────────────────
# Stage 1 – Collection ingestion
# ─────────────────────────────

@register(Dependency.COLLECTION_GATHERING)
def gather_collection_node(context):
    roi = context.inputs["roi"]
    cloud_threshold = context.inputs.get("cloud_threshold")

    return gather_collection(
        roi=roi,
        cloud_threshold=cloud_threshold,
    )


@register(Dependency.PRE_FIRE_COLLECTION)
def build_pre_fire_collection(context):
    collection = context.get(Dependency.COLLECTION_GATHERING)
    if collection is None:
        raise RuntimeError("COLLECTION_GATHERING not available")

    start_date = context.inputs["start_date"]
    end_date = context.inputs["end_date"]
    days = context.inputs.get("days_before_after")

    before_start, before_end, _, _ = compute_fire_time_windows(
        start_date, end_date, days
    )

    return collection.filterDate(before_start, before_end)


@register(Dependency.POST_FIRE_COLLECTION)
def build_post_fire_collection(context):
    collection = context.get(Dependency.COLLECTION_GATHERING)
    if collection is None:
        raise RuntimeError("COLLECTION_GATHERING not available")

    start_date = context.inputs["start_date"]
    end_date = context.inputs["end_date"]
    days = context.inputs.get("days_before_after")

    _, _, after_start, after_end = compute_fire_time_windows(
        start_date, end_date, days
    )

    return collection.filterDate(after_start, after_end)


# ─────────────────────────────
# Stage 1 – Mosaics
# ─────────────────────────────

@register(Dependency.PRE_FIRE_MOSAIC)
def build_pre_fire_mosaic(context):
    pre_collection = context.get(Dependency.PRE_FIRE_COLLECTION)
    if pre_collection is None:
        raise RuntimeError("PRE_FIRE_COLLECTION not available")

    return pre_collection.mosaic()


@register(Dependency.POST_FIRE_MOSAIC)
def build_post_fire_mosaic(context):
    post_collection = context.get(Dependency.POST_FIRE_COLLECTION)
    if post_collection is None:
        raise RuntimeError("POST_FIRE_COLLECTION not available")

    return post_collection.mosaic()


@register(Dependency.RGB_PRE_FIRE)
def build_rgb_pre_fire(context):
    """
    Build RGB composite from the pre-fire mosaic.
    """
    mosaic = context.get(Dependency.PRE_FIRE_MOSAIC)
    if mosaic is None:
        raise RuntimeError("PRE_FIRE_MOSAIC not available in DAG context")

    rgb = mosaic.select(
        ["B4_refl", "B3_refl", "B2_refl"],
        ["red", "green", "blue"],
    )

    return rgb


@register(Dependency.RGB_POST_FIRE)
def build_rgb_post_fire(context):
    mosaic = context.get(Dependency.POST_FIRE_MOSAIC)
    if mosaic is None:
        raise RuntimeError("POST_FIRE_MOSAIC not available in DAG context")

    rgb = mosaic.select(
        ["B4_refl", "B3_refl", "B2_refl"],
        ["red", "green", "blue"],
    )

    return rgb


# ─────────────────────────────
# Stage 2 – NDVI
# ─────────────────────────────

@register(Dependency.NDVI_PRE_FIRE)
def compute_ndvi_pre(context):
    pre_fire = context.get(Dependency.PRE_FIRE_MOSAIC)
    if pre_fire is None:
        raise RuntimeError("PRE_FIRE_MOSAIC not available")

    return pre_fire.normalizedDifference(
        ["B8_refl", "B4_refl"]
    ).rename("ndvi")


@register(Dependency.NDVI_POST_FIRE)
def compute_ndvi_post(context):
    post_fire = context.get(Dependency.POST_FIRE_MOSAIC)
    if post_fire is None:
        raise RuntimeError("POST_FIRE_MOSAIC not available")

    return post_fire.normalizedDifference(
        ["B8_refl", "B4_refl"]
    ).rename("ndvi")


@register(Dependency.DNDVI)
def compute_dndvi(context):
    """
    Compute differenced NDVI (dNDVI).

    dNDVI = NDVI_pre - NDVI_post
    """
    ndvi_pre = context.get(Dependency.NDVI_PRE_FIRE)
    ndvi_post = context.get(Dependency.NDVI_POST_FIRE)

    if ndvi_pre is None or ndvi_post is None:
        raise RuntimeError("NDVI_PRE_FIRE or NDVI_POST_FIRE not available")

    return ndvi_pre.subtract(ndvi_post).rename("dndvi")


# ─────────────────────────────
# Stage 2 – NBR
# ─────────────────────────────

@register(Dependency.NBR_PRE_FIRE)
def compute_nbr_pre_fire(context):
    """
    Compute NBR from the pre-fire mosaic.
    """
    pre_fire = context.get(Dependency.PRE_FIRE_MOSAIC)
    if pre_fire is None:
        raise RuntimeError("PRE_FIRE_MOSAIC not available")

    nbr = pre_fire.normalizedDifference(
        ["B8_refl", "B12_refl"]
    ).rename("nbr")

    return nbr


@register(Dependency.NBR_POST_FIRE)
def compute_nbr_post_fire(context):
    """
    Compute NBR from the post-fire mosaic.
    """
    post_fire = context.get(Dependency.POST_FIRE_MOSAIC)
    if post_fire is None:
        raise RuntimeError("POST_FIRE_MOSAIC not available")

    nbr = post_fire.normalizedDifference(
        ["B8_refl", "B12_refl"]
    ).rename("nbr")

    return nbr

# ─────────────────────────────
# Stage 3 – DNBR
# ─────────────────────────────


@register(Dependency.DNBR)
def compute_dnbr(context):
    """
    Compute differenced Normalized Burn Ratio (dNBR).
    dNBR = NBR_pre - NBR_post
    """
    nbr_pre = context.get(Dependency.NBR_PRE_FIRE)
    nbr_post = context.get(Dependency.NBR_POST_FIRE)

    if nbr_pre is None or nbr_post is None:
        raise RuntimeError("NBR_PRE_FIRE or NBR_POST_FIRE not available")

    dnbr = nbr_pre.subtract(nbr_post).rename("dnbr")

    return dnbr

# ─────────────────────────────
# Stage 4 – RBR
# ─────────────────────────────


@register(Dependency.RBR)
def compute_rbr(context):
    """
    Compute Relative Burn Ratio (RBR).

    RBR = dNBR / sqrt(|NBR_pre|)
    """
    dnbr = context.get(Dependency.DNBR)
    nbr_pre = context.get(Dependency.NBR_PRE_FIRE)

    if dnbr is None or nbr_pre is None:
        raise RuntimeError("DNBR or NBR_PRE_FIRE not available")

    rbr = dnbr.divide(
        nbr_pre.add(1.001)
    ).rename("rbr")

    return rbr

# ─────────────────────────────
# Stage 5 – STATISTICS
# ─────────────────────────────


SEVERITY_LABELS = {
    0: "Unburned",
    1: "Low Severity",
    2: "Moderate Severity",
    3: "High Severity",
    4: "Very High Severity",
}


def format_area_statistics(stats):
    """
    Convert EE grouped reduce output into paper-ready statistics.
    """
    total_area = sum(item["sum"] for item in stats)
    burned_area = sum(
        item["sum"] for item in stats if item["severity_class"] > 0
    )

    result = {}

    for item in stats:
        label = SEVERITY_LABELS[item["severity_class"]]
        area = item["sum"]
        ratio = (area / total_area) * 100 if total_area > 0 else 0

        result[label] = {
            "area_ha": round(area, 2),
            "ratio_percent": round(ratio, 2),
        }

    result["Total Burned Area"] = {
        "area_ha": round(burned_area, 2),
        "ratio_percent": round((burned_area / total_area) * 100, 2),
    }

    result["Total Area"] = {
        "area_ha": round(total_area, 2),
        "ratio_percent": 100.0,
    }

    return result


def compute_area_stats(severity: ee.Image, roi: ee.Geometry):
    pixel_area = ee.Image.pixelArea().divide(10_000)  # m² → ha

    reducer = ee.Reducer.sum().group(
        groupField=1,
        groupName="severity_class",
    )

    stats = (
        pixel_area
        .addBands(severity)
        .reduceRegion(
            reducer=reducer,
            geometry=roi,
            scale=10,
            maxPixels=1e13,
        )
        .get("groups")
    )

    stats = ee.List(stats).getInfo()

    return format_area_statistics(stats)


@register(Dependency.DNBR_AREA_STATISTICS)
def compute_dnbr_area_statistics(context):
    dnbr = context.get(Dependency.DNBR)
    roi = context.inputs["roi"]

    if dnbr is None:
        raise RuntimeError("DNBR not available")

    severity = (
        ee.Image(0)
        .where(dnbr.gte(0.10).And(dnbr.lt(0.27)), 1)
        .where(dnbr.gte(0.27).And(dnbr.lt(0.44)), 2)
        .where(dnbr.gte(0.44).And(dnbr.lt(0.66)), 3)
        .where(dnbr.gte(0.66), 4)
        .rename("severity")
        .toInt8()
    )

    return compute_area_stats(severity, roi)


@register(Dependency.DNDVI_AREA_STATISTICS)
def compute_dndvi_area_statistics(context):
    dndvi = context.get(Dependency.DNDVI)
    roi = context.inputs["roi"]

    if dndvi is None:
        raise RuntimeError("DNDVI not available")

    severity = (
        ee.Image(0)  # Unburned: dNDVI < 0.07
        .where(dndvi.gte(0.07).And(dndvi.lt(0.10)), 1)   # Low
        .where(dndvi.gte(0.10).And(dndvi.lt(0.20)), 1)  # Low
        .where(dndvi.gte(0.20).And(dndvi.lt(0.33)), 2)  # Moderate
        .where(dndvi.gte(0.33).And(dndvi.lt(0.44)), 3)  # High
        .where(dndvi.gte(0.45), 4)                      # Very High
    )

    return compute_area_stats(severity, roi)


@register(Dependency.RBR_AREA_STATISTICS)
def compute_rbr_area_statistics(context):
    rbr = context.get(Dependency.RBR)
    roi = context.inputs["roi"]

    if rbr is None:
        raise RuntimeError("RBR not available")

    severity = (
        ee.Image(0)
        .where(rbr.gte(0.10).And(rbr.lt(0.27)), 1)
        .where(rbr.gte(0.27).And(rbr.lt(0.44)), 2)
        .where(rbr.gte(0.44).And(rbr.lt(0.66)), 3)
        .where(rbr.gte(0.66), 4)
        .rename("severity")
        .toInt8()
    )

    return compute_area_stats(severity, roi)

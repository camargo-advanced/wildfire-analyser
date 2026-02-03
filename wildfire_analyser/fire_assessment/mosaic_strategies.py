# SPDX-License-Identifier: MIT
#
# Mosaic strategy implementations.
#
# Mosaic strategy implementations.
#
# This module defines alternative compositing strategies for combining
# multiple satellite acquisitions into a single analysis-ready image.
#
# Each strategy represents a distinct decision policy for resolving
# clouds, overlapping scenes, and temporal redundancy.
#
# The processing pipeline delegates all compositing decisions to this
# module, keeping higher-level code policy-agnostic.
#
# Copyright (C) 2025
# Marcelo Camargo.


import ee


def apply_mosaic_strategy(
    collection: ee.ImageCollection,
    strategy: str,
    context,
) -> ee.Image:
    """
    Dispatch to a compositing strategy based on a named decision rule.
    """

    if strategy == "scene_mosaic_cloud_sorted":
        return _scene_mosaic_cloud_sorted(collection, context)
    
    if strategy == "best_scene_selection":
        return _best_scene_selection(collection, context)
    
    if strategy == "pixel_quality":
        return _pixel_quality(collection, context)

    if strategy == "pixel_quality_cloud_penalized":
        return _pixel_quality_cloud_penalized(collection, context)
    
    if strategy == "pixel_quality_hybrid_fallback":
        return _pixel_quality_hybrid_fallback(collection, context)

    raise ValueError(f"Unknown mosaic strategy: {strategy}")


def _scene_mosaic_cloud_sorted(
    collection: ee.ImageCollection,
    context,
) -> ee.Image:
    """
    Prefer pixels from less cloudy scenes, falling back to more
    cloudy scenes only where necessary to fill gaps.
    """
    
    cloud_threshold = context.inputs.get("cloud_threshold")
    
    return (
        collection
        .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", cloud_threshold))
        .sort("CLOUDY_PIXEL_PERCENTAGE", False)
        .mosaic()
    )

def _best_scene_selection(
    collection: ee.ImageCollection,
    context,
) -> ee.Image:
    """
    Use a single acquisition, chosen as the least cloudy scene
    within the analysis period.
    """

    cloud_threshold = context.inputs.get("cloud_threshold")

    return (
        collection
        .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", cloud_threshold))
        .sort("CLOUDY_PIXEL_PERCENTAGE", True)
        .limit(1)
        .mosaic()
    )

def _pixel_quality(
    collection: ee.ImageCollection,
    context,
) -> ee.Image:
    """
    For each pixel location, select the locally clearest observation
    based solely on per-pixel cloud information.
    """

    def add_quality_band(image):
        qa = image.select("QA60")

        cloud = qa.bitwiseAnd(1 << 10).neq(0)
        cirrus = qa.bitwiseAnd(1 << 11).neq(0)

        quality = (
            ee.Image(1.0)
            .where(cirrus.And(cloud.Not()), 0.6)
            .where(cloud.And(cirrus.Not()), 0.2)
            .where(cloud.And(cirrus), 0.0)
            .rename("quality")
        )

        return image.addBands(quality)

    return (
        collection
        .sort("CLOUDY_PIXEL_PERCENTAGE", False)
        .map(add_quality_band)
        .qualityMosaic("quality")
    )

def _pixel_quality_cloud_penalized(
    collection: ee.ImageCollection,
    context,
) -> ee.Image:
    """
    Select the clearest pixel locally, but slightly penalize pixels
    originating from globally cloudier scenes.
    """

    def add_quality(image):
        qa = image.select("QA60")

        cloud = qa.bitwiseAnd(1 << 10).neq(0)
        cirrus = qa.bitwiseAnd(1 << 11).neq(0)

        pixel_quality = (
            ee.Image(1.0)
            .where(cirrus.And(cloud.Not()), 0.6)
            .where(cloud.And(cirrus.Not()), 0.2)
            .where(cloud.And(cirrus), 0.0)
        )

        # Scene-level cloudiness (normalized 0–1)
        scene_cloud = ee.Number(
            image.get("CLOUDY_PIXEL_PERCENTAGE")
        ).divide(100.0)

        scene_penalty = ee.Image(scene_cloud).multiply(0.05)

        quality = (
            pixel_quality
            .subtract(scene_penalty)
            .rename("quality")
            .toFloat()
        )

        return image.addBands(quality)

    return (
        collection
        .map(add_quality)
        .qualityMosaic("quality")
    )

def _pixel_quality_hybrid_fallback(
    collection: ee.ImageCollection,
    context,
) -> ee.Image:
    """
    Use the best available pixel where possible; where no pixel
    meets a minimum quality threshold, fall back to a scene-based
    selection.
    """

    min_quality = context.inputs.get("min_pixel_quality", 0.3)
    cloud_threshold = context.inputs.get("cloud_threshold", 100)
    scene_weight = context.inputs.get("scene_penalty_weight", 0.05)

    def add_quality(image):
        qa = image.select("QA60")

        cloud = qa.bitwiseAnd(1 << 10).neq(0)
        cirrus = qa.bitwiseAnd(1 << 11).neq(0)

        pixel_quality = (
            ee.Image(1.0)
            .where(cirrus.And(cloud.Not()), 0.6)
            .where(cloud.And(cirrus.Not()), 0.2)
            .where(cloud.And(cirrus), 0.0)
        )

        scene_cloud = ee.Number(
            image.get("CLOUDY_PIXEL_PERCENTAGE")
        ).divide(100.0)

        scene_penalty = ee.Image(scene_cloud).multiply(scene_weight)

        quality = (
            pixel_quality
            .subtract(scene_penalty)
            .rename("quality")
            .toFloat()
        )

        return image.addBands(quality)

    quality_mosaic = (
        collection
        .map(add_quality)
        .qualityMosaic("quality")
    )

    quality_mosaic_clean = quality_mosaic.select(
        quality_mosaic.bandNames().remove("quality")
    )

    fallback_mosaic = (
        collection
        .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", cloud_threshold))
        .sort("CLOUDY_PIXEL_PERCENTAGE", False)
        .mosaic()
    )

    low_quality_mask = (
        quality_mosaic
        .select("quality")
        .lt(min_quality)
    )

    final_mosaic = quality_mosaic_clean.where(
        low_quality_mask,
        fallback_mosaic
    )

    return final_mosaic


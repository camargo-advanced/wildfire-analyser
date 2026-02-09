""" 
SPDX-License-Identifier: MIT

This module defines alternative mosaic strategies grouped into:

1) Date-based strategies:
   - Select a single sensing date and mosaic all spatial tiles from that date.

2) Tile-based strategies:
   - Select the best available scene independently for each spatial tile.

3) Pixel-based strategies:
   - Select pixels across time based on per-pixel quality metrics.

Each strategy makes its compositing policy explicit, avoiding implicit
assumptions about spatial or temporal completeness.

Copyright (C) 2025
Marcelo Camargo.
"""

import ee

from enum import Enum
import ee


class MosaicStrategy(str, Enum):
    """
    Public-facing mosaic strategy identifiers.

    These values define the compositing policy applied to an ImageCollection.
    """

    # Date-based strategies
    BEST_DATE_MOSAIC = "best_date_mosaic"
    BEST_DATE_MASKED_MOSAIC = "best_date_masked_mosaic"

    # Tile-based strategies (default)
    BEST_AVAILABLE_PER_TILE_MOSAIC = "best_available_per_tile_mosaic"

    # Pixel-based strategies
    CLOUD_MASKED_LIGHT_MOSAIC = "cloud_masked_light_mosaic"


def apply_mosaic_strategy(
    collection: ee.ImageCollection,
    strategy,
    context,
) -> ee.Image:
    """
    Apply a named mosaic strategy to an ImageCollection.
    """

    # Accept Enum or raw string
    if isinstance(strategy, MosaicStrategy):
        strategy = strategy.value

    strategies = {
        MosaicStrategy.BEST_DATE_MOSAIC.value: best_date_mosaic,
        MosaicStrategy.BEST_DATE_MASKED_MOSAIC.value: best_date_masked_mosaic,
        MosaicStrategy.BEST_AVAILABLE_PER_TILE_MOSAIC.value: best_available_per_tile_mosaic,
        MosaicStrategy.CLOUD_MASKED_LIGHT_MOSAIC.value: cloud_masked_light_mosaic,
    }

    func = strategies.get(strategy)
    if func is None:
        raise ValueError(f"Unknown mosaic strategy: '{strategy}'")

    return func(collection, context)


def best_date_mosaic(
    collection: ee.ImageCollection,
    context,
) -> ee.Image:
    """
    Date-based mosaic strategy.

    Selects the least cloudy sensing date and mosaics all spatial tiles
    available for that date.

    - Single sensing date
    - Multi-tile (Sentinel-2 compatible)
    - No temporal mixing
    - Mosaic is used only for spatial stitching
    """

    cloud_threshold = context.inputs.get("cloud_threshold")

    filtered = collection
    if cloud_threshold is not None:
        filtered = filtered.filter(
            ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", cloud_threshold)
        )

    # Derive sensing date (YYYY-MM-dd)
    def add_date(image):
        date = ee.Date(image.get("system:time_start")).format("YYYY-MM-dd")
        return image.set("sensing_date", date)

    dated = filtered.map(add_date)

    # Pick best image to identify the best date
    best_image = dated.sort("CLOUDY_PIXEL_PERCENTAGE").first()
    best_date = best_image.get("sensing_date")

    # Rebuild collection using all tiles from that date
    same_date = dated.filter(
        ee.Filter.eq("sensing_date", best_date)
    )

    return same_date.mosaic()


def cloud_masked_light_mosaic(
    collection: ee.ImageCollection,
    context,
) -> ee.Image:    
    """
    Pixel-based mosaic using cloud probability as a quality weight.

    - Applies a light SCL cloud mask
    - Selects pixels with lower cloud probability across dates
    """
       
    def _mask_scl_light(image: ee.Image) -> ee.Image:
        scl = image.select("SCL")

        # Mask only clearly invalid observations
        invalid = (
            scl.eq(1)
            .Or(scl.eq(3))   # Cloud shadow
            .Or(scl.eq(9))   # High probability cloud
            .Or(scl.eq(10))  # Cirrus
        )
        return image.updateMask(invalid.Not())

    def _pixel_mosaic_by_cloud_prob(
        collection: ee.ImageCollection,
    ) -> ee.Image:

        def add_quality(image: ee.Image) -> ee.Image:
            prob = image.select("MSK_CLDPRB")
            scl = image.select("SCL")

            # Higher quality = lower cloud probability
            quality = ee.Image(100).subtract(prob)

            # Penalize cloud edges without fully masking them
            quality = quality.where(
                scl.eq(8),
                quality.subtract(5)
            )

            return image.addBands(quality.rename("quality"))

        return (
            collection
            .map(add_quality)
            .qualityMosaic("quality")
        )
    
    masked = collection.map(_mask_scl_light)
    mosaic = _pixel_mosaic_by_cloud_prob(masked)

    # Remove auxiliary quality band from output
    return mosaic.select(
        mosaic.bandNames().remove("quality")
    )

def best_date_masked_mosaic(
    collection: ee.ImageCollection,
    context,
) -> ee.Image:
    """
    Date-based mosaic strategy with physical cloud masking.

    - Single sensing date
    - Multi-tile (Sentinel-2 compatible)
    - Applies SCL-based cloud mask
    - Accepts data gaps
    """

    def _mask_scl(image: ee.Image) -> ee.Image:
        """
        Removes physically invalid pixels using the SCL band.
        """

        scl = image.select("SCL")

        invalid = (
            scl.eq(1)        # Saturated / defective
            .Or(scl.eq(3))   # Cloud shadow
            .Or(scl.eq(9))   # Cloud high probability
            .Or(scl.eq(10))  # Cirrus
        )

        return image.updateMask(invalid.Not())

    return _mask_scl(best_date_mosaic(collection, context))


def best_available_per_tile_mosaic(
    collection: ee.ImageCollection,
    context,
) -> ee.Image:
    """
    Scene-based per-tile mosaic strategy.

    - For each spatial tile (MGRS_TILE), selects the best available scene
    - Scene quality is evaluated independently per tile
    - Dates may vary across tiles
    - No pixel-level mixing
    - Mosaic is used only for spatial stitching
    """

    cloud_threshold = context.inputs.get("cloud_threshold")

    filtered = collection
    if cloud_threshold is not None:
        filtered = filtered.filter(
            ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", cloud_threshold)
        )

    tiles = ee.List(filtered.aggregate_array("MGRS_TILE")).distinct()

    def select_best_for_tile(tile_id):
        tile_collection = (
            filtered
            .filter(ee.Filter.eq("MGRS_TILE", tile_id))
            .sort("CLOUDY_PIXEL_PERCENTAGE")
        )
        return ee.Image(tile_collection.first())

    per_tile_best = ee.ImageCollection(
        tiles.map(select_best_for_tile)
    )

    return per_tile_best.mosaic()

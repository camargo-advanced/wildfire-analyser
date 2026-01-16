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
    cloud_threshold = context.inputs.get("cloud_threshold", 70)

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
# Stage 5 – BURN SEVERITY
# ─────────────────────────────

@register(Dependency.BURN_SEVERITY)
def compute_burn_severity(context):
    dnbr = context.get(Dependency.DNBR) 
    if dnbr is None:
        raise RuntimeError("DNBR not available in DAG context")

    severity = (
        ee.Image(0)  # Unburned
        .where(dnbr.gte(0.10).And(dnbr.lt(0.27)), 1)   # Low
        .where(dnbr.gte(0.27).And(dnbr.lt(0.44)), 2)  # Moderate
        .where(dnbr.gte(0.44).And(dnbr.lt(0.66)), 3)  # High
        .where(dnbr.gte(0.66), 4)                     # Very High
        .rename("burn_severity")
        .toInt8()
    )

    return severity

# ─────────────────────────────
# Stage 6 – STATISTICS
# ─────────────────────────────

@register(Dependency.BURNED_AREA_STATISTICS)
def compute_burned_area_statistics(context):
    severity = context.get(Dependency.BURN_SEVERITY)
    roi = context.inputs["roi"]

    if severity is None:
        raise RuntimeError("BURN_SEVERITY not available")

    pixel_area = ee.Image.pixelArea().divide(10_000)  # m² → ha

    reducer = ee.Reducer.sum().group(
        groupField=1,          # severity band index
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

    class_map = {
        0: "Unburned",
        1: "Low Severity",
        2: "Moderate Severity",
        3: "High Severity",
        4: "Very High Severity",
    }

    total_area = sum(item["sum"] for item in stats)
    burned_area = sum(
        item["sum"] for item in stats if item["severity_class"] > 0
    )

    result = {}

    for item in stats:
        name = class_map[item["severity_class"]]
        area = item["sum"]
        ratio = (area / total_area) * 100 if total_area > 0 else 0

        result[name] = {
            "area_ha": round(area, 2),
            "ratio_percent": round(ratio, 2),
        }

    # Totals (paper-style)
    result["Total Burned Area"] = {
        "area_ha": round(burned_area, 2),
        "ratio_percent": round((burned_area / total_area) * 100, 2),
    }

    result["Total Area"] = {
        "area_ha": round(total_area, 2),
        "ratio_percent": 100.0,
    }

    return result

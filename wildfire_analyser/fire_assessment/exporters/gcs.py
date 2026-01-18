import ee


def export_geotiff_to_gcs(
    image: ee.Image,
    roi: ee.Geometry,
    bucket: str,
    object_name: str,
    scale: int = 10,
    max_pixels: int = 1e13,
) -> dict:
    task = ee.batch.Export.image.toCloudStorage(
        image=image,
        description=object_name,
        bucket=bucket,
        fileNamePrefix=object_name,
        region=roi,
        scale=scale,
        maxPixels=max_pixels,
        fileFormat="GeoTIFF",
    )
    task.start()

    return {
        "url": f"https://storage.googleapis.com/{bucket}/{object_name}.tif",
        "gee_task_id": task.id,
    }

def get_visual_thumbnail_url(
    image: ee.Image,
    roi: ee.Geometry,
    scale: int = 20,
) -> str:
    return image.getThumbURL({
        "region": roi,
        "scale": scale,
        "format": "jpg",
    })

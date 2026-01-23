
import ee

def get_visual_thumbnail_url(
    image: ee.Image,
    roi: ee.Geometry,
) -> str:
    image = image.clip(roi.bounds()) 
    return image.getThumbURL({
        "dimensions": 1024,
        "format": "jpg",
    })

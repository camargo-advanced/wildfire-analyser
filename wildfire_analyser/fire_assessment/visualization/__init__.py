from wildfire_analyser.fire_assessment.deliverables import Deliverable
from wildfire_analyser.fire_assessment.visualization.rgb import (
    rgb_pre_fire_visual,
    rgb_post_fire_visual,
)

from wildfire_analyser.fire_assessment.visualization.dnbr import dnbr_visual
from wildfire_analyser.fire_assessment.visualization.dnbr_severity import (
    dnbr_severity_visual,
)
from wildfire_analyser.fire_assessment.visualization.rbr import rbr_visual
from wildfire_analyser.fire_assessment.visualization.dndvi import dndvi_visual
from .thumbnails import get_visual_thumbnail_url

VISUAL_RENDERERS = {
    Deliverable.RGB_PRE_FIRE_VISUAL: rgb_pre_fire_visual,
    Deliverable.RGB_POST_FIRE_VISUAL: rgb_post_fire_visual,
    Deliverable.DNDVI_VISUAL: dndvi_visual,
    Deliverable.DNBR_VISUAL: dnbr_visual,
    Deliverable.RBR_VISUAL: rbr_visual,
}

__all__ = [
    "get_visual_thumbnail_url",
]
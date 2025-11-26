# deliverable.py
from enum import Enum

class Deliverable(Enum):
    RGB_PRE_FIRE = "rgb_pre_fire"
    RGB_POST_FIRE = "rgb_post_fire"
    NDVI_PRE_FIRE = "ndvi_pre_fire"
    NDVI_POST_FIRE = "ndvi_post_fire"
    RBR = "rbr"

    def __str__(self):
        return self.value

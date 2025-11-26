# fire_severity.py
from enum import IntEnum

class FireSeverity(IntEnum):
    UNBURNED = (0, "Unburned")
    LOW = (1, "Low")
    MODERATE = (2, "Moderate")
    HIGH = (3, "High")
    VERY_HIGH = (4, "Very High")

    def __new__(cls, value, label):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.label = label
        return obj

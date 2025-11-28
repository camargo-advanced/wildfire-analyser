# validators.py
import os
import re
import ee
from datetime import datetime
from wildfire_analyser.fire_assessment.deliverable import Deliverable

DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"


def validate_date(value: str, field_name: str) -> None:
    """Validate date format YYYY-MM-DD."""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string in format YYYY-MM-DD.")

    if not re.match(DATE_PATTERN, value):
        raise ValueError(f"{field_name} must follow format YYYY-MM-DD.")

    try:
        datetime.strptime(value, "%Y-%m-%d")
    except Exception:
        raise ValueError(f"{field_name} is not a valid calendar date.")


def validate_geojson_path(path: str) -> None:
    """Validate that path exists, is a file, and ends with .geojson."""
    if not isinstance(path, str):
        raise ValueError("geojson_path must be a string.")

    if not path.endswith(".geojson"):
        raise ValueError("geojson_path must end with .geojson")

    if not os.path.isfile(path):
        raise ValueError(f"geojson_path does not exist: {path}")


def validate_deliverables(deliverables: list | None) -> None:
    """
    Validate deliverables list.
    If None → allowed (client wants all deliverables).
    If list → ensure each item is Deliverable.
    """
    if deliverables is None:
        return  # valid, user wants default behavior

    if not isinstance(deliverables, list):
        raise ValueError("deliverables must be a list of Deliverable values.")

    invalid = [d for d in deliverables if not isinstance(d, Deliverable)]
    if invalid:
        raise ValueError(f"Invalid deliverables: {invalid}")

def ensure_not_empty(collection: ee.ImageCollection, start: str, end: str) -> None:
    try:
        size_val = collection.size().getInfo()
    except Exception:
        size_val = 0

    if size_val == 0:
        raise ValueError(f"No images found in date range {start} → {end}")
# date_utils.py
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def compute_fire_time_windows(
    start_date: str,
    end_date: str,
    buffer_days: int,
) -> tuple[str, str, str, str]:
    sd = datetime.strptime(start_date, "%Y-%m-%d")
    ed = datetime.strptime(end_date, "%Y-%m-%d")

    before_start = (sd - timedelta(days=buffer_days)).strftime("%Y-%m-%d")
    before_end   = (sd + timedelta(days=1)).strftime("%Y-%m-%d")  # INCLUI sd

    after_start  = ed.strftime("%Y-%m-%d")
    after_end    = (ed + timedelta(days=buffer_days + 1)).strftime("%Y-%m-%d")  # INCLUI ed

    return before_start, before_end, after_start, after_end



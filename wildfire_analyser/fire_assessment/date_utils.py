# date_utils.py
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def expand_dates(start_date: str, end_date: str, days_before_after: int):
    sd = datetime.strptime(start_date, "%Y-%m-%d")
    ed = datetime.strptime(end_date, "%Y-%m-%d")
    before_start = (sd - timedelta(days=days_before_after)).strftime("%Y-%m-%d")
    after_end = (ed + timedelta(days=days_before_after)).strftime("%Y-%m-%d")
    return before_start, start_date, end_date, after_end


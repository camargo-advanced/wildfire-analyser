# date_utils.py
from datetime import datetime, timedelta
import logging

DAYS_BEFORE_AFTER = 30


logger = logging.getLogger(__name__)
def expand_dates(start_date: str, end_date: str):
        sd = datetime.strptime(start_date, "%Y-%m-%d")
        ed = datetime.strptime(end_date, "%Y-%m-%d")
        before_start = (sd - timedelta(days=DAYS_BEFORE_AFTER)).strftime("%Y-%m-%d")
        after_end = (ed + timedelta(days=DAYS_BEFORE_AFTER)).strftime("%Y-%m-%d")
        return before_start, start_date, end_date, after_end

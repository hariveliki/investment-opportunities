"""Trading calendar service using exchange_calendars."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from functools import lru_cache

import exchange_calendars as xcals
import pandas as pd

from app.models.schemas import UNIVERSE_EXCHANGE_CALENDARS

logger = logging.getLogger(__name__)


@lru_cache(maxsize=32)
def _get_calendar(exchange_code: str) -> xcals.ExchangeCalendar:
    return xcals.get_calendar(exchange_code)


def resolve_sessions(
    universe_id: str,
    as_of: date,
    horizon_str: str,
) -> tuple[date, date]:
    """Resolve start and end trading sessions given a universe, as-of date, and horizon.

    Returns (start_session, end_session).
    """
    exchange_code = UNIVERSE_EXCHANGE_CALENDARS.get(universe_id, "XNYS")
    cal = _get_calendar(exchange_code)

    as_of_ts = pd.Timestamp(as_of)

    if as_of_ts > cal.last_session:
        end_session = cal.last_session
    elif cal.is_session(as_of_ts):
        end_session = as_of_ts
    else:
        end_session = cal.date_to_session(as_of_ts, direction="previous")

    horizon_value, horizon_type = _parse_horizon(horizon_str)

    if horizon_type == "trading":
        sessions = cal.sessions
        end_idx = sessions.get_loc(end_session)
        start_idx = max(0, end_idx - horizon_value)
        start_session = sessions[start_idx]
    else:
        calendar_start = as_of - timedelta(days=horizon_value)
        cal_start_ts = pd.Timestamp(calendar_start)
        if cal_start_ts < cal.first_session:
            start_session = cal.first_session
        elif cal.is_session(cal_start_ts):
            start_session = cal_start_ts
        else:
            start_session = cal.date_to_session(cal_start_ts, direction="previous")

    return start_session.date(), end_session.date()


def _parse_horizon(horizon_str: str) -> tuple[int, str]:
    """Parse horizon string like '5d' (trading days) or '7c' (calendar days).

    Returns (value, type) where type is 'trading' or 'calendar'.
    """
    horizon_str = horizon_str.strip().lower()
    if horizon_str.endswith("d"):
        return int(horizon_str[:-1]), "trading"
    elif horizon_str.endswith("c"):
        return int(horizon_str[:-1]), "calendar"
    else:
        return int(horizon_str), "trading"

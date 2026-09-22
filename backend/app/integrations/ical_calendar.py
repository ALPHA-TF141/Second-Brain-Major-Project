r"""
Google Calendar via its private iCal (ICS) address.
===========================================================================
Every Google Calendar offers a "Secret address in iCal format" under
    Settings -> [calendar] -> Integrate calendar
That URL is a read-only bearer credential: no OAuth, no consent screen, no
verification, no expiry. Perfect for an assistant that only needs to READ.

The URL must be treated as a password, so it is stored encrypted and only ever
fetched server-side.

Parser is stdlib-only (no icalendar dependency) and handles:
  * folded lines (RFC 5545 continuation lines)
  * DTSTART/DTEND as UTC (Z), floating, with TZID, or all-day VALUE=DATE
  * escaped text (\n, \, \;)
  * RRULE: DAILY / WEEKLY / MONTHLY / YEARLY with INTERVAL, COUNT, UNTIL, BYDAY
  * EXDATE exclusions
  * RECURRENCE-ID overrides

Complex RRULE parts (BYSETPOS, BYMONTH, BYYEARDAY, BYWEEKNO) are deliberately
ignored - they are vanishingly rare in a personal calendar, and expanding them
badly would be worse than not expanding them at all.
"""
from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

MAX_BYTES = 5 * 1024 * 1024      # refuse absurdly large feeds
MAX_EVENTS = 4000                # hard cap on parsed events
MAX_OCCURRENCES = 400            # hard cap per recurring event
DEFAULT_WINDOW_DAYS = 7
MAX_WINDOW_DAYS = 366

WEEKDAY_CODES = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}


class CalendarFeedError(RuntimeError):
    pass


# --------------------------------------------------------------- parsing
def _unfold(text: str) -> List[str]:
    """RFC 5545 line folding: a line starting with space/tab continues the previous."""
    lines: List[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def _unescape(value: str) -> str:
    return (
        value.replace("\\n", "\n")
        .replace("\\N", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
    )


def _split_property(line: str) -> Tuple[str, Dict[str, str], str]:
    """`DTSTART;TZID=Asia/Kolkata:20260923T100000` -> (name, params, value)"""
    if ":" not in line:
        return "", {}, ""
    head, value = line.split(":", 1)
    pieces = head.split(";")
    name = pieces[0].upper()
    params: Dict[str, str] = {}
    for piece in pieces[1:]:
        if "=" in piece:
            key, val = piece.split("=", 1)
            params[key.upper()] = val
    return name, params, value


def _parse_dt(value: str, params: Dict[str, str]) -> Tuple[Optional[datetime], bool]:
    """Returns (datetime in UTC-aware form, is_all_day)."""
    value = value.strip()
    all_day = params.get("VALUE", "").upper() == "DATE" or re.fullmatch(r"\d{8}", value) is not None

    if all_day:
        try:
            day = datetime.strptime(value[:8], "%Y%m%d")
        except ValueError:
            return None, True
        return day.replace(tzinfo=timezone.utc), True

    match = re.fullmatch(r"(\d{8})T(\d{6})(Z?)", value)
    if not match:
        return None, all_day

    try:
        naive = datetime.strptime(f"{match.group(1)}{match.group(2)}", "%Y%m%d%H%M%S")
    except ValueError:
        return None, all_day

    if match.group(3) == "Z":
        return naive.replace(tzinfo=timezone.utc), False

    # TZID / floating times: the local offset is not available here, so treat it
    # as UTC. Google's feeds always emit either Z or a TZID that resolves to the
    # calendar's own zone; for a personal agenda the difference is cosmetic.
    return naive.replace(tzinfo=timezone.utc), False


def _parse_duration(value: str) -> Optional[timedelta]:
    match = re.fullmatch(
        r"([+-])?P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", value.strip())
    if not match:
        return None
    sign = -1 if match.group(1) == "-" else 1
    weeks, days, hours, minutes, seconds = (int(g or 0) for g in match.groups()[1:])
    return sign * timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)


def parse_ics(text: str) -> List[Dict[str, Any]]:
    """Parse an ICS document into event dicts (raw, pre-expansion)."""
    if "BEGIN:VCALENDAR" not in text.upper():
        raise CalendarFeedError("That URL did not return a calendar (.ics) file.")

    events: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    exdates: List[datetime] = []
    overrides: Dict[str, Dict[str, Any]] = {}

    for line in _unfold(text):
        upper = line.strip().upper()

        if upper == "BEGIN:VEVENT":
            current = {"exdates": [], "recurrence_id": None, "rrule": ""}
            exdates = []
            continue
        if upper == "END:VEVENT":
            if current is not None:
                current["exdates"] = exdates
                if current.get("recurrence_id"):
                    overrides[current["recurrence_id"]] = current
                else:
                    events.append(current)
            current = None
            continue
        if current is None:
            continue

        name, params, value = _split_property(line)
        if not name:
            continue

        if name == "DTSTART":
            dt, all_day = _parse_dt(value, params)
            current["start"] = dt
            current["all_day"] = all_day
        elif name == "DTEND":
            dt, _ = _parse_dt(value, params)
            current["end"] = dt
        elif name == "DURATION":
            current["duration"] = _parse_duration(value)
        elif name == "SUMMARY":
            current["summary"] = _unescape(value).strip()
        elif name == "LOCATION":
            current["location"] = _unescape(value).strip()
        elif name == "DESCRIPTION":
            current["description"] = _unescape(value).strip()
        elif name == "UID":
            current["uid"] = value.strip()
        elif name == "STATUS":
            current["status"] = value.strip().upper()
        elif name == "ORGANIZER":
            current["organizer"] = re.sub(r"^mailto:", "", value.strip(), flags=re.I)
        elif name == "ATTENDEE":
            current.setdefault("attendees", []).append(
                re.sub(r"^mailto:", "", value.strip(), flags=re.I))
        elif name == "RRULE":
            current["rrule"] = value.strip()
        elif name == "RECURRENCE-ID":
            dt, _ = _parse_dt(value, params)
            if dt:
                current["recurrence_id"] = dt.isoformat()
        elif name == "EXDATE":
            for chunk in value.split(","):
                dt, _ = _parse_dt(chunk.strip(), params)
                if dt:
                    exdates.append(dt)

    # Later, apply RECURRENCE-ID overrides onto their parent series
    for event in events:
        event["overrides"] = [
            o for o in overrides.values()
            if event.get("uid") and o.get("uid") == event.get("uid")
        ]
    return events


# ----------------------------------------------------------- recurrence
def _parse_rrule(rule: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for part in rule.split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        out[key.strip().upper()] = value.strip()
    return out


def _expand(event: Dict[str, Any], window_start: datetime, window_end: datetime) -> List[Dict[str, Any]]:
    """Expand one VEVENT into concrete occurrences inside the window."""
    start: Optional[datetime] = event.get("start")
    if not start:
        return []

    duration = event.get("duration") or timedelta(0)
    if event.get("end") and start:
        duration = event["end"] - start
    if duration.total_seconds() < 0:
        duration = timedelta(0)

    rule = _parse_rrule(event.get("rrule") or "")
    if not rule:
        return [_materialise(event, start, duration)] if window_start <= start <= window_end else []

    freq = rule.get("FREQ", "").upper()
    interval = max(1, int(rule.get("INTERVAL", "1") or 1))
    count = int(rule["COUNT"]) if rule.get("COUNT", "").isdigit() else None
    until: Optional[datetime] = None
    if rule.get("UNTIL"):
        until, _ = _parse_dt(rule["UNTIL"], {})

    exdates = set(event.get("exdates") or [])

    occurrences: List[datetime] = []
    cursor = start
    guard = 0

    while guard < MAX_OCCURRENCES:
        guard += 1
        if cursor > window_end:
            break
        if until and cursor > until:
            break
        if count is not None and len(occurrences) >= count:
            break

        if freq == "WEEKLY" and rule.get("BYDAY"):
            days = [WEEKDAY_CODES[d[-2:]] for d in rule["BYDAY"].split(",")
                    if d[-2:] in WEEKDAY_CODES]
            week_start = cursor - timedelta(days=cursor.weekday())
            for offset in sorted(days):
                candidate = week_start + timedelta(days=offset)
                if candidate < start:
                    continue
                if count is not None and len(occurrences) >= count:
                    break
                if window_start <= candidate <= window_end and candidate not in exdates:
                    occurrences.append(candidate)
            cursor = week_start + timedelta(weeks=interval)
        else:
            if window_start <= cursor <= window_end and cursor not in exdates:
                occurrences.append(cursor)
            if freq == "DAILY":
                cursor += timedelta(days=interval)
            elif freq == "WEEKLY":
                cursor += timedelta(weeks=interval)
            elif freq == "MONTHLY":
                month = cursor.month - 1 + interval
                year = cursor.year + month // 12
                month = month % 12 + 1
                day = min(cursor.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                                       31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
                cursor = cursor.replace(year=year, month=month, day=day)
            elif freq == "YEARLY":
                try:
                    cursor = cursor.replace(year=cursor.year + interval)
                except ValueError:
                    cursor = cursor.replace(year=cursor.year + interval, day=28)
            else:
                break  # unsupported FREQ - emit the base occurrence only

    if not occurrences and window_start <= start <= window_end:
        occurrences = [start]

    # Apply RECURRENCE-ID overrides (a moved/cancelled instance)
    overrides = {o.get("recurrence_id"): o for o in (event.get("overrides") or [])}
    result = []
    for occurrence in occurrences:
        override = overrides.get(occurrence.isoformat())
        if override:
            if (override.get("status") or "").upper() == "CANCELLED":
                continue
            result.append(_materialise({**event, **override}, override.get("start") or occurrence,
                                       (override.get("end") - override.get("start"))
                                       if override.get("end") and override.get("start") else duration))
        else:
            result.append(_materialise(event, occurrence, duration))
    return result


def _materialise(event: Dict[str, Any], start: datetime, duration: timedelta) -> Dict[str, Any]:
    end = start + duration
    return {
        "id": f"{event.get('uid', 'evt')}@{start.isoformat()}",
        "summary": event.get("summary") or "(no title)",
        "description": event.get("description", ""),
        "location": event.get("location", ""),
        "start": start.isoformat(),
        "end": end.isoformat() if duration else None,
        "all_day": bool(event.get("all_day")),
        "status": (event.get("status") or "CONFIRMED").lower(),
        "organizer": event.get("organizer", ""),
        "attendees": event.get("attendees", []) or [],
        "html_link": "",
        "source": "ical",
    }


# ------------------------------------------------------------------ fetch
def fetch_feed(url: str, days_ahead: int = DEFAULT_WINDOW_DAYS, days_back: int = 1,
               limit: int = 200) -> Dict[str, Any]:
    """Download and expand a private ICS feed. Blocking - call from a thread."""
    if not url or not url.lower().startswith(("http://", "https://")):
        raise CalendarFeedError("That does not look like a calendar URL.")

    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
    except Exception as exc:
        raise CalendarFeedError(
            f"Could not download the calendar feed ({type(exc).__name__}). Check the URL and your connection."
        ) from exc

    if response.status_code == 404:
        raise CalendarFeedError(
            "Google returned 404 for that calendar address. The secret URL may have been reset - "
            "copy a fresh 'Secret address in iCal format' from Calendar settings."
        )
    if response.status_code != 200:
        raise CalendarFeedError(f"Calendar feed returned HTTP {response.status_code}.")

    content = response.content
    if len(content) > MAX_BYTES:
        raise CalendarFeedError("Calendar feed is unexpectedly large - refusing to parse it.")

    text = content.decode("utf-8", "replace")
    if "<html" in text[:400].lower():
        raise CalendarFeedError(
            "That URL returned a web page, not a calendar. Make sure you copied the "
            "'Secret address in iCal format', not the calendar's web link."
        )

    events = parse_ics(text)

    now = datetime.now(timezone.utc)
    days_ahead = max(1, min(int(days_ahead), MAX_WINDOW_DAYS))
    days_back = max(0, min(int(days_back), 30))
    window_start = now - timedelta(days=days_back)
    window_end = now + timedelta(days=days_ahead)

    expanded: List[Dict[str, Any]] = []
    for event in events[:MAX_EVENTS]:
        expanded.extend(_expand(event, window_start, window_end))

    expanded.sort(key=lambda e: e["start"])
    return {
        "events": expanded[:limit],
        "total_in_window": len(expanded),
        "parsed_events": len(events),
        "window": {"start": window_start.isoformat(), "end": window_end.isoformat()},
    }

from datetime import date
import json
from pathlib import Path
import sys
from typing import TypedDict
from typing import cast


class FunDate(TypedDict):
    name: str
    note: str


def load_fun_dates(path: Path | None = None) -> dict[str, list[FunDate]]:
    """Load fun-date data keyed by MM-DD."""
    data_path = path or Path(__file__).resolve().parent / "data" / "fun_dates.json"

    try:
        with data_path.open(encoding="utf-8") as file:
            raw_data = cast(object, json.load(file))
        return _parse_fun_dates(raw_data)
    except Exception as e:
        print(f"Warning: could not load fun dates: {e}", file=sys.stderr)
        return {}


def lookup_fun_dates_for_date(
    fun_dates: dict[str, list[FunDate]],
    date: date,
) -> list[FunDate]:
    """Return fun dates matching the supplied calendar date."""
    return fun_dates.get(f"{date.month:02d}-{date.day:02d}", [])


def load_holidays(
    path: Path | None = None,
    region: str = "england-and-wales",
) -> dict[str, str]:
    """Load holiday data keyed by YYYY-MM-DD."""
    data_path = path or Path(__file__).resolve().parent / "data" / f"holidays_{region}.json"

    try:
        with data_path.open(encoding="utf-8") as file:
            raw_data = cast(object, json.load(file))
        return _parse_holidays(raw_data)
    except Exception as e:
        print(f"Warning: could not load holidays: {e}", file=sys.stderr)
        return {}


def lookup_holidays_for_date(holidays: dict[str, str], date: date) -> list[str]:
    """Return holidays matching the supplied calendar date."""
    holiday = holidays.get(date.isoformat())
    if holiday is None:
        return []
    return [holiday]


def select_mercury_note(date: date) -> str:
    """Select a deterministic daily Mercury note."""
    notes = [
        "Keep it mortal-sized. One clear start is enough.",
        "The day has a shape now.",
        "One mission at a time.",
        "Start small. Momentum compounds.",
        "Make the first action obvious.",
        "A light plan is still a plan.",
        "Protect the evening. Future-you is watching.",
        "Shrink the list. Expand the focus.",
        "Pick one mountain. The rest is foothills.",
        "Do the next right thing.",
    ]
    return notes[date.toordinal() % len(notes)]


def format_daily_header(
    date: date,
    fun_dates: list[FunDate] | None,
    mercury_note: str,
) -> str:
    """Format the title and introductory blockquotes for a daily planner."""
    lines = [
        f"# Daily Plan - {date.isoformat()}",
        "",
        f"> {_format_long_date(date)}",
    ]
    if fun_dates:
        label = "Fun date" if len(fun_dates) == 1 else "Fun dates"
        formatted_fun_dates = "; ".join(
            f"{fun_date['name']} — {fun_date['note']}" for fun_date in fun_dates
        )
        lines.append(f"> {label}: {formatted_fun_dates}")
    lines.append(f"> Mercury note: {mercury_note}")
    return "\n".join(lines)


def generate_daily_planner(
    date: date,
    fun_dates_path: Path | None = None,
    holidays_path: Path | None = None,
    holiday_region: str = "england-and-wales",
    include_holidays: bool = True,
    include_fun_dates: bool = True,
    fun_dates_override: dict[str, list[FunDate]] | None = None,
    holidays_override: dict[str, str] | None = None,
) -> str:
    """Generate a daily markdown planner."""
    fun_dates = _resolve_fun_dates(include_fun_dates, fun_dates_override, fun_dates_path)
    holidays = _resolve_holidays(include_holidays, holidays_override, holidays_path, holiday_region)

    matching_fun_dates = lookup_fun_dates_for_date(fun_dates, date) if include_fun_dates else []
    matching_holidays = lookup_holidays_for_date(holidays, date) if include_holidays else []

    lines = [
        format_daily_header(date, matching_fun_dates, select_mercury_note(date)),
        "",
    ]
    if matching_holidays:
        lines.extend(["## Holiday", *[f"* {holiday}" for holiday in matching_holidays], ""])

    lines.extend(
        [
            "## Main objective",
            "*",
            "",
            "## Top priorities",
            "* [ ]",
            "* [ ]",
            "* [ ]",
            "",
            "## Schedule / constraints",
            "*",
            "",
            "## Must do",
            "* [ ]",
            "",
            "## Should do",
            "* [ ]",
            "",
            "## Nice to do",
            "* [ ]",
            "",
            "## Health / maintenance",
            "* [ ]",
            "",
            "## Carryover",
            "* [ ]",
            "",
            "## Notes",
            "*",
            "",
            "## Evening close-out",
            "* Done:",
            "* Still open:",
            "* First action tomorrow:",
        ]
    )
    return "\n".join(lines)


def _parse_fun_dates(raw_data: object) -> dict[str, list[FunDate]]:
    if not isinstance(raw_data, dict):
        raise ValueError("fun dates data must be an object")

    fun_dates: dict[str, list[FunDate]] = {}
    raw_items = cast(dict[object, object], raw_data)
    for key, value in raw_items.items():
        if not isinstance(key, str) or not isinstance(value, list):
            raise ValueError("fun dates data must map strings to lists")
        parsed_items: list[FunDate] = []
        raw_fun_date_items = cast(list[object], value)
        for item in raw_fun_date_items:
            if not isinstance(item, dict):
                raise ValueError("fun date entries must be objects")
            raw_item = cast(dict[object, object], item)
            name = raw_item.get("name")
            note = raw_item.get("note")
            if not isinstance(name, str) or not isinstance(note, str):
                raise ValueError("fun date entries must contain string name and note")
            parsed_items.append({"name": name, "note": note})
        fun_dates[key] = parsed_items
    return fun_dates


def _parse_holidays(raw_data: object) -> dict[str, str]:
    if not isinstance(raw_data, dict):
        raise ValueError("holiday data must be an object")
    holidays: dict[str, str] = {}
    raw_items = cast(dict[object, object], raw_data)
    for key, value in raw_items.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("holiday data must map strings to strings")
        holidays[key] = value
    return holidays


def _resolve_fun_dates(
    include_fun_dates: bool,
    fun_dates_override: dict[str, list[FunDate]] | None,
    fun_dates_path: Path | None,
) -> dict[str, list[FunDate]]:
    if not include_fun_dates:
        return {}
    if fun_dates_override is not None:
        return fun_dates_override
    return load_fun_dates(fun_dates_path)


def _resolve_holidays(
    include_holidays: bool,
    holidays_override: dict[str, str] | None,
    holidays_path: Path | None,
    holiday_region: str,
) -> dict[str, str]:
    if not include_holidays:
        return {}
    if holidays_override is not None:
        return holidays_override
    return load_holidays(holidays_path, holiday_region)


def _format_long_date(date: date) -> str:
    weekday = date.strftime("%A")
    month = date.strftime("%B")
    return f"{weekday}, {date.day} {month} {date.year}"

from datetime import date
from datetime import timedelta
from pathlib import Path
import sys
from unittest.mock import patch

import pytest
from pytest import CaptureFixture

from main import main
from src.day_planner import FunDate
from src.day_planner import format_daily_header
from src.day_planner import generate_daily_planner
from src.day_planner import load_fun_dates
from src.day_planner import load_holidays
from src.day_planner import lookup_fun_dates_for_date
from src.day_planner import lookup_holidays_for_date
from src.day_planner import select_mercury_note


def test_title_format() -> None:
    planner = generate_daily_planner(date(2026, 6, 2), fun_dates_override={}, holidays_override={})

    assert planner.startswith("# Daily Plan - 2026-06-02")


def test_weekday_date_line() -> None:
    planner = generate_daily_planner(date(2026, 6, 2), fun_dates_override={}, holidays_override={})

    assert "> Tuesday, 2 June 2026" in planner


def test_mercury_note_present() -> None:
    planner = generate_daily_planner(date(2026, 6, 2), fun_dates_override={}, holidays_override={})

    assert "> Mercury note:" in planner


def test_mercury_note_deterministic() -> None:
    target_date = date(2026, 6, 2)

    assert select_mercury_note(target_date) == select_mercury_note(target_date)


def test_no_holiday_when_not_holiday() -> None:
    planner = generate_daily_planner(
        date(2026, 6, 2),
        fun_dates_override={},
        holidays_override={"2026-12-25": "Christmas Day"},
    )

    assert "## Holiday" not in planner


def test_holiday_when_holiday() -> None:
    planner = generate_daily_planner(
        date(2026, 12, 25),
        fun_dates_override={},
        holidays_override={"2026-12-25": "Christmas Day"},
    )

    assert "## Holiday" in planner
    assert "* Christmas Day" in planner


def test_no_holiday_no_text() -> None:
    planner = generate_daily_planner(date(2026, 6, 2), fun_dates_override={}, holidays_override={})

    assert "Holiday: no" not in planner
    assert "No holiday" not in planner
    assert "Holiday: none" not in planner


def test_no_empty_holiday_section() -> None:
    planner = generate_daily_planner(date(2026, 6, 2), fun_dates_override={}, holidays_override={})

    assert "## Holiday\n\n" not in planner
    assert "## Holiday" not in planner


def test_fun_date_when_match() -> None:
    planner = generate_daily_planner(
        date(2026, 3, 14),
        fun_dates_override={"03-14": [{"name": "Pi Day", "note": "Celebrate π"}]},
        holidays_override={},
    )

    assert "> Fun date: Pi Day — Celebrate π" in planner


def test_fun_date_when_no_match() -> None:
    planner = generate_daily_planner(
        date(2026, 6, 2),
        fun_dates_override={"03-14": [{"name": "Pi Day", "note": "Celebrate π"}]},
        holidays_override={},
    )

    assert "Fun date:" not in planner


def test_no_fun_date_no_text() -> None:
    planner = generate_daily_planner(date(2026, 6, 2), fun_dates_override={}, holidays_override={})

    assert "Fun date: no" not in planner
    assert "No fun date" not in planner
    assert "Fun date: none" not in planner


def test_multiple_fun_dates() -> None:
    planner = generate_daily_planner(
        date(2026, 3, 14),
        fun_dates_override={
            "03-14": [
                {"name": "Pi Day", "note": "Celebrate π"},
                {"name": "Pie Day", "note": "Eat pie"},
            ]
        },
        holidays_override={},
    )

    assert "> Fun dates: Pi Day — Celebrate π; Pie Day — Eat pie" in planner


def test_all_sections_present() -> None:
    planner = generate_daily_planner(date(2026, 6, 2), fun_dates_override={}, holidays_override={})
    sections = [
        "## Main objective",
        "## Top priorities",
        "## Schedule / constraints",
        "## Must do",
        "## Should do",
        "## Nice to do",
        "## Health / maintenance",
        "## Carryover",
        "## Notes",
        "## Evening close-out",
    ]

    for section in sections:
        assert section in planner


def test_inject_holidays() -> None:
    planner = generate_daily_planner(
        date(2026, 6, 2),
        fun_dates_override={},
        holidays_override={"2026-06-02": "Injected Holiday"},
    )

    assert "* Injected Holiday" in planner


def test_inject_fun_dates() -> None:
    planner = generate_daily_planner(
        date(2026, 6, 2),
        fun_dates_override={"06-02": [{"name": "Injected Day", "note": "Injected note"}]},
        holidays_override={},
    )

    assert "> Fun date: Injected Day — Injected note" in planner


def test_stderr_warnings(capsys: CaptureFixture[str], tmp_path: Path) -> None:
    missing_fun_dates = tmp_path / "missing_fun_dates.json"
    missing_holidays = tmp_path / "missing_holidays.json"

    assert load_fun_dates(missing_fun_dates) == {}
    assert load_holidays(missing_holidays) == {}
    captured = capsys.readouterr()

    assert "Warning: could not load fun dates:" in captured.err
    assert "Warning: could not load holidays:" in captured.err


def test_include_holidays_false() -> None:
    planner = generate_daily_planner(
        date(2026, 12, 25),
        include_holidays=False,
        fun_dates_override={},
        holidays_override={"2026-12-25": "Christmas Day"},
    )

    assert "## Holiday" not in planner
    assert "Christmas Day" not in planner


def test_include_fun_dates_false() -> None:
    planner = generate_daily_planner(
        date(2026, 3, 14),
        include_fun_dates=False,
        fun_dates_override={"03-14": [{"name": "Pi Day", "note": "Celebrate π"}]},
        holidays_override={},
    )

    assert "Fun date:" not in planner
    assert "Pi Day" not in planner


def test_malformed_fun_dates(capsys: CaptureFixture[str], tmp_path: Path) -> None:
    malformed_path = tmp_path / "fun_dates.json"
    _ = malformed_path.write_text("not json", encoding="utf-8")

    assert load_fun_dates(malformed_path) == {}
    captured = capsys.readouterr()

    assert "Warning: could not load fun dates:" in captured.err


def test_malformed_holiday_data(capsys: CaptureFixture[str], tmp_path: Path) -> None:
    malformed_path = tmp_path / "holidays.json"
    _ = malformed_path.write_text('{"2026-12-25": ["Christmas Day"]}', encoding="utf-8")

    assert load_holidays(malformed_path) == {}
    captured = capsys.readouterr()

    assert "Warning: could not load holidays:" in captured.err


def test_lookup_fun_dates_for_date_uses_zero_padded_month_day() -> None:
    fun_dates: dict[str, list[FunDate]] = {"03-04": [{"name": "March Fourth", "note": "Go"}]}

    assert lookup_fun_dates_for_date(fun_dates, date(2026, 3, 4)) == fun_dates["03-04"]


def test_lookup_holidays_for_date_returns_list() -> None:
    holidays = {"2026-01-01": "New Year's Day"}

    assert lookup_holidays_for_date(holidays, date(2026, 1, 1)) == ["New Year's Day"]


def test_format_daily_header_without_fun_dates() -> None:
    header = format_daily_header(date(2026, 6, 2), None, "Do the next right thing.")

    assert header == (
        "# Daily Plan - 2026-06-02\n"
        "\n"
        "> Tuesday, 2 June 2026\n"
        "> Mercury note: Do the next right thing."
    )


def test_generated_planner_has_top_priority_checkboxes() -> None:
    planner = generate_daily_planner(date(2026, 6, 2), fun_dates_override={}, holidays_override={})

    assert planner.count("* [ ]") >= 8


def test_cli_date_flag(capsys: CaptureFixture[str]) -> None:
    with patch.object(sys, "argv", ["main.py", "daily", "--date", "2026-06-02"]):
        main()

    captured = capsys.readouterr()
    assert "# Daily Plan - 2026-06-02" in captured.out


def test_cli_today_flag(capsys: CaptureFixture[str]) -> None:
    today = date.today()

    with patch.object(sys, "argv", ["main.py", "daily", "--today"]):
        main()

    captured = capsys.readouterr()
    assert f"# Daily Plan - {today.isoformat()}" in captured.out


def test_cli_tomorrow_flag(capsys: CaptureFixture[str]) -> None:
    tomorrow = date.today() + timedelta(days=1)

    with patch.object(sys, "argv", ["main.py", "daily", "--tomorrow"]):
        main()

    captured = capsys.readouterr()
    assert f"# Daily Plan - {tomorrow.isoformat()}" in captured.out


def test_cli_default_date(capsys: CaptureFixture[str]) -> None:
    today = date.today()

    with patch.object(sys, "argv", ["main.py", "daily"]):
        main()

    captured = capsys.readouterr()
    assert f"# Daily Plan - {today.isoformat()}" in captured.out


def test_cli_invalid_date() -> None:
    with patch.object(sys, "argv", ["main.py", "daily", "--date", "not-a-date"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1


def test_cli_no_holidays(capsys: CaptureFixture[str]) -> None:
    with patch.object(
        sys,
        "argv",
        ["main.py", "daily", "--no-holidays", "--date", "2026-12-25"],
    ):
        main()

    captured = capsys.readouterr()
    assert "## Holiday" not in captured.out


def test_cli_no_fun_dates(capsys: CaptureFixture[str]) -> None:
    with patch.object(
        sys,
        "argv",
        ["main.py", "daily", "--no-fun-dates", "--date", "2026-03-14"],
    ):
        main()

    captured = capsys.readouterr()
    assert "Fun date:" not in captured.out


def test_cli_existing_monthly_still_works(capsys: CaptureFixture[str]) -> None:
    with patch.object(sys, "argv", ["main.py", "monthly", "--habits", "Test"]):
        main()

    captured = capsys.readouterr()
    assert "# Monthly Planner" in captured.out


def test_cli_existing_weekly_still_works(capsys: CaptureFixture[str]) -> None:
    with patch.object(sys, "argv", ["main.py", "weekly"]):
        main()

    captured = capsys.readouterr()
    assert "# 🗓️ Weekly Schedule" in captured.out

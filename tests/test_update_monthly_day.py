from __future__ import annotations

from email.message import Message
import json
from pathlib import Path
import shutil
import sys
from typing import cast
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from scripts import update_monthly_day as monthly_day

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, body: bytes = b"{}") -> None:
        self.body: bytes = body

    def read(self) -> bytes:
        return self.body

    def close(self) -> None:
        return None


def sample_body() -> str:
    return (FIXTURES / "sample_monthly_body.md").read_text(encoding="utf-8")


def parsed_table() -> monthly_day.TableParsed:
    return monthly_day.parse_monthly_table(sample_body(), "may-note-id")


def assert_exits_with_code(code: int) -> pytest.RaisesExc[SystemExit]:
    return pytest.raises(SystemExit, match=str(code))


def write_config(tmp_path: Path) -> Path:
    _ = shutil.copy(FIXTURES / "sample_planner_state.json", tmp_path / "planner-state.json")
    _ = shutil.copy(FIXTURES / "sample_joplin.env", tmp_path / "joplin.env")
    return tmp_path


def run_main(argv: list[str]) -> None:
    with patch.object(sys, "argv", ["update_monthly_day.py", *argv]):
        monthly_day.main()


def http_error(reason: str = "fake-secret-token failed") -> HTTPError:
    return HTTPError("http://127.0.0.1/?token=fake-secret-token", 500, reason, Message(), None)


def test_parse_monthly_table_basic() -> None:
    parsed = parsed_table()

    assert parsed.header_cells == [
        " Day ",
        " Weekday ",
        " Highlight ",
        " Hydrate ",
        " Move ",
        " Read ",
        " Deep Work ",
        " Steps ",
    ]
    assert len(parsed.rows) == 31
    assert parsed.rows[0].cells[0].strip() == "01"
    assert parsed.rows[-1].cells[0].strip() == "31"


def test_parse_monthly_table_no_table() -> None:
    with assert_exits_with_code(1):
        _ = monthly_day.parse_monthly_table("# No tracker here\n", "missing-note")


def test_parse_monthly_table_preserves_preamble() -> None:
    parsed = parsed_table()

    assert "## Main Goals of the Month\n" in parsed.preamble
    assert "| Day |" not in "".join(parsed.preamble)


def test_parse_monthly_table_preserves_postamble() -> None:
    parsed = parsed_table()

    assert "## End-of-Month Review\n" in parsed.postamble
    assert "- Biggest win:\n" in parsed.postamble


def test_find_day_row_existing() -> None:
    row = monthly_day.find_day_row(parsed_table().rows, 15)

    assert row.cells[0].strip() == "15"
    assert row.cells[2].strip() == "Demo day"


def test_find_day_row_not_found() -> None:
    with assert_exits_with_code(1):
        _ = monthly_day.find_day_row(parsed_table().rows, 32)


@pytest.mark.parametrize("raw", ["true", "True", "TRUE"])
def test_coerce_checkbox_true_variants(raw: str) -> None:
    assert monthly_day.coerce_checkbox(raw, "Hydrate") is True


@pytest.mark.parametrize("raw", ["false", "False", "FALSE"])
def test_coerce_checkbox_false_variants(raw: str) -> None:
    assert monthly_day.coerce_checkbox(raw, "Hydrate") is False


@pytest.mark.parametrize("raw", ["yes", "1", ""])
def test_coerce_checkbox_invalid(raw: str) -> None:
    with assert_exits_with_code(1):
        _ = monthly_day.coerce_checkbox(raw, "Hydrate")


def test_coerce_number_zero() -> None:
    assert monthly_day.coerce_number("0", "Steps") == 0


def test_coerce_number_positive() -> None:
    assert monthly_day.coerce_number("5", "Steps") == 5


def test_coerce_number_negative() -> None:
    with assert_exits_with_code(1):
        _ = monthly_day.coerce_number("-1", "Steps")


def test_coerce_number_float() -> None:
    with assert_exits_with_code(1):
        _ = monthly_day.coerce_number("3.5", "Steps")


def test_coerce_number_non_numeric() -> None:
    with assert_exits_with_code(1):
        _ = monthly_day.coerce_number("abc", "Steps")


def test_validate_fields_unknown_name(capsys: pytest.CaptureFixture[str]) -> None:
    with assert_exits_with_code(1):
        _ = monthly_day.validate_fields([("Unknown", "true")], {"Hydrate": "checkbox"})

    error = capsys.readouterr().err
    assert "Unknown" in error
    assert "Hydrate" in error


def test_validate_fields_mixed_valid_invalid(capsys: pytest.CaptureFixture[str]) -> None:
    with assert_exits_with_code(1):
        _ = monthly_day.validate_fields(
            [("Hydrate", "true"), ("Bad One", "1"), ("Bad Two", "2")],
            {"Hydrate": "checkbox", "Steps": "number"},
        )

    error = capsys.readouterr().err
    assert "Bad One" in error
    assert "Bad Two" in error
    assert "Hydrate, Steps" in error


def updated_cells(updates: dict[str, bool | int], note: str | None = None) -> list[str]:
    parsed = parsed_table()
    row = monthly_day.find_day_row(parsed.rows, 15)
    line = monthly_day.update_row_cells(
        row,
        parsed.header_cells,
        updates,
        {
            "Hydrate": "checkbox",
            "Move": "checkbox",
            "Read": "checkbox",
            "Deep Work": "checkbox",
            "Steps": "number",
        },
        note,
    )
    return [cell.strip() for cell in monthly_day.parse_table_cells(line)]


def test_update_checkbox_true() -> None:
    assert updated_cells({"Hydrate": True})[3] == "[x]"


def test_update_checkbox_false() -> None:
    assert updated_cells({"Hydrate": False})[3] == "[ ]"


def test_update_number_positive() -> None:
    assert updated_cells({"Steps": 3})[7] == "3"


def test_update_number_zero() -> None:
    assert updated_cells({"Steps": 0})[7] == "0"


def test_update_note() -> None:
    assert updated_cells({}, "Updated highlight")[2] == "Updated highlight"


def test_preserve_other_cells() -> None:
    cells = updated_cells({"Hydrate": True, "Steps": 3}, "Updated highlight")

    assert cells[0] == "15"
    assert cells[1] == "Fri"
    assert cells[4] == "[ ]"
    assert cells[5] == "[ ]"
    assert cells[6] == "[ ]"


def rebuild_for_day_15() -> str:
    parsed = parsed_table()
    row = monthly_day.find_day_row(parsed.rows, 15)
    updated_row = monthly_day.update_row_cells(
        row,
        parsed.header_cells,
        {"Hydrate": True, "Steps": 3},
        {"Hydrate": "checkbox", "Steps": "number"},
        "Updated highlight",
    )
    return monthly_day.rebuild_body(parsed, parsed.rows.index(row), updated_row)


def test_rebuild_body_preserves_goals_section() -> None:
    rebuilt = rebuild_for_day_15()

    assert "- [ ] Ship a focused monthly workflow" in rebuilt
    assert "## Main Goals of the Month" in rebuilt


def test_rebuild_body_preserves_other_rows() -> None:
    rebuilt = rebuild_for_day_15()

    assert "| 14 | Thu | Budget check | [ ] | [ ] | [ ] | [ ] | 0 |" in rebuilt
    assert "| 16 | Sat | Family visit | [ ] | [ ] | [ ] | [ ] | 0 |" in rebuilt


def test_rebuild_body_updates_target_cells() -> None:
    rebuilt = rebuild_for_day_15()

    assert "Updated highlight" in rebuilt
    assert "[x]" in rebuilt
    assert "| 3 |" in rebuilt


def test_parse_date_valid() -> None:
    assert monthly_day.month_key_from_date("2026-05-15") == "2026-05"


def test_parse_date_invalid() -> None:
    with pytest.raises(ValueError):
        _ = monthly_day.month_key_from_date("2026-05-99")


def test_parse_field_args() -> None:
    assert monthly_day.parse_field_arg("Hydrate=true") == ("Hydrate", "true")


def test_parse_field_malformed() -> None:
    with assert_exits_with_code(1):
        _ = monthly_day.parse_field_arg("Hydrate:true")


def test_full_update_flow(tmp_path: Path) -> None:
    config_dir = write_config(tmp_path)
    note = {"id": "may-note-id", "title": "May", "body": sample_body()}
    calls: list[Request] = []

    def fake_urlopen(request: Request) -> FakeResponse:
        calls.append(request)
        if request.get_method() == "GET":
            return FakeResponse(json.dumps(note).encode("utf-8"))
        return FakeResponse(b"{}")

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        run_main(
            [
                "--date",
                "2026-05-15",
                "--field",
                "Hydrate=true",
                "--field",
                "Steps=3",
                "--note",
                "Updated highlight",
                "--config-dir",
                str(config_dir),
            ],
        )

    assert [call.get_method() for call in calls] == ["GET", "PUT"]
    put_data = calls[1].data
    assert put_data is not None
    put_payload = cast(dict[str, str], json.loads(cast(bytes, put_data).decode("utf-8")))
    put_body = put_payload["body"]
    assert "Updated highlight" in put_body
    assert "[x]" in put_body
    assert "| 3 |" in put_body


def test_api_get_failure(tmp_path: Path) -> None:
    config_dir = write_config(tmp_path)

    with patch("urllib.request.urlopen", side_effect=http_error()), assert_exits_with_code(2):
        run_main(
            [
                "--date",
                "2026-05-15",
                "--field",
                "Hydrate=true",
                "--config-dir",
                str(config_dir),
            ],
        )


def test_api_put_failure(tmp_path: Path) -> None:
    config_dir = write_config(tmp_path)
    note = {"id": "may-note-id", "title": "May", "body": sample_body()}

    with (
        patch(
            "urllib.request.urlopen",
            side_effect=[FakeResponse(json.dumps(note).encode("utf-8")), http_error()],
        ),
        assert_exits_with_code(2),
    ):
        run_main(
            [
                "--date",
                "2026-05-15",
                "--field",
                "Hydrate=true",
                "--config-dir",
                str(config_dir),
            ],
        )


def test_token_not_in_error_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config_dir = write_config(tmp_path)

    with patch("urllib.request.urlopen", side_effect=http_error()), assert_exits_with_code(2):
        run_main(
            [
                "--date",
                "2026-05-15",
                "--field",
                "Hydrate=true",
                "--config-dir",
                str(config_dir),
            ],
        )

    assert "fake-secret-token" not in capsys.readouterr().err


def test_dry_run_prints_body_skips_put(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config_dir = write_config(tmp_path)
    note = {"id": "may-note-id", "title": "May", "body": sample_body()}

    with patch(
        "urllib.request.urlopen",
        return_value=FakeResponse(json.dumps(note).encode("utf-8")),
    ) as urlopen_mock:
        run_main(
            [
                "--date",
                "2026-05-15",
                "--field",
                "Hydrate=true",
                "--config-dir",
                str(config_dir),
                "--dry-run",
            ],
        )

    assert urlopen_mock.call_count == 1
    assert "|  15  |  Fri  |  Demo day  | [x] |" in capsys.readouterr().out


def test_dry_run_still_validates_get(tmp_path: Path) -> None:
    config_dir = write_config(tmp_path)

    with patch("urllib.request.urlopen", side_effect=http_error()), assert_exits_with_code(2):
        run_main(
            [
                "--date",
                "2026-05-15",
                "--field",
                "Hydrate=true",
                "--config-dir",
                str(config_dir),
                "--dry-run",
            ],
        )

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import cast


@dataclass(frozen=True)
class TableRow:
    original_line: str
    cells: list[str]


@dataclass
class TableParsed:
    preamble: list[str]
    header_line: str
    separator_line: str
    rows: list[TableRow]
    postamble: list[str]
    header_cells: list[str]


def month_key_from_date(date_str: str) -> str:
    """Convert a date string in YYYY-MM-DD format to YYYY-MM format."""
    parsed = datetime.strptime(date_str, "%Y-%m-%d")
    return parsed.strftime("%Y-%m")


def load_joplin_credentials(config_dir: Path) -> tuple[str, str]:
    """Load Joplin credentials from config file.

    Reads KEY=VALUE lines from config_dir/joplin.env, strips quotes,
    ignores comments (#) and blank lines.

    Returns:
        tuple of (base_url, token)

    Exits with code 1 if:
    - Config file not found
    - Required variables not set
    """
    config_file = config_dir / "joplin.env"

    if not config_file.exists():
        print(f"Error: Config file not found: {config_file}", file=sys.stderr)
        sys.exit(1)

    joplin_base_url: str | None = None
    joplin_token: str | None = None

    with open(config_file, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            # Skip comments and blank lines
            if not stripped or stripped.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, raw_value = line.split("=", 1)
            key = key.strip()
            value = raw_value.strip()

            # Strip quotes if present
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]

            if key == "JOPLIN_BASE_URL":
                joplin_base_url = value
            elif key == "JOPLIN_TOKEN":
                joplin_token = value

    if joplin_base_url is None:
        print(
            f"Error: JOPLIN_BASE_URL not set in {config_file}.", file=sys.stderr
        )
        sys.exit(1)

    if joplin_token is None:
        print(f"Error: JOPLIN_TOKEN not set in {config_file}.", file=sys.stderr)
        sys.exit(1)

    return (joplin_base_url, joplin_token)


def load_planner_state(config_dir: Path) -> dict[str, object]:
    """Load planner state from JSON file.

    Reads and parses config_dir/planner-state.json.

    Returns:
        Parsed JSON as dict

    Exits with code 1 if:
    - File not found
    - Invalid JSON
    """
    state_file = config_dir / "planner-state.json"

    if not state_file.exists():
        print(
            f"Error: planner-state.json not found at {state_file}.", file=sys.stderr
        )
        sys.exit(1)

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            loaded = cast(object, json.load(f))
    except json.JSONDecodeError:
        print("Error: planner-state.json is not valid JSON.", file=sys.stderr)
        sys.exit(1)

    if not isinstance(loaded, dict):
        print("Error: planner-state.json root must be an object.", file=sys.stderr)
        sys.exit(1)

    return cast(dict[str, object], loaded)


def get_month_config(state: dict[str, object], month_key: str) -> dict[str, object]:
    """Extract and validate month configuration from state.

    Args:
        state: The planner state dict
        month_key: The month key in YYYY-MM format

    Returns:
        The month config dict with note_id and fields

    Exits with code 1 if:
    - Month key not found in state
    - note_id missing or empty
    - fields missing or empty
    """
    monthly_planner = state.get("monthly_planner")

    if not isinstance(monthly_planner, dict):
        print("Error: monthly_planner key not found in planner-state.json.", file=sys.stderr)
        sys.exit(1)
    monthly_planner_config = cast(dict[str, object], monthly_planner)

    month_config = monthly_planner_config.get(month_key)

    if not isinstance(month_config, dict):
        print(f"Error: No configuration found for {month_key} in planner-state.json.", file=sys.stderr)
        sys.exit(1)
    month_config_values = cast(dict[str, object], month_config)

    note_id = month_config_values.get("note_id")

    if not isinstance(note_id, str) or note_id == "":
        print(f"Error: note_id is missing or empty for {month_key}.", file=sys.stderr)
        sys.exit(1)

    fields = month_config_values.get("fields")

    if not isinstance(fields, dict):
        print(f"Error: fields is missing or empty for {month_key}.", file=sys.stderr)
        sys.exit(1)
    fields_config = cast(dict[str, object], fields)

    if len(fields_config) == 0:
        print(f"Error: fields is missing or empty for {month_key}.", file=sys.stderr)
        sys.exit(1)

    return month_config_values


def parse_field_arg(arg: str) -> tuple[str, str]:
    if "=" not in arg:
        print("Error: Malformed field argument '%s' (missing '=')" % arg, file=sys.stderr)
        sys.exit(1)
    name, raw_value = arg.split("=", 1)
    return (name, raw_value)


def coerce_checkbox(raw: str, field_name: str = "<unknown>") -> bool:
    normalized = raw.lower()

    if normalized == "true":
        return True
    if normalized == "false":
        return False

    print(
        f"Error: Field '{field_name}' expects true/false, got '{raw}'.",
        file=sys.stderr,
    )
    sys.exit(1)


def coerce_number(raw: str, field_name: str = "<unknown>") -> int:
    if raw.isdigit():
        return int(raw)

    print(
        f"Error: Field '{field_name}' expects a non-negative integer, got '{raw}'.",
        file=sys.stderr,
    )
    sys.exit(1)


def validate_fields(
    field_args: list[tuple[str, str]], schema: dict[str, str]
) -> dict[str, bool | int]:
    unknown_fields = [name for name, _raw_value in field_args if name not in schema]

    if unknown_fields:
        unknown_list = ", ".join(unknown_fields)
        valid_fields = ", ".join(schema.keys())
        print(
            f"Error: Unknown field(s): {unknown_list}. Valid fields: {valid_fields}.",
            file=sys.stderr,
        )
        sys.exit(1)

    typed_fields: dict[str, bool | int] = {}

    for name, raw_value in field_args:
        field_type = schema[name]

        if field_type == "checkbox":
            typed_fields[name] = coerce_checkbox(raw_value, name)
        elif field_type == "number":
            typed_fields[name] = coerce_number(raw_value, name)
        else:
            message = (
                f"Error: Unknown field type '{field_type}' for field '{name}'. "
                "Supported types: checkbox, number."
            )
            print(
                message,
                file=sys.stderr,
            )
            sys.exit(1)

    return typed_fields


def parse_table_cells(line: str) -> list[str]:
    """Parse a pipe-delimited Markdown table line without outer-pipe artifacts."""
    return line.rstrip("\r\n").split("|")[1:-1]


def parse_monthly_table(body: str, note_id: str = "<unknown>") -> TableParsed:
    """Parse the first monthly tracker table headed by '| Day |'."""
    lines = body.splitlines(keepends=True)

    header_index: int | None = None
    for index, line in enumerate(lines):
        if line.strip().startswith("| Day |"):
            header_index = index
            break

    if header_index is None:
        message = (
            "Error: Could not find the tracker table (header starting with '| Day |') "
            f"in note '{note_id}'."
        )
        print(
            message,
            file=sys.stderr,
        )
        sys.exit(1)

    separator_index = header_index + 1
    separator_line = lines[separator_index] if separator_index < len(lines) else ""
    row_start_index = separator_index + 1
    row_end_index = row_start_index

    while row_end_index < len(lines) and lines[row_end_index].strip().startswith("|"):
        row_end_index += 1

    rows = [
        TableRow(original_line=line, cells=parse_table_cells(line))
        for line in lines[row_start_index:row_end_index]
    ]

    return TableParsed(
        preamble=lines[:header_index],
        header_line=lines[header_index],
        separator_line=separator_line,
        rows=rows,
        postamble=lines[row_end_index:],
        header_cells=parse_table_cells(lines[header_index]),
    )


def find_day_row(rows: list[TableRow], day: int) -> TableRow:
    """Find the table row for a 1-based day of month."""
    target_day = f"{day:02d}"

    for row in rows:
        if row.cells and row.cells[0].strip() == target_day:
            return row

    print(f"Error: No row for day {target_day} in the tracker table.", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update a monthly day entry in Joplin.",
    )
    _ = parser.add_argument(
        "--date",
        type=str,
        required=True,
        help="Date in YYYY-MM-DD format",
    )
    _ = parser.add_argument(
        "--field",
        type=str,
        action="append",
        required=True,
        help="Field to update in name=value format (repeatable)",
    )
    _ = parser.add_argument(
        "--note",
        type=str,
        default=None,
        help="Optional note to add",
    )
    _ = parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("~/.config/hermes-personal/"),
        help="Config directory path (default: ~/.config/hermes-personal/)",
    )
    _ = parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )
    _ = parser.add_argument(
        "--body-file",
        type=Path,
        default=None,
        help=argparse.SUPPRESS,
    )

    args = parser.parse_args()
    date = cast(str, args.date)
    field_args = cast(list[str], args.field)
    note = cast(str | None, args.note)
    config_dir_arg = cast(Path, args.config_dir)
    dry_run = cast(bool, args.dry_run)
    body_file = cast(Path | None, args.body_file)

    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        sys.exit(1)

    fields: list[tuple[str, str]] = [parse_field_arg(field) for field in field_args]
    config_dir = config_dir_arg.expanduser()

    # Parse date and get month key
    month_key = month_key_from_date(date)

    # Load planner state (before credentials - lazy load)
    state = load_planner_state(config_dir)

    # Get month configuration
    month_config = get_month_config(state, month_key)
    schema = cast(dict[str, str], month_config["fields"])
    typed_fields = validate_fields(fields, schema)

    # Load credentials after state validation
    joplin_base_url, _joplin_token = load_joplin_credentials(config_dir)
    note_id = cast(str, month_config["note_id"])

    if body_file is not None:
        body = body_file.read_text(encoding="utf-8")
        parsed_table = parse_monthly_table(body, note_id)
        day_row = find_day_row(parsed_table.rows, parsed_date.day)
    else:
        parsed_table = None
        day_row = None

    message_template = (
        "Business logic not yet implemented. "
        + "Parsed args: date=%s, month_key=%s, fields=%s, note=%s, "
        + "config_dir=%s, dry_run=%s, joplin_base_url=%s, month_config=%s, "
        + "parsed_table=%s, day_row=%s"
    )
    message = message_template % (
        date,
        month_key,
        typed_fields,
        note,
        config_dir,
        dry_run,
        joplin_base_url,
        month_config,
        parsed_table,
        day_row,
    )
    raise NotImplementedError(message)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as e:
        print("Error: %s" % e, file=sys.stderr)
        sys.exit(3)

from __future__ import annotations

import argparse
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from http.client import HTTPResponse
import json
from pathlib import Path
import sys
from typing import cast
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.parse import quote
from urllib.parse import urlencode
from urllib.request import Request
from urllib.request import urlopen


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


def sanitize_error_message(message: str, token: str) -> str:
    """Redact the Joplin token from user-visible errors."""
    if token == "":
        return message
    return message.replace(token, "<redacted>")


def joplin_note_url(base_url: str, token: str, note_id: str) -> str:
    """Build the Joplin note endpoint URL with token and required fields."""
    query = urlencode({"token": token, "fields": "id,body,title"})
    return f"{base_url.rstrip('/')}/notes/{quote(note_id)}?{query}"


def joplin_get_note(base_url: str, token: str, note_id: str) -> dict[str, object]:
    """Fetch a single Joplin note by ID."""
    url = joplin_note_url(base_url, token, note_id)
    request = Request(url, method="GET")

    try:
        response = cast(HTTPResponse, urlopen(request))  # noqa: S310 - local Joplin URL
        with closing(response):
            response_body = response.read().decode("utf-8")
        loaded = cast(object, json.loads(response_body))
    except HTTPError as exc:
        message = f"Error: Joplin GET failed with HTTP {exc.code}: {exc.reason}"
        print(sanitize_error_message(message, token), file=sys.stderr)
        sys.exit(2)
    except URLError as exc:
        message = f"Error: Joplin GET failed: {exc.reason}"
        print(sanitize_error_message(message, token), file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError:
        print("Error: Joplin GET returned invalid JSON.", file=sys.stderr)
        sys.exit(2)

    if not isinstance(loaded, dict):
        print("Error: Joplin GET returned a non-object response.", file=sys.stderr)
        sys.exit(2)

    return cast(dict[str, object], loaded)


def joplin_put_note(base_url: str, token: str, note_id: str, body: str) -> None:
    """Update a single Joplin note body by ID."""
    url = joplin_note_url(base_url, token, note_id)
    payload = json.dumps({"body": body}).encode("utf-8")
    request = Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="PUT",
    )

    try:
        response = cast(HTTPResponse, urlopen(request))  # noqa: S310 - local Joplin URL
        with closing(response):
            _ = response.read()
    except HTTPError as exc:
        message = f"Error: Joplin PUT failed with HTTP {exc.code}: {exc.reason}"
        print(sanitize_error_message(message, token), file=sys.stderr)
        sys.exit(2)
    except URLError as exc:
        message = f"Error: Joplin PUT failed: {exc.reason}"
        print(sanitize_error_message(message, token), file=sys.stderr)
        sys.exit(2)


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


def update_row_cells(
    row: TableRow,
    header: list[str],
    updates: dict[str, bool | int],
    field_types: dict[str, str],
    note: str | None,
) -> str:
    """Apply field updates to a monthly tracker table row."""
    if len(header) == 1 and "|" in header[0]:
        header_cells = parse_table_cells(header[0])
    else:
        header_cells = header

    column_indexes = {cell.strip(): index for index, cell in enumerate(header_cells)}
    cells = row.cells.copy()

    for field_name, value in updates.items():
        if field_name not in column_indexes:
            print(f"Error: Field '{field_name}' is not present in the tracker table.", file=sys.stderr)
            sys.exit(1)

        field_type = field_types[field_name]
        column_index = column_indexes[field_name]

        if field_type == "checkbox":
            cells[column_index] = "[x]" if value else "[ ]"
        elif field_type == "number":
            cells[column_index] = str(value)
        else:
            print(
                f"Error: Unknown field type '{field_type}' for field '{field_name}'.",
                file=sys.stderr,
            )
            sys.exit(1)

    if note is not None:
        cells[2] = note

    return "| " + " | ".join(cells) + " |"


def rebuild_body(parsed: TableParsed, updated_row_index: int, updated_row_text: str) -> str:
    """Rebuild a note body with one tracker table row replaced."""
    lines = parsed.preamble + [parsed.header_line, parsed.separator_line]

    for index, row in enumerate(parsed.rows):
        if index == updated_row_index:
            if row.original_line.endswith("\r\n"):
                line_ending = "\r\n"
            elif row.original_line.endswith("\n"):
                line_ending = "\n"
            else:
                line_ending = ""
            lines.append(updated_row_text + line_ending)
        else:
            lines.append(row.original_line)

    lines.extend(parsed.postamble)
    return "".join(lines)


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

    note_id = cast(str, month_config["note_id"])
    joplin_base_url = ""
    joplin_token = ""

    if body_file is not None:
        body = body_file.read_text(encoding="utf-8")
    else:
        # Load credentials after state validation.
        joplin_base_url, joplin_token = load_joplin_credentials(config_dir)
        joplin_note = joplin_get_note(joplin_base_url, joplin_token, note_id)
        note_body = joplin_note.get("body")

        if not isinstance(note_body, str):
            print("Error: Joplin note response is missing a string body.", file=sys.stderr)
            sys.exit(2)

        body = note_body

    parsed_table = parse_monthly_table(body, note_id)
    day_row = find_day_row(parsed_table.rows, parsed_date.day)
    updated_row_index = parsed_table.rows.index(day_row)
    updated_row_text = update_row_cells(
        day_row,
        parsed_table.header_cells,
        typed_fields,
        schema,
        note,
    )
    updated_body = rebuild_body(parsed_table, updated_row_index, updated_row_text)

    if body_file is not None:
        _ = sys.stdout.write(updated_body)
        return

    if dry_run:
        _ = sys.stdout.write(updated_body)
        return

    joplin_put_note(joplin_base_url, joplin_token, note_id, updated_body)
    print(f"Updated day {parsed_date.day:02d} in monthly planner for {month_key}.")


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

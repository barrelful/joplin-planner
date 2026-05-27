from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any


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


def load_planner_state(config_dir: Path) -> dict[str, Any]:
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
            return json.load(f)  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        print("Error: planner-state.json is not valid JSON.", file=sys.stderr)
        sys.exit(1)


def get_month_config(state: dict[str, Any], month_key: str) -> dict[str, Any]:
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

    if monthly_planner is None:
        print("Error: monthly_planner key not found in planner-state.json.", file=sys.stderr)
        sys.exit(1)

    month_config = monthly_planner.get(month_key)

    if month_config is None:
        print(f"Error: No configuration found for {month_key} in planner-state.json.", file=sys.stderr)
        sys.exit(1)

    note_id = month_config.get("note_id")

    if note_id is None or note_id == "":
        print(f"Error: note_id is missing or empty for {month_key}.", file=sys.stderr)
        sys.exit(1)

    fields = month_config.get("fields")

    if fields is None or not isinstance(fields, dict) or len(fields) == 0:
        print(f"Error: fields is missing or empty for {month_key}.", file=sys.stderr)
        sys.exit(1)

    return month_config  # type: ignore[no-any-return]


def parse_field_arg(arg: str) -> tuple[str, str]:
    if "=" not in arg:
        print("Error: Malformed field argument '%s' (missing '=')" % arg, file=sys.stderr)
        sys.exit(1)
    name, raw_value = arg.split("=", 1)
    return (name, raw_value)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update a monthly day entry in Joplin.",
    )
    parser.add_argument(
        "--date",
        type=str,
        required=True,
        help="Date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--field",
        type=str,
        action="append",
        required=True,
        help="Field to update in name=value format (repeatable)",
    )
    parser.add_argument(
        "--note",
        type=str,
        default=None,
        help="Optional note to add",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("~/.config/hermes-personal/"),
        help="Config directory path (default: ~/.config/hermes-personal/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )

    args = parser.parse_args()

    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        sys.exit(1)

    fields: list[tuple[str, str]] = [parse_field_arg(f) for f in args.field]
    config_dir = args.config_dir.expanduser()

    # Parse date and get month key
    month_key = month_key_from_date(args.date)

    # Load planner state (before credentials - lazy load)
    state = load_planner_state(config_dir)

    # Get month configuration
    month_config = get_month_config(state, month_key)

    # Load credentials after state validation
    joplin_base_url, joplin_token = load_joplin_credentials(config_dir)

    raise NotImplementedError(
        "Business logic not yet implemented. "
        "Parsed args: date=%s, month_key=%s, fields=%s, note=%s, config_dir=%s, dry_run=%s, "
        "joplin_base_url=%s, month_config=%s"
        % (args.date, month_key, fields, args.note, config_dir, args.dry_run, joplin_base_url, month_config)
    )


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

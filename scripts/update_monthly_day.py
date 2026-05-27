import argparse
from datetime import datetime
from pathlib import Path
import sys


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

    raise NotImplementedError(
        "Business logic not yet implemented. "
        "Parsed args: date=%s, fields=%s, note=%s, config_dir=%s, dry_run=%s"
        % (args.date, fields, args.note, config_dir, args.dry_run)
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

# pyright: reportAny=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnusedCallResult=false
import argparse
from datetime import date
from datetime import datetime
from datetime import timedelta
import os
import sys

# Adiciona a pasta 'src' no caminho de módulos
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from day_planner import generate_daily_planner  # pyright: ignore[reportMissingImports]
from month_planner import generate_monthly_planner  # pyright: ignore[reportMissingImports]
from week_planner import generate_weekly_planner  # pyright: ignore[reportMissingImports]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Joplin Planner Generator. Use 'monthly', 'weekly', or 'daily' subcommands.",
    )
    subparsers = parser.add_subparsers(dest="planner_type", required=True)

    # Monthly planner arguments
    month_parser = subparsers.add_parser("monthly", help="Generate a monthly planner")
    month_parser.add_argument(
        "--habits",
        type=str,
        nargs="*",
        default=[],
        help="List of habit names (max 5)",
    )
    month_parser.add_argument(
        "--next",
        action="store_true",
        help="Generate for next month instead of current month",
    )

    # Weekly planner arguments
    week_parser = subparsers.add_parser("weekly", help="Generate a weekly planner")
    week_parser.add_argument(
        "--start",
        type=int,
        default=8,
        help="Start hour of the day (0-23), e.g., 8 for 08:00",
    )
    week_parser.add_argument(
        "--end",
        type=int,
        default=22,
        help="End hour of the day (1-24), e.g., 22 for 22:00",
    )
    week_parser.add_argument(
        "--interval",
        type=int,
        choices=[1, 2],
        default=2,
        help="Interval between time blocks: 1 for hourly, 2 for every 2 hours",
    )
    week_parser.add_argument(
        "--format",
        choices=["12h", "24h"],
        default="24h",
        help="Hour format: 12h (e.g., 08:00 AM) or 24h (e.g., 08:00)",
    )
    week_parser.add_argument(
        "--next",
        action="store_true",
        help="Generate for next week instead of current week",
    )

    # Daily planner arguments
    day_parser = subparsers.add_parser("daily", help="Generate a daily planner")
    day_parser.add_argument(
        "--date",
        type=str,
        help="Date to generate for in YYYY-MM-DD format",
    )
    day_parser.add_argument(
        "--today",
        action="store_true",
        help="Generate for today",
    )
    day_parser.add_argument(
        "--tomorrow",
        action="store_true",
        help="Generate for tomorrow",
    )
    day_parser.add_argument(
        "--fun-dates",
        type=str,
        help="Path to fun dates JSON file",
    )
    day_parser.add_argument(
        "--holiday-region",
        type=str,
        default="england-and-wales",
        help="Holiday region to use",
    )
    day_parser.add_argument(
        "--no-holidays",
        action="store_true",
        help="Do not include holidays",
    )
    day_parser.add_argument(
        "--no-fun-dates",
        action="store_true",
        help="Do not include fun dates",
    )

    args = parser.parse_args()

    if args.planner_type == "monthly":
        habit_names = args.habits[:5]
        md = generate_monthly_planner(
            num_habits=len(habit_names),
            habit_names=habit_names,
            target_month="next" if args.next else "current",
        )
    elif args.planner_type == "weekly":
        md = generate_weekly_planner(
            time_start=args.start,
            time_end=args.end,
            hour_format=args.format,
            interval_hours=args.interval,
            next_week=args.next,
        )
    elif args.planner_type == "daily":
        from pathlib import Path

        if args.date:
            try:
                target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
            except ValueError:
                print("Invalid date format. Use YYYY-MM-DD.", file=sys.stderr)
                sys.exit(1)
        elif args.tomorrow:
            target_date = date.today() + timedelta(days=1)
        else:
            target_date = date.today()

        md = generate_daily_planner(
            date=target_date,
            fun_dates_path=Path(args.fun_dates) if args.fun_dates else None,
            holiday_region=args.holiday_region,
            include_holidays=not args.no_holidays,
            include_fun_dates=not args.no_fun_dates,
        )
    else:
        raise ValueError(f"Unsupported planner type: {args.planner_type}")

    print(md)


if __name__ == "__main__":
    main()

import argparse
import os
import sys

# Adiciona a pasta 'src' no caminho de módulos
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from month_planner import generate_monthly_planner
from src.week_planner import generate_weekly_planner


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Joplin Planner Generator. Use 'monthly' or 'weekly' subcommands.",
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

    print(md)


if __name__ == "__main__":
    main()

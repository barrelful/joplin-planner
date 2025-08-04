from datetime import datetime
from datetime import timedelta


def generate_weekly_planner(
    time_start: int = 8,
    time_end: int = 22,
    hour_format: str = "24h",
    interval_hours: int = 2,
    next_week: bool = False,
) -> str:
    """
    Generates a weekly planner in Markdown format.
    """

    assert hour_format in ["12h", "24h"], "hour_format must be '12h' or '24h'"
    assert interval_hours in [1, 2], "interval_hours must be 1 or 2"
    assert 0 <= time_start < time_end <= 24, "Invalid time range"

    today = datetime.today()
    monday = today - timedelta(days=today.weekday())
    if next_week:
        monday += timedelta(weeks=1)
    days = [monday + timedelta(days=i) for i in range(7)]

    # Header
    start_str = days[0].strftime("%d")
    end_str = days[-1].strftime("%dth of %B %Y")
    header = f"# 🗓️ Weekly Planner – {start_str} to {end_str}\n\n"

    # Objectives section
    objectives = """## Overview and main objective

Week brief summary and goal

- [ ] Objective 1
- [ ] Objective 2

"""

    # Table header
    day_headers = [d.strftime("%d/%m") for d in days]
    weekday_names = [d.strftime("%A") for d in days]
    table = "## Weak planner\n\n"
    table += "|     | " + " | ".join(day_headers) + " |\n"
    table += "| --- |" + " --- |" * len(day_headers) + "\n"
    table += "| --- | " + " | ".join(weekday_names) + " |\n"

    # Time slots
    for hour in range(time_start, time_end, interval_hours):
        start = datetime(2000, 1, 1, hour)
        end = datetime(2000, 1, 1, hour + interval_hours)

        if hour_format == "12h":
            time_label = f"{start.strftime('%I:%M %p')} to {end.strftime('%I:%M %p')}"
        else:
            time_label = f"{start.strftime('%H:%M')} to {end.strftime('%H:%M')}"

        table += f"| {time_label} | " + " | ".join(["" for _ in range(7)]) + " |\n"

    return header + objectives + table

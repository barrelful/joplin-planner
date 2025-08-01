import calendar
from datetime import date
from typing import List


def generate_monthly_md(
    num_habits: int,
    habit_names: List[str],
    target_month: str = "current",
) -> str:
    assert 0 <= num_habits <= 5, "You can track up to 5 habits."

    today = date.today()
    if target_month == "next":
        month = today.month + 1 if today.month < 12 else 1
        year = today.year if today.month < 12 else today.year + 1
    else:
        month = today.month
        year = today.year

    # Get the number of days in the month
    num_days = calendar.monthrange(year, month)[1]

    # Header
    month_name = calendar.month_name[month]
    output = [f"# Monthly Planner – {month_name} {year}\n"]
    output.append(
        f"**First day of the month:** {date(year, month, 1).strftime('%A, %B %d, %Y')}\n",
    )

    # Table header
    headers = ["Day", "Weekday", "Highlight"] + habit_names
    output.append("| " + " | ".join(headers) + " |")
    output.append("|" + "|".join(["---"] * len(headers)) + "|")

    # Table rows
    for day in range(1, num_days + 1):
        current_date = date(year, month, day)
        weekday = current_date.strftime("%a")
        row = [f"{day:02}", weekday, ""]
        row += ["[ ]" for _ in range(num_habits)]
        output.append("| " + " | ".join(row) + " |")

    # Goals section
    output.append("\n## Main Goals of the Month\n")
    output.append("- [ ] Goal 1")
    output.append("- [ ] Goal 2")
    output.append("- [ ] Goal 3")

    return "\n".join(output)

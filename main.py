import os
import sys
from typing import Any
from typing import Callable
from typing import List
from typing import Optional
from typing import TypeVar
from typing import cast

import typer

# Add the 'src' folder to the Python module search path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Import the function from the correct file
from month_planner import generate_monthly_md

app = typer.Typer()

# Define a type variable for the command decorator
F = TypeVar("F", bound=Callable[..., Any])


def validate_month(value: str) -> str:
    """Validate that month is either 'current' or 'next'."""
    if value not in ["current", "next"]:
        raise typer.BadParameter("Month must be either 'current' or 'next'")
    return value


# Create a properly typed command decorator
def command(func: F) -> F:
    """Typed wrapper for Typer's command decorator."""
    return cast(F, app.command()(func))


@command
def monthly(
    habits: Optional[List[str]] = typer.Argument(None, help="Names of habits to track (max 5)."),
    month: str = typer.Option(
        "current",
        help="Choose current or next month.",
        callback=validate_month,
    ),
    output: str = typer.Option("monthly_planner.md", help="Output markdown file."),
) -> None:
    """
    🗓️ Generate a monthly planner.

    Example:
        $ python main.py monthly Meditate Duolingo Workout Diet --month next --output next_month.md
    """
    if habits is None:
        habits = []

    # Validate number of habits
    if len(habits) > 5:
        raise ValueError("You can track up to 5 habits.")

    # Call the generate_monthly_md function with the correct parameters
    md_content = generate_monthly_md(len(habits), habits, month)

    # Save the output to the specified file
    with open(output, "w", encoding="utf-8") as f:
        f.write(md_content)


if __name__ == "__main__":
    app()

# main.py
from functools import wraps
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


# Create a properly typed command decorator with workaround for MyPy
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


# Create a typed version of the callback decorator
def typed_callback(*args: Any, **kwargs: Any) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return cast(F, app.callback(*args, **kwargs)(wrapper))

    return decorator


@typed_callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Show help message if no command is provided."""
    if ctx.invoked_subcommand is None:
        print("Error: No planner type specified.")
        print("Please specify a planner type (monthly, weekly, etc.)")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

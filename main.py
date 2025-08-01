import os
import sys
from typing import List

import click

# Add the 'src' folder to the Python module search path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Import the function from the correct file
from month_planner import generate_monthly_md


@click.group()
def cli() -> None:
    """📆 Joplin Planner: Generate markdown planners for Joplin."""
    pass


@cli.command()
@click.option("--habits", "-h", multiple=True, help="Names of habits to track (max 5).")
@click.option(
    "--month",
    "-m",
    type=click.Choice(["current", "next"]),
    default="current",
    help="Choose current or next month.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(writable=True),
    default="monthly_planner.md",
    help="Output markdown file.",
)
def monthly(habits: List[str], month: str, output: str) -> None:
    """🗓️ Generate a monthly planner."""
    # Convert habits tuple to list
    habits_list = list(habits)
    # Call the generate_monthly_md function with the correct parameters
    md_content = generate_monthly_md(len(habits_list), habits_list, month)

    # Save the output to the specified file
    with open(output, "w", encoding="utf-8") as f:
        f.write(md_content)


if __name__ == "__main__":
    cli()

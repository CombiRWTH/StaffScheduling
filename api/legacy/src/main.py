from datetime import datetime

import click

from src.db.export_main import main as fetcher
from src.db.import_main import main as inserter
from src.loader import FSLoader
from src.services.solve_service import execute_solve, execute_solve_multiple
from src.web import App


@click.group()
def cli():
    """Staff Scheduling CLI"""
    pass


@cli.command()
@click.argument("unit", type=click.INT)
@click.argument("start", type=click.DateTime(formats=["%d.%m.%Y"]))
@click.argument("end", type=click.DateTime(formats=["%d.%m.%Y"]))
@click.option("--weight", multiple=True, help="Override weights")
@click.option("--timeout", default=300, help="Timeout in seconds for the solver")
@click.option(
    "--solver-analyzer-log",
    default="",
    help="Log the CP-SAT output to the specified file (which can be used for e.g. analyzing the search process)",
)
def solve(unit: int, start: datetime, end: datetime, weight: tuple[str, ...], timeout: int, solver_analyzer_log: str):
    """Solve the scheduling problem for a given case and start date.

    UNIT is the case number to solve.

    START is the start date for the planning period in YYYY-MM-DD format.

    END is the end date for the planning period in YYYY-MM-DD format.
    """

    # Parse the CLI weight overrides into a dictionary
    weight_overrides: dict[str, int] = {}
    for w in weight:
        try:
            key, value = w.split("=")
            weight_overrides[key] = int(value)
        except ValueError:
            raise click.ClickException(f"Invalid --weight format: '{w}'. Use key=value.") from None

    click.echo(f"Creating staff schedule for planning unit {unit}...")

    try:
        execute_solve(
            unit=unit,
            start_date=start.date(),
            end_date=end.date(),
            timeout=timeout,
            weight_overrides=weight_overrides,
            analyzer_log=None if solver_analyzer_log == "" else solver_analyzer_log,
        )
    except ValueError as e:
        # Catch the "Unknown weight key" error from the service
        raise click.ClickException(str(e)) from None


@cli.command("solve-multiple")
@click.argument("unit", type=click.INT)
@click.argument("start", type=click.DateTime(formats=["%d.%m.%Y"]))
@click.argument("end", type=click.DateTime(formats=["%d.%m.%Y"]))
@click.option("--timeout", default=300, help="Timeout in seconds for the solver")
def solve_multiple(unit: int, start: datetime, end: datetime, timeout: int):
    """
    Solve the scheduling problem for a given case and start date.

    UNIT is the case number to solve.

    START is the start date for the planning period in YYYY-MM-DD format.

    END is the end date for the planning period in YYYY-MM-DD format.
    """

    def cli_callback(phase_name: str, weight_id: int, total_weights: int):
        click.echo(f"  [Weight Set {weight_id + 1}/{total_weights}] Phase: {phase_name}")

    click.echo(f"Starting multiple solves for planning unit {unit}...")

    execute_solve_multiple(unit, start.date(), end.date(), timeout, cli_callback)


@cli.command()
@click.argument("case", type=click.INT)
@click.option("--debug", is_flag=True, help="Run the plot in debug mode")
def plot(case: int, debug: bool):
    """
    Plot the solution for a given case.

    CASE is the case number to plot.
    """

    loader = FSLoader(case)
    app = App(loader=loader)
    app.run(debug=debug)


@cli.command()
@click.argument("unit", type=click.INT)
@click.argument("start", type=click.DateTime(formats=["%d.%m.%Y"]))
@click.argument("end", type=click.DateTime(formats=["%d.%m.%Y"]))
def fetch(unit: int, start: datetime, end: datetime):
    """
    Fetch data from the DB and write Json Files
    """
    start_date = start.date()  # convert datetime.datetime to datetime.date
    end_date = end.date()
    fetcher(planning_unit=unit, from_date=start_date, till_date=end_date)


@cli.command()
@click.argument("unit", type=click.INT)
@click.argument("start", type=click.DateTime(formats=["%d.%m.%Y"]))
@click.argument("end", type=click.DateTime(formats=["%d.%m.%Y"]))
def insert(unit: int, start: datetime, end: datetime):
    """
    Insert data from Json Solution Files to DB
    """
    start_date = start.date()  # convert datetime.datetime to datetime.date
    end_date = end.date()
    inserter(planning_unit=unit, from_date=start_date, till_date=end_date, cli_input="i")


@cli.command()
@click.argument("unit", type=click.INT)
@click.argument("start", type=click.DateTime(formats=["%d.%m.%Y"]))
@click.argument("end", type=click.DateTime(formats=["%d.%m.%Y"]))
def delete(unit: int, start: datetime, end: datetime):
    """
    Delete data from Json Solution Files to DB, effectivly resetting the changes
    stored in solution.
    """
    start_date = start.date()  # convert datetime.datetime to datetime.date
    end_date = end.date()
    inserter(planning_unit=unit, from_date=start_date, till_date=end_date, cli_input="d")


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()

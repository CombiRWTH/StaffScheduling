from datetime import datetime

import click

from src.db.export_main import main as fetcher
from src.db.import_main import main as inserter
from src.loader import FSLoader
from src.solve import main as solver
from src.web import App

from src.web.process_solution import process_solution


@click.group()
def cli():
    """Staff Scheduling CLI"""
    pass


@cli.command("process-solution")
@click.argument("case", type=click.INT)
@click.option("--filename", default=None, type=click.STRING)
@click.option("--output", default="processed_solution.json", type=click.STRING)
@click.option("--debug", is_flag=True, help="Enable debug output")
def export_json(case: int, debug: bool, filename: str = None, output: str = "processed_solution.json"):
    """
    Process a solution for a given CASE and export it as JSON.
    """

    loader = FSLoader(case)

    process_solution(loader=loader,output_filename=output, solution_file_name=filename)

@cli.command()
@click.argument("unit", type=click.INT)
@click.argument("start", type=click.DateTime(formats=["%d.%m.%Y"]))
@click.argument("end", type=click.DateTime(formats=["%d.%m.%Y"]))
@click.option("--timeout", default=300, help="Timeout in seconds for the solver")
def solve(unit: int, start: datetime, end: datetime, timeout: int):
    """
    Solve the scheduling problem for a given case and start date.

    UNIT is the case number to solve.

    START is the start date for the planning period in YYYY-MM-DD format.

    END is the end date for the planning period in YYYY-MM-DD format.
    """

    click.echo(f"Creating staff schedule for planning unit {unit} from {start.date()} to {end.date()}.")

    solver(
        unit=unit,
        start_date=start.date(),
        end_date=end.date(),
        timeout=timeout,
    )


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

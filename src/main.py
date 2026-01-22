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

    loader = FSLoader(unit, start_date=start.date(), end_date=end.date())

    solution_name = f"solution_{unit}_{start.date()}-{end.date()}_wdefault"

    process_solution(loader=loader, output_filename=solution_name + "_processed.json", solution_file_name=solution_name)


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
    weight_sets = [
        {
            "free_weekend": 2,
            "consecutive_nights": 2,
            "hidden": 100,
            "overtime": 4,
            "consecutive_days": 1,
            "rotate": 1,
            "wishes": 3,
            "after_night": 3,
            "second_weekend": 1,
        },
        {
            "free_weekend": 5,
            "consecutive_nights": 1,
            "hidden": 50,
            "overtime": 10,
            "consecutive_days": 1,
            "rotate": 2,
            "wishes": 3,
            "after_night": 1,
            "second_weekend": 1,
        },
        {
            "free_weekend": 0.1,
            "consecutive_nights": 5,
            "hidden": 80,
            "overtime": 1,
            "consecutive_days": 2,
            "rotate": 0,
            "wishes": 5,
            "after_night": 3,
            "second_weekend": 2,
        },
    ]

    for weight_id, weights in enumerate(weight_sets):
        click.echo(
            "Creating staff schedule for planning unit "
            f"{unit} from {start.date()} to {end.date()} "
            f"with weight set {weight_id}"
        )

        solver(
            unit=unit,
            start_date=start.date(),
            end_date=end.date(),
            timeout=timeout,
            weights=weights,
            weight_id=weight_id,
        )
        loader = FSLoader(unit, start_date=start.date(), end_date=end.date())

        in_name = f"solution_{unit}_{start.date()}-{end.date()}_w{weight_id}"

        process_solution(loader=loader, output_filename=in_name + "_processed.json", solution_file_name=in_name)


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

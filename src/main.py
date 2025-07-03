import click
from solve import main as solver
from plot import main as plotter
from loader import FSLoader


@click.group()
def cli():
    """Staff Scheduling CLI"""
    pass


@cli.command()
@click.argument("unit", type=click.INT)
@click.argument("start", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.argument("end", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option("--timeout", default=300, help="Timeout in seconds for the solver")
def solve(unit: int, start: click.DateTime, end: click.DateTime, timeout: int):
    """
    Solve the scheduling problem for a given case and start date.

    UNIT is the case number to solve.

    START is the start date for the planning period in YYYY-MM-DD format.

    END is the end date for the planning period in YYYY-MM-DD format.
    """

    click.echo(
        f"Creating staff schedule for planning unit {unit} from {start.date()} to {end.date()}."
    )

    loader = FSLoader(unit)
    solver(loader=loader, start_date=start.date(), end_date=end.date(), timeout=timeout)


@cli.command()
@click.argument("case", type=click.INT)
@click.option("--debug", is_flag=True, help="Run the plot in debug mode")
def plot(case: int, debug: bool):
    """
    Plot the solution for a given case.

    CASE is the case number to plot.
    """

    loader = FSLoader(case)
    plotter(loader=loader, debug=debug)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()

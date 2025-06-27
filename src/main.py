import click
from solve import main as solver
from plot import main as plotter
from loader import FSLoader


@click.group()
def cli():
    """Staff Scheduling CLI"""
    pass


@cli.command()
@click.argument("case", type=click.INT)
@click.option(
    "--date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default="2024-11-01",
    help="Start date in the format YYYY-MM-DD",
)
@click.option("--timeout", default=300, help="Timeout in seconds for the solver")
def solve(case: int, date: click.DateTime, timeout: int):
    """
    Solve the scheduling problem for a given case and start date.

    CASE is the case number to solve.
    """

    loader = FSLoader(case)
    solver(loader=loader, start_date=date.date(), timeout=timeout)


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

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
@click.argument("date", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option("--timeout", default=300, help="Timeout in seconds for the solver")
def solve(case: int, date: click.DateTime, timeout: int):
    loader = FSLoader(case)
    solver(loader=loader, start_date=date.date(), timeout=timeout)


@cli.command()
@click.argument("case", type=click.INT)
@click.option("--debug", is_flag=True, help="Run the plot in debug mode")
def plot(case: int, debug: bool):
    click.echo(f"Plotting case {case} with debug={debug}")
    loader = FSLoader(case)
    plotter(loader=loader, debug=debug)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()

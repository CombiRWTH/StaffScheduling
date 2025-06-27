import click
from solve import main as solver
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

def main():
    """Main entry point for the CLI."""
    cli()

if __name__ == "__main__":
    main()
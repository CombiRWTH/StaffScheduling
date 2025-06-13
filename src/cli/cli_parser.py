from argparse import ArgumentParser
from datetime import date
from cp import (
    Constraint,
)


class CLIParser:
    def __init__(self, constraints: list[Constraint]):
        self._parser = ArgumentParser(
            description="Staff scheduling for a given month and year."
        )

        self._parser.add_argument(
            "--id",
            "-i",
            type=int,
            default=2,
            help="ID of the cases folder to load",
        )

        self._parser.add_argument(
            "--month",
            "-m",
            type=int,
            choices=range(1, 13),
            default=11,
            help="Month to plan (1-12)",
        )
        self._parser.add_argument(
            "--year", "-y", type=int, default=2024, help="Year to plan"
        )
        self._parser.add_argument(
            "--output",
            "-o",
            nargs="+",
            default=["json"],
            help="Output formats (json, plot, print)",
        )
        constraint_keys = [f"{constraint.KEY}" for constraint in constraints]
        self._parser.add_argument(
            "--constraints",
            "-c",
            nargs="+",
            choices=constraint_keys,
            default=None,
            help=(
                "List of Constraints to switch on. Allowed values: "
                + ", ".join(constraint_keys)
            ),
        )

        self._args = self._parser.parse_args()

    def get_case_id(self) -> int:
        return self._args.id

    def get_start_date(self) -> date:
        return date(self._args.year, self._args.month, 1)

    def get_constraints(self) -> list[str] | None:
        return self._args.constraints if self._args.constraints else None

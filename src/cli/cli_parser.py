from argparse import ArgumentParser
from datetime import date


class CLIParser:
    def __init__(self):
        self._parser = ArgumentParser(
            description="Staff scheduling for a given month and year."
        )

        self._parser.add_argument(
            "--case-id",
            "-c",
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
        self._parser.add_argument(
            "--switch",
            "-s",
            nargs="+",
            choices=[
                "B",
                "FreeS",
                "Staff",
                "Tar",
                "MinN",
                "NSAN",
                "FreeW",
                "MFNW",
                "MaxC",
                "Rot",
            ],
            default=None,
            help=(
                "List of Constraints to switch on. Allowed values: "
                "B, FreeS, Staff, Tar, MinN, NSAN, FreeW, MFNW, MaxC, Rot"
            ),
        )

        self._args = self._parser.parse_args()

    def get_case_id(self) -> int:
        return self._args.case_id

    def get_start_date(self) -> date:
        return date(self._args.year, self._args.month, 1)

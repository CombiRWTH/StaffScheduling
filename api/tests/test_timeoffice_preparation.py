"""The prepared inputs of stations 77 and 79 and jumper pool 408 in the TimeOffice test database.

The units keep their existing employees; every other input comes from the SQL files in `timeoffice_preparation/`,
applied in name order. `just test-timeoffice` runs each file in one transaction, fails unless every read-back `ok`
is 1 and no write changes a row, and rolls back, so a pass shows that every prepared row is present and that a
rerun would change nothing. `TIMEOFFICE_PREPARATION=apply just test-timeoffice` commits each file instead, which
prepares a copy that lacks them; the next run without it must then pass.
"""

import os
from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy import Connection, Engine, text

from app.domain.calendar import public_holiday
from app.settings import get_settings
from app.timeoffice.database import create_db_engine
from app.timeoffice.facts import TIMEOFFICE_FACTS

pytestmark = pytest.mark.timeoffice

PREPARATION = Path(__file__).with_name("timeoffice_preparation")
WRITES = sorted(PREPARATION.glob("0*.sql"))
APPLY = os.environ.get("TIMEOFFICE_PREPARATION") == "apply"


@pytest.fixture(scope="module")
def engine() -> Iterator[Engine]:
    # The demand file writes about 2,000 rows in one statement, beyond the adapter's default query wait.
    engine = create_db_engine(get_settings().model_copy(update={"db_timeout_seconds": 30}))
    yield engine
    engine.dispose()


def run(connection: Connection, path: Path) -> int:
    """Execute a file's `GO`-separated statements and return the rows its writes changed.

    Statements that fill session temporary tables (`SELECT ... INTO #`) are not counted.
    """
    changed = 0
    for part in path.read_text(encoding="utf-8").split("\nGO\n"):
        if not (statement := "\n".join(line for line in part.splitlines() if not line.startswith("--")).strip()):
            continue
        result = connection.execute(text(statement))
        if result.returns_rows:
            rows = result.mappings().all()
            assert all(row["ok"] == 1 for row in rows if "ok" in row), f"{path.name}: {rows}"
        elif statement.startswith(("INSERT", "UPDATE", "DELETE")):
            changed += max(result.rowcount, 0)
    return changed


def test_preparation_is_applied(engine: Engine) -> None:
    changed: dict[str, int] = {}
    for path in WRITES:  # in order; a failing file stops the run before the later ones
        with engine.connect() as connection:
            transaction = connection.begin()
            changed[path.name] = run(connection, path)
            if APPLY:
                transaction.commit()
            else:
                transaction.rollback()
    assert APPLY or not any(changed.values()), f"rows changed: {changed}; apply with TIMEOFFICE_PREPARATION=apply"


def test_prepared_units_are_ready(engine: Engine) -> None:
    facts = TIMEOFFICE_FACTS
    days = (date(2026, 1, 1) + timedelta(days=offset) for offset in range(181))
    absence_codes = (*facts.availability_type_by_absence_code, *facts.ignored_availability_absence_codes)
    with engine.connect() as connection:
        connection.execute(
            text(
                "CREATE TABLE #profession_level"
                " (code nvarchar(32) COLLATE DATABASE_DEFAULT, lvl nvarchar(16) COLLATE DATABASE_DEFAULT)"
            )
        )
        connection.execute(
            text("INSERT INTO #profession_level VALUES (:code, :lvl)"),
            [{"code": code, "lvl": level.value} for code, level in facts.staff_level_by_profession_code.items()],
        )
        connection.execute(text("CREATE TABLE #absence_code (code nvarchar(16) COLLATE DATABASE_DEFAULT)"))
        connection.execute(text("INSERT INTO #absence_code VALUES (:code)"), [{"code": code} for code in absence_codes])
        connection.execute(
            text("CREATE TABLE #credited_absence (account int, code nvarchar(16) COLLATE DATABASE_DEFAULT)")
        )
        connection.execute(
            text("INSERT INTO #credited_absence VALUES (:account, :code)"),
            [{"account": a, "code": c} for a, c in facts.credited_absence_code_by_account_id.items()],
        )
        connection.execute(text("CREATE TABLE #holiday (d date)"))
        connection.execute(
            text("INSERT INTO #holiday VALUES (:d)"), [{"d": day} for day in days if public_holiday(day)]
        )
        run(connection, PREPARATION / "readiness.sql")

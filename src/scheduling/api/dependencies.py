from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine

from scheduling.settings import get_settings
from scheduling.solver.tmp import SolverService
from scheduling.timeoffice.database import TimeOfficeDatabase, create_db_engine
from scheduling.timeoffice.facts import TIMEOFFICE_FACTS, TimeOfficeFacts
from scheduling.timeoffice.repositories import TimeOfficeRepositories
from scheduling.timeoffice.service import TimeOfficeService


@lru_cache(maxsize=1)
def get_db_engine() -> Engine:
    """Create and cache the SQLAlchemy engine for the app process."""
    settings = get_settings()
    return create_db_engine(settings=settings)


def get_timeoffice_facts() -> TimeOfficeFacts:
    """Return static TimeOffice source facts."""
    return TIMEOFFICE_FACTS


@lru_cache(maxsize=1)
def get_timeoffice_repositories() -> TimeOfficeRepositories:
    """Create stateless TimeOffice repositories."""
    return TimeOfficeRepositories.create(facts=TIMEOFFICE_FACTS)


def get_timeoffice_database(
    engine: Annotated[Engine, Depends(get_db_engine)],
    repositories: Annotated[TimeOfficeRepositories, Depends(get_timeoffice_repositories)],
    facts: Annotated[TimeOfficeFacts, Depends(get_timeoffice_facts)],
) -> TimeOfficeDatabase:
    """Create the TimeOffice database gateway."""
    return TimeOfficeDatabase(engine=engine, repositories=repositories, facts=facts)


def get_timeoffice_service(
    database: Annotated[TimeOfficeDatabase, Depends(get_timeoffice_database)],
    facts: Annotated[TimeOfficeFacts, Depends(get_timeoffice_facts)],
) -> TimeOfficeService:
    """Create the high-level TimeOffice service."""
    return TimeOfficeService(database=database, facts=facts)


async def get_solver_service() -> SolverService:
    return SolverService()

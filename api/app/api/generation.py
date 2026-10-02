"""Start the full-month generation of the selected stations and follow the latest job."""

from typing import Annotated, Any, Protocol

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.shared import planning_errors
from app.solver.generation import GenerationBusy, GenerationJob, GenerationRequest

router = APIRouter()


class GenerationRunner(Protocol):
    def start(self, request: GenerationRequest) -> GenerationJob: ...

    def latest(self) -> GenerationJob | None: ...


def get_generation(request: Request) -> Any:
    return request.app.state.generation


Runner = Annotated[GenerationRunner, Depends(get_generation)]

INVALID = "Invalid generation: choose stations with a target plan for the month and reference shifts."
INCOMPLETE = "Generation input is incomplete. Save every station's staffing and verify the employee facts."


@router.post("/generation", status_code=status.HTTP_202_ACCEPTED)
def start_generation(body: GenerationRequest, runner: Runner) -> GenerationJob:
    """Validate the input, then solve in the background; poll `GET /generation` for the result."""
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        try:
            return runner.start(body)
        except GenerationBusy as error:
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(error)) from error


@router.get("/generation")
def get_latest_generation(runner: Runner) -> GenerationJob:
    if (job := runner.latest()) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No generation since the API started; results are lost when it restarts.",
        )
    return job

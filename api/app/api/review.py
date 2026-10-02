"""Review the latest schedule, import a portable pair of files and download the bundle."""

from typing import Annotated, Any, Protocol

from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile, status

from app.solver.bundle import EMPLOYEES_FILE, INPUT_FILE, RESULT_FILE, SCHEDULE_FILE, FileName
from app.solver.review import ScheduleReview

router = APIRouter()


class ScheduleReviewer(Protocol):
    def imported(self, input_json: bytes, result_json: bytes) -> ScheduleReview: ...

    def current(self) -> ScheduleReview | None: ...

    def file(self, name: FileName) -> bytes | None: ...


def get_review(request: Request) -> Any:
    return request.app.state.review


Reviewer = Annotated[ScheduleReviewer, Depends(get_review)]

NO_REVIEW = "No schedule to review: generate one or import an input.json/result.json pair. Lost when the API restarts."
MEDIA_TYPES: dict[FileName, str] = {
    INPUT_FILE: "application/json",
    RESULT_FILE: "application/json",
    SCHEDULE_FILE: "text/csv; charset=utf-8",
    EMPLOYEES_FILE: "text/csv; charset=utf-8",
}


@router.get("/review")
def get_current_review(reviewer: Reviewer) -> ScheduleReview:
    if (review := reviewer.current()) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NO_REVIEW)
    return review


@router.post("/review/import", responses={422: {"description": "Not a valid pair; `problem` names why."}})
def import_review(input: UploadFile, result: UploadFile, reviewer: Reviewer) -> ScheduleReview:
    """Review an uploaded input/result pair; a rejected pair (`InvalidBundle`) leaves the current review unchanged.

    Synchronous, so validating and re-checking the pair runs in FastAPI's worker thread pool.
    """
    return reviewer.imported(input.file.read(), result.file.read())


@router.get("/review/files/{name}")
def download_review_file(name: FileName, reviewer: Reviewer) -> Response:
    if (content := reviewer.file(name)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NO_REVIEW)
    return Response(
        content,
        media_type=MEDIA_TYPES[name],
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )

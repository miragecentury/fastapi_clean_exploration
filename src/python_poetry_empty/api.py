"""Provide the API for the Python Poetry Empty project."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from structlog.stdlib import get_logger

from .services import DependsService
from .test_services import TestBusinessObject, TestService

router = APIRouter()

_logger = get_logger(__package__)

depends_test_service = DependsService(TestService)


@router.get("/")
def get_root() -> None:
    return


@router.post("/test")
async def create_test(
    test_service: Annotated[TestService, Depends(depends_test_service)],
    test_object: TestBusinessObject,
) -> TestBusinessObject:
    return await test_service.create(test_object)


@router.get("/test/{test_id}")
async def get_test(
    test_id: UUID, test_service: Annotated[TestService, Depends(depends_test_service)]
) -> TestBusinessObject:
    return await test_service.get(test_id)

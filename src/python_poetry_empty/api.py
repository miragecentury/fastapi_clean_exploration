"""Provide the API for the Python Poetry Empty project."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from python_poetry_empty.dependencies import (
    DependsService,
    EventPublisher,
    Repository,
    Service,
)

router = APIRouter()

service_depends = DependsService(Service)


@router.get("/")
def get_root(
    request: Request, service: Annotated[Service, Depends(service_depends)]
) -> str:
    val1 = service.use()
    return f"Hello, world! {val1}"

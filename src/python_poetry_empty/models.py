from typing import ClassVar
from uuid import UUID

from beanie import Document
from pydantic import ConfigDict, Field
from structlog.stdlib import get_logger

from python_poetry_empty.dependencies import MotorResource
from python_poetry_empty.test_objects import TestBusinessObject

_logger = get_logger(__package__)


class TestDocument(Document):
    """Test document model for Beanie."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    id: UUID = Field(default_factory=UUID, alias="_id")  # type: ignore
    name: str = Field(..., alias="name")


class TestRepository:

    def __init__(self, motor_resource: MotorResource) -> None:
        self.motor_resource: MotorResource = motor_resource

    async def create(self, test_object: TestBusinessObject) -> TestBusinessObject:
        try:
            test_document_to_be_created = TestDocument(**test_object.model_dump())
        except ValueError as exception:
            _logger.exception("Error creating test document", exception=exception)
            raise

        async with self.motor_resource.acquire_session() as session:
            test_document_created: TestDocument = await test_document_to_be_created.insert(session=session)

        try:
            test_object_created = TestBusinessObject(**test_document_created.model_dump())
        except ValueError as exception:
            _logger.exception("Error creating test business object", exception=exception)
            raise

        return test_object_created

    async def get(self, document_id: UUID) -> TestBusinessObject:
        async with self.motor_resource.acquire_session() as session:
            test_document: TestDocument | None = await TestDocument.get(document_id, session=session)

        if not test_document:
            raise ValueError(f"Test document with ID {document_id} not found")

        try:
            test_object = TestBusinessObject(**test_document.model_dump())
        except ValueError as exception:
            _logger.exception("Error creating test business object", exception=exception)
            raise

        return test_object

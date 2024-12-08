from uuid import UUID

from python_poetry_empty.models import TestRepository

from .test_objects import TestBusinessObject


class TestService:

    def __init__(self, test_repository: TestRepository) -> None:
        self.test_repository: TestRepository = test_repository

    async def create(self, test_business_object: TestBusinessObject) -> TestBusinessObject:
        return await self.test_repository.create(test_business_object)

    async def get(self, test_id: UUID) -> TestBusinessObject:
        return await self.test_repository.get(test_id)

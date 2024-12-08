from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from python_poetry_empty.models import TestRepository
from python_poetry_empty.test_objects import TestBusinessObject
from python_poetry_empty.test_services import TestService


class TestServiceExample:

    TEST_BUSINESS_OBJECT = TestBusinessObject(id=uuid4(), name="test_name")

    @pytest.mark.asyncio
    async def test_service(self):
        test_repository_mocked = MagicMock(TestRepository)
        test_repository_mocked.get = AsyncMock(return_value=self.TEST_BUSINESS_OBJECT)

        test_service = TestService(test_repository_mocked)
        test_business_object = await test_service.get(self.TEST_BUSINESS_OBJECT.id)

        assert test_business_object.id == self.TEST_BUSINESS_OBJECT.id
        assert test_business_object.name == self.TEST_BUSINESS_OBJECT.name

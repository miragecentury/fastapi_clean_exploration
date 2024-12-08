from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from python_poetry_empty.api import depends_test_service
from python_poetry_empty.application import Application
from python_poetry_empty.dependencies import AioPikaResource, MotorResource
from python_poetry_empty.test_objects import TestBusinessObject
from python_poetry_empty.test_services import TestService


class TestApi:

    TEST_BUSINESS_OBJECT = TestBusinessObject(id=uuid4(), name="test-name")

    def test_create_test(self):
        test_service_mocked = MagicMock(TestService)
        test_service_mocked.create = AsyncMock(return_value=self.TEST_BUSINESS_OBJECT)

        application = Application(
            motor_resource=MagicMock(MotorResource),
            aio_pika_resource=MagicMock(AioPikaResource),
        )
        test_client = TestClient(application)
        application.fastapi_app.dependency_overrides[depends_test_service] = lambda: test_service_mocked
        response = test_client.post("/test", content=self.TEST_BUSINESS_OBJECT.model_dump_json())
        assert response.status_code == 200
        assert response.json()["id"] == str(self.TEST_BUSINESS_OBJECT.id)
        assert response.json()["name"] == self.TEST_BUSINESS_OBJECT.name

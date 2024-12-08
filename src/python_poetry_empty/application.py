"""Provides the Application class."""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import (
    Any,
    AsyncContextManager,
    AsyncGenerator,
    AsyncIterator,
    Callable,
    Mapping,
)

import fastapi
import uvicorn
from starlette.types import Receive, Scope, Send
from structlog.stdlib import get_logger

from python_poetry_empty.models import TestDocument, TestRepository
from python_poetry_empty.test_services import TestService

from .api import router
from .dependencies import AioPikaResource, MotorResource
from .resources import ResourceManager
from .services import ServiceManager

_logger = get_logger(__package__)


class AbstractApplication(ABC):
    """Abstract application class."""

    def __init__(
        self,
        api_router: fastapi.APIRouter | None,
        resource_manager: ResourceManager | None = None,
        service_manager: ServiceManager | None = None,
    ) -> None:
        self.fastapi_app: fastapi.FastAPI | None = None
        self._api_router: fastapi.APIRouter | None = api_router
        self.resource_manager: ResourceManager = resource_manager or ResourceManager()
        self.service_manager: ServiceManager = service_manager or ServiceManager()
        self.fastapi_app = self.setup_fastapi_app()

    def setup_fastapi_app(self, **kargs) -> fastapi.FastAPI:
        self.setup_resources()
        self.setup_services()
        fastapi_app = fastapi.FastAPI(
            title="Python Poetry Empty",
            description="A sample project for Python Poetry.",
            version="0.1.0",
            dependencies=[],
            lifespan=self.lifespan_builder(),  # type: ignore
            **kargs,
        )
        if self._api_router:
            fastapi_app.include_router(self._api_router)
        return fastapi_app

    @abstractmethod
    def setup_resources(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def setup_services(self) -> None:
        raise NotImplementedError

    def run(self) -> None:
        server_config = uvicorn.Config(self, host="127.0.0.1", port=8000)
        server = uvicorn.Server(server_config)
        try:
            server.run()
        except KeyboardInterrupt:
            pass

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:

        if not self.fastapi_app:
            raise RuntimeError("FastAPI app is not set up.")

        if self.fastapi_app.root_path:
            scope["root_path"] = self.fastapi_app.root_path
        await self.fastapi_app.__call__(scope, receive, send)

    def lifespan_builder(
        self,
    ) -> Callable[[fastapi.FastAPI], AsyncIterator[Mapping[str, Any]]]:
        @asynccontextmanager
        async def lifespan(
            app: fastapi.FastAPI,
        ) -> AsyncIterator[Mapping[str, Any]]:
            for key, resource in self.resource_manager.get_all().items():
                setattr(app.state, str(key), resource)

            await self.resource_manager.start()
            yield {str(key): value for key, value in self.resource_manager.get_all().items()}
            await self.resource_manager.stop()

        return lifespan  # type: ignore


class Application(AbstractApplication):

    def __init__(
        self,
        resource_manager: ResourceManager | None = None,
        service_manager: ServiceManager | None = None,
        motor_resource: MotorResource | None = None,
        aio_pika_resource: AioPikaResource | None = None,
    ) -> None:
        self.motor_resource: MotorResource = motor_resource or MotorResource(document_models=[TestDocument])
        self.aio_pika_resource: AioPikaResource = aio_pika_resource or AioPikaResource()

        super().__init__(api_router=router, resource_manager=resource_manager, service_manager=service_manager)

    def setup_resources(self) -> None:
        self.resource_manager.add(self.service_manager)
        self.resource_manager.add(self.motor_resource)
        self.resource_manager.add(self.aio_pika_resource)

    def setup_services(self) -> None:
        self.service_manager.register_factory(TestRepository, lambda request: TestRepository(self.motor_resource))
        self.service_manager.register_factory(
            TestService, lambda request: TestService(self.service_manager.depends(TestRepository, request))
        )

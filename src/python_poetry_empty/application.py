"""Provides the Application class."""

import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, AsyncContextManager, Callable, Dict, Generator, Mapping, Type
from webbrowser import get

import fastapi
import uvicorn
from starlette.types import Receive, Scope, Send
from structlog.stdlib import get_logger

from .api import router
from .dependencies import EventPublisher, Repository, Resource, Service

_logger = get_logger(__package__)


class ResourceManager:

    def __init__(self) -> None:
        self.resources: Dict[str, Resource] = {}

    def add(self, resource: Resource) -> None:
        if self.resources.get(resource.name, None):
            raise ValueError(f"Resource with name {resource.name} already exists.")

        self.resources[resource.name] = resource

    def get_all(self) -> Dict[str, Resource]:
        return self.resources

    async def start(self) -> None:

        start_coroutines = []
        for _, resource in self.resources.items():
            start_coroutines.append(resource.start())
        await asyncio.gather(*start_coroutines)

    async def stop(self) -> None:
        stop_coroutines = []
        for _, resource in self.resources.items():
            stop_coroutines.append(resource.stop())
        await asyncio.gather(*stop_coroutines)


class ServiceManager(Resource):

    def __init__(self) -> None:
        super().__init__(name="service_manager")
        self.service_factories: Dict[Type, Callable[[Any], Any]] = {}

    def register_factory(
        self, service_type: Type, factory: Callable[[Any], Any]
    ) -> None:
        if self.service_factories.get(service_type, None):
            raise ValueError(f"Service factory for {service_type} already exists.")

        self.service_factories[service_type] = factory

    def get_service(self, service_type: Type, request: fastapi.Request) -> Any:
        factory = self.service_factories.get(service_type, None)
        if not factory:
            raise ValueError(f"Service factory for {service_type} does not exist.")

        # Instrospect the factory to determine the dependencies
        dependencies = {}
        for param in factory.__code__.co_varnames:
            if param == "request":
                dependencies[param] = request

        return factory(**dependencies)  # type: ignore


class AbstractApplication(ABC):

    def __init__(
        self,
        api_router: fastapi.APIRouter | None,
        resource_manager: ResourceManager = ResourceManager(),
        service_manager: ServiceManager = ServiceManager(),
    ) -> None:
        self._fastapi_app: fastapi.FastAPI | None = None
        self._api_router: fastapi.APIRouter | None = api_router
        self.resource_manager: ResourceManager = resource_manager
        self.service_manager: ServiceManager = service_manager

    def setup_fastapi_app(self, **kargs) -> fastapi.FastAPI:
        self.setup_resources()
        self.setup_services()
        fastapi_app = fastapi.FastAPI(
            title="Python Poetry Empty",
            description="A sample project for Python Poetry.",
            version="0.1.0",
            dependencies=[],
            lifespan=self.lifespan_builder(),
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
        self._fastapi_app = self.setup_fastapi_app()
        server_config = uvicorn.Config(self, host="127.0.0.1", port=8000)
        server = uvicorn.Server(server_config)
        try:
            server.run()
        except KeyboardInterrupt:
            pass

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:

        if not self._fastapi_app:
            raise RuntimeError("FastAPI app is not set up.")

        if self._fastapi_app.root_path:
            scope["root_path"] = self._fastapi_app.root_path
        await self._fastapi_app.__call__(scope, receive, send)

    def lifespan_builder(
        self,
    ) -> Callable[[fastapi.FastAPI], AsyncContextManager[Mapping[str, Any]]]:
        @asynccontextmanager
        async def lifespan(
            app: fastapi.FastAPI,
        ) -> AsyncContextManager[Mapping[str, Any]]:
            for key, resource in self.resource_manager.get_all().items():
                setattr(app.state, key, resource)

            await self.resource_manager.start()
            yield self.resource_manager.get_all()
            await self.resource_manager.stop()

        return lifespan


class Application(AbstractApplication):

    def __init__(self) -> None:
        super().__init__(api_router=router)

    def setup_resources(self) -> None:
        self.resource_manager.add(self.service_manager)
        self.resource_manager.add(Resource(name="resource1"))
        self.resource_manager.add(Resource(name="resource2"))

    def setup_services(self) -> None:
        self.service_manager.register_factory(
            Repository,
            lambda request: Repository(
                resource=request.app.state.resource1,
            ),
        )
        self.service_manager.register_factory(
            Service,
            lambda request: Service(
                repository=self.service_manager.get_service(Repository, request),
            ),
        )

"""Service manager module."""

from typing import Any, Callable, Dict, Self, Type

import fastapi

from .resources import AbstractResource


class ServiceManager(AbstractResource):
    """Service manager."""

    def __init__(self) -> None:
        super().__init__()
        self.service_factories: Dict[Type, Callable[[Any], Any]] = {}

    def register_factory(self, service_type: Type, factory: Callable[[Any], Any]) -> Self:
        if self.service_factories.get(service_type, None):
            raise ValueError(f"Service factory for {service_type} already exists.")

        self.service_factories[service_type] = factory
        return self

    def depends(self, service_type: Type, request: fastapi.Request) -> Any:
        factory: Callable[..., Any] | None = self.service_factories.get(service_type, None)
        if not factory:
            raise ValueError(f"Service factory for {service_type} does not exist.")

        # Instrospect the factory to determine the dependencies
        dependencies = {}
        for param in factory.__code__.co_varnames:
            if param == "request":
                dependencies[param] = request

        return factory(**dependencies)

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass


class DependsService:

    def __init__(self, service_type: Type) -> None:
        self.service_type: Type = service_type

    def __call__(self, request: fastapi.Request) -> Any:
        service_manager_class_str = str(ServiceManager)
        service_manager: ServiceManager = getattr(request.app.state, service_manager_class_str)  # type: ignore
        return service_manager.depends(self.service_type, request)

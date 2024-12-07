"""Sample module for dependency injection."""

from typing import Any, Type

import fastapi


class Resource:

    def __init__(self, name: str):
        self.name: str = name
        self._state: int = 0

    async def start(self):
        self._state = 1

    async def stop(self):
        self._state = 0


class DependsService:

    def __init__(self, service_type: Type) -> None:
        self.service_type: Type = service_type

    def __call__(self, request: fastapi.Request) -> Any:
        return request.app.state.service_manager.get_service(self.service_type, request)


class Repository:

    def __init__(self, resource: Resource):
        self._resource: Resource = resource

    def use(self):
        return self._resource._state


class EventHandler:

    def __init__(self, resource: Resource):
        self._resource: Resource = resource

    def use(self):
        return self._resource._state


class EventPublisher:

    def __init__(self, resource: Resource):
        self._resource: Resource = resource

    def use(self):
        return self._resource._state


class Service:

    def __init__(
        self,
        repository: Repository,
    ):
        self._repository: Repository = repository

    def use(self):
        return self._repository.use()

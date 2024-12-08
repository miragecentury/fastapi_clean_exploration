""" Provide

"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Coroutine, Dict, Self, Type

from structlog.stdlib import get_logger

_logger = get_logger(__package__)


class AbstractResource(ABC):

    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError


class ResourceManager:
    """A manager for resources.

    Resources are objects that need to be started, stopped and keep in state.
    """

    def __init__(self) -> None:
        self.resources: Dict[Type, AbstractResource] = {}

    def add(self, resource: AbstractResource) -> Self:
        """Add a resource to the manager.

        Args:
            resource (AbstractResource): The resource to add.
        Returns:
            ResourceManager: The manager instance.
        Raises:
            ValueError: If the resource already exists in the manager.
        """
        if self.resources.get(type(resource), None):
            raise ValueError(f"Resource with type {type(resource)} already exists.")

        self.resources[type(resource)] = resource
        return self

    def get_all(self) -> Dict[Type, AbstractResource]:
        """Get all resources in the manager."""
        return self.resources

    async def start(self) -> None:
        """Start all resources in the manager."""
        resources_start_coros: list[Coroutine[Any, Any, None]] = [
            resource.start() for resource in self.resources.values()
        ]
        await asyncio.gather(*resources_start_coros)
        _logger.debug(f"ResourceManager started all resources {len(self.resources)}")

    async def stop(self) -> None:
        """Stop all resources in the manager."""
        resources_stop_coros: list[Coroutine[Any, Any, None]] = [
            resource.stop() for resource in self.resources.values()
        ]
        await asyncio.gather(*resources_stop_coros)
        _logger.debug("ResourceManager stopped all resources")

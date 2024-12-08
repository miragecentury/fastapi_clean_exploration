""" This module contains the resources that will be injected into the classes that need them. """

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, List, Type

from aio_pika import connect_robust
from aio_pika.abc import AbstractChannel, AbstractRobustConnection
from aio_pika.pool import Pool
from beanie import Document, init_beanie
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorClientSession,
    AsyncIOMotorDatabase,
)

from python_poetry_empty.resources import AbstractResource


class MotorResource(AbstractResource):
    """Resource for managing the connection to MongoDB."""

    def __init__(self, document_models: List[Type[Document]] | None = None) -> None:
        self.document_models = document_models
        self.client: AsyncIOMotorClient[Any] | None = None
        self.database: AsyncIOMotorDatabase[Any] | None = None

    async def start(self) -> None:
        self.client = AsyncIOMotorClient("mongodb://localhost:27017")
        self.database = self.client.get_database("test")
        self.database.get_collection("test")
        await init_beanie(database=self.database, document_models=self.document_models)

    async def stop(self) -> None:
        if self.client:
            self.client.close()

    @asynccontextmanager
    async def acquire_session(self) -> AsyncGenerator[AsyncIOMotorClientSession, None]:
        if not self.client:
            raise RuntimeError("Client is not set up.")

        yield await self.client.start_session()


class AioPikaResource(AbstractResource):
    """Resource for managing the connection to RabbitMQ."""

    def __init__(self) -> None:
        self.connection_pool: Pool[AbstractRobustConnection] | None = None
        self.channel_pool: Pool[AbstractChannel] | None = None

    async def acquire_connection(self) -> AbstractRobustConnection:
        return await connect_robust("amqp://guest:guest@localhost/")

    async def acquire_channel(self) -> AbstractChannel:
        if not self.connection_pool:
            raise RuntimeError("Connection pool is not set up.")

        async with self.connection_pool.acquire() as connection:
            return await connection.channel()

    async def start(self) -> None:
        self.connection_pool = Pool(self.acquire_connection)
        self.channel_pool = Pool(self.acquire_channel)

    async def stop(self) -> None:
        if self.connection_pool:
            await self.connection_pool.close()

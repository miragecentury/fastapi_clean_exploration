from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TestBusinessObject(BaseModel):
    """Test business object model for Beanie."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    id: UUID
    name: str

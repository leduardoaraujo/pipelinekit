from abc import ABC, abstractmethod
from typing import Any


class BaseSink(ABC):
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.validate_config()

    @abstractmethod
    def validate_config(self) -> None:
        pass

    @abstractmethod
    async def write(self, data: dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

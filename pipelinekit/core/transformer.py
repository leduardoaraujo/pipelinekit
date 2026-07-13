from abc import ABC, abstractmethod
from typing import Any


class BaseTransformer(ABC):
    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    @abstractmethod
    def transform(self, data: Any) -> dict[str, Any]:
        pass

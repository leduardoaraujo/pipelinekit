from forgeflow.core.connector import BaseConnector
from forgeflow.core.sink import BaseSink
from forgeflow.core.transformer import BaseTransformer

Source = BaseConnector
Transform = BaseTransformer
Destination = BaseSink

__all__ = [
    "BaseConnector",
    "BaseTransformer",
    "BaseSink",
    "Source",
    "Transform",
    "Destination",
]

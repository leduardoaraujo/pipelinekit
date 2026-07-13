from pipelinekit.core.connector import BaseConnector
from pipelinekit.core.sink import BaseSink
from pipelinekit.core.transformer import BaseTransformer

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

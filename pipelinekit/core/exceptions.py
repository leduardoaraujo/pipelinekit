class ForgeFlowException(Exception):
    pass


class ConnectorException(ForgeFlowException):
    pass


class TransformerException(ForgeFlowException):
    pass


class SinkException(ForgeFlowException):
    pass


class ConfigurationException(ForgeFlowException):
    pass


class PipelineException(ForgeFlowException):
    pass

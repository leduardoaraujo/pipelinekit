from importlib import import_module

import structlog

from forgeflow.core import Destination, Source, Transform
from forgeflow.core.exceptions import PipelineException
from forgeflow.destinations import FileSink
from forgeflow.sources import HttpConnector, RestConnector
from forgeflow.transforms import JsonNormalizer

logger = structlog.get_logger()


class PipelineExecutor:
    CONNECTORS = {
        "http": HttpConnector,
        "rest": RestConnector,
    }

    TRANSFORMERS = {
        "json_normalizer": JsonNormalizer,
    }

    SINKS = {
        "postgres": "PostgresSink",
        "duckdb": "DuckDBSink",
        "file": FileSink,
    }

    async def execute(self, pipeline: dict) -> None:
        name = pipeline["name"]
        log = logger.bind(pipeline=name)

        if not pipeline.get("enabled", True):
            log.info("pipeline_skipped", reason="disabled")
            return

        log.info("pipeline_started")

        connector = None
        sinks = []

        try:
            connector = self._create_connector(pipeline["connector"])
            transformer = self._create_transformer(pipeline["transformer"])
            sinks = [self._create_sink(sink_cfg) for sink_cfg in pipeline["sinks"]]

            raw_data = await connector.fetch()
            log.info("data_fetched")

            normalized_data = transformer.transform(raw_data)
            log.info("data_transformed")

            for sink in sinks:
                await sink.write(normalized_data)
                log.info("data_written", sink_type=type(sink).__name__)

            log.info("pipeline_completed")

        except Exception as e:
            log.error("pipeline_failed", error=str(e))
            raise PipelineException(f"Pipeline {name} failed: {e}") from e

        finally:
            if connector:
                await connector.close()
            for sink in sinks:
                await sink.close()

    def _create_connector(self, config: dict) -> Source:
        connector_type = config.get("type")
        if not connector_type or connector_type not in self.CONNECTORS:
            raise PipelineException(f"Unknown connector type: {connector_type}")

        connector_class = self.CONNECTORS[connector_type]
        return connector_class(config.get("config", {}))

    def _create_transformer(self, config: dict) -> Transform:
        transformer_type = config.get("type")
        if not transformer_type or transformer_type not in self.TRANSFORMERS:
            raise PipelineException(f"Unknown transformer type: {transformer_type}")

        transformer_class = self.TRANSFORMERS[transformer_type]
        return transformer_class(config.get("config"))

    def _create_sink(self, config: dict) -> Destination:
        sink_type = config.get("type")
        if not sink_type or sink_type not in self.SINKS:
            raise PipelineException(f"Unknown sink type: {sink_type}")

        sink_class_ref = self.SINKS[sink_type]
        sink_class = sink_class_ref
        if isinstance(sink_class_ref, str):
            sink_class = getattr(import_module("forgeflow.destinations"), sink_class_ref)
        return sink_class(config.get("config", {}))

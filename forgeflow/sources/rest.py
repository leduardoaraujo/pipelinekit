import httpx

from forgeflow.core.connector import BaseConnector
from forgeflow.core.exceptions import ConnectorException


class RestConnector(BaseConnector):
    def __init__(self, config: dict):
        super().__init__(config)
        self.client: httpx.AsyncClient | None = None

    def validate_config(self) -> None:
        required = ["base_url", "endpoint"]
        missing = [key for key in required if key not in self.config]
        if missing:
            raise ConnectorException(f"Missing required config: {missing}")

    async def fetch(self) -> dict:
        if not self.client:
            timeout = self.config.get("timeout", 30.0)
            self.client = httpx.AsyncClient(
                base_url=self.config["base_url"], timeout=timeout
            )

        try:
            response = await self.client.get(
                self.config["endpoint"],
                headers=self.config.get("headers", {}),
                params=self.config.get("params", {}),
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise ConnectorException(f"REST request failed: {e}") from e

    async def close(self) -> None:
        if self.client:
            await self.client.aclose()

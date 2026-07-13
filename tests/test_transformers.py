import pytest

from forgeflow.core.exceptions import TransformerException
from forgeflow.transforms import JsonNormalizer


def test_json_normalizer_basic():
    transformer = JsonNormalizer()
    data = {"name": "test", "value": 123}

    result = transformer.transform(data)

    assert result["name"] == "test"
    assert result["value"] == 123
    assert "_ingested_at" in result


def test_json_normalizer_flatten():
    transformer = JsonNormalizer(config={"flatten": True})
    data = {"user": {"name": "test", "age": 30}, "active": True}

    result = transformer.transform(data)

    assert result["user_name"] == "test"
    assert result["user_age"] == 30
    assert result["active"] is True


def test_json_normalizer_invalid_input():
    transformer = JsonNormalizer()

    with pytest.raises(TransformerException):
        transformer.transform("not a dict")


def test_json_normalizer_timestamp_field():
    transformer = JsonNormalizer(config={"timestamp_field": "created_at"})
    data = {"name": "test"}

    result = transformer.transform(data)

    assert "created_at" in result
    assert "_ingested_at" in result

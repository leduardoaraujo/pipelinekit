from datetime import datetime
from typing import Any, Callable

from forgeflow.core.exceptions import TransformerException
from forgeflow.core.transformer import BaseTransformer


class SchemaMapper(BaseTransformer):
    """Transformer for mapping fields between different schemas."""

    TYPE_CONVERTERS: dict[str, Callable] = {
        "string": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
    }

    def transform(self, data: Any) -> dict[str, Any]:
        """
        Transform data by mapping fields to a new schema.

        Config structure:
        {
            "mappings": [
                {
                    "source": "old_field",
                    "target": "new_field",
                    "type": "string",
                    "default": "N/A",
                    "required": false
                },
                {
                    "source": "user.name",  # nested field
                    "target": "user_name",
                    "type": "string"
                },
                {
                    "target": "computed_field",
                    "expression": "{first_name} {last_name}"
                }
            ],
            "exclude_fields": ["internal_id", "password"],
            "include_unmapped": false,  # Include fields not in mappings
            "strict": false  # Fail on missing required fields
        }
        """
        if not isinstance(data, dict):
            raise TransformerException(f"Expected dict, got {type(data).__name__}")

        mappings = self.config.get("mappings", [])
        exclude_fields = self.config.get("exclude_fields", [])
        include_unmapped = self.config.get("include_unmapped", False)
        strict = self.config.get("strict", False)

        result = {}

        # Process mappings
        for mapping in mappings:
            target = mapping.get("target")
            if not target:
                raise TransformerException("Mapping must have 'target' field")

            # Check if it's a computed field
            if "expression" in mapping:
                value = self._compute_expression(data, mapping["expression"])
            else:
                source = mapping.get("source")
                if not source:
                    raise TransformerException(
                        f"Mapping for '{target}' must have 'source' or 'expression'"
                    )

                # Get source value (supports nested fields)
                value = self._get_nested_value(data, source)

                # Handle missing values
                if value is None:
                    if mapping.get("required", False):
                        if strict:
                            raise TransformerException(
                                f"Required field '{source}' is missing"
                            )
                        value = mapping.get("default")
                    else:
                        value = mapping.get("default")

            # Apply type conversion
            if value is not None and "type" in mapping:
                value = self._convert_type(value, mapping["type"])

            # Set value in result
            if value is not None:
                self._set_nested_value(result, target, value)

        # Include unmapped fields if configured
        if include_unmapped:
            mapped_sources = {m.get("source") for m in mappings if "source" in m}
            for key, value in data.items():
                if key not in mapped_sources and key not in exclude_fields:
                    result[key] = value

        return result

    def _get_nested_value(self, data: dict, field: str) -> Any:
        """Get value from nested dict using dot notation (e.g., 'user.address.city')."""
        keys = field.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    def _set_nested_value(self, data: dict, field: str, value: Any) -> None:
        """Set value in nested dict using dot notation."""
        keys = field.split(".")

        # Navigate to the parent dict
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the final value
        current[keys[-1]] = value

    def _compute_expression(self, data: dict, expression: str) -> str:
        """
        Compute a value from an expression template.

        Supports simple field substitution: "{field_name}" or "{nested.field}"
        """
        result = expression

        # Find all field references in the expression
        import re
        pattern = r"\{([^}]+)\}"
        matches = re.findall(pattern, expression)

        for match in matches:
            value = self._get_nested_value(data, match)
            if value is None:
                value = ""
            result = result.replace(f"{{{match}}}", str(value))

        return result

    def _convert_type(self, value: Any, target_type: str) -> Any:
        """Convert value to target type."""
        if target_type not in self.TYPE_CONVERTERS:
            raise TransformerException(
                f"Unsupported type: {target_type}. "
                f"Supported: {', '.join(self.TYPE_CONVERTERS.keys())}"
            )

        try:
            converter = self.TYPE_CONVERTERS[target_type]

            # Special handling for bool
            if target_type == "bool":
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on")
                return bool(value)

            return converter(value)

        except (ValueError, TypeError) as e:
            raise TransformerException(
                f"Failed to convert {value} to {target_type}: {e}"
            ) from e

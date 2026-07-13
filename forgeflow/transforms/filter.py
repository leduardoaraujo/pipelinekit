from typing import Any

from forgeflow.core.exceptions import TransformerException
from forgeflow.core.transformer import BaseTransformer


class FilterTransformer(BaseTransformer):
    """Transformer for filtering data based on conditions."""

    SUPPORTED_OPERATORS = {
        "eq": lambda a, b: a == b,
        "ne": lambda a, b: a != b,
        "gt": lambda a, b: a > b,
        "gte": lambda a, b: a >= b,
        "lt": lambda a, b: a < b,
        "lte": lambda a, b: a <= b,
        "contains": lambda a, b: b in a if isinstance(a, (str, list)) else False,
        "not_contains": lambda a, b: b not in a if isinstance(a, (str, list)) else True,
        "in": lambda a, b: a in b if isinstance(b, (list, tuple)) else False,
        "not_in": lambda a, b: a not in b if isinstance(b, (list, tuple)) else True,
        "is_null": lambda a, b: a is None,
        "is_not_null": lambda a, b: a is not None,
        "startswith": lambda a, b: a.startswith(b) if isinstance(a, str) else False,
        "endswith": lambda a, b: a.endswith(b) if isinstance(a, str) else False,
    }

    def transform(self, data: Any) -> dict[str, Any] | None:
        """
        Filter data based on conditions.

        Returns the data if it passes all conditions, None otherwise.

        Config structure:
        {
            "conditions": [
                {"field": "status", "operator": "eq", "value": "active"},
                {"field": "age", "operator": "gt", "value": 18}
            ],
            "logic": "AND"  # or "OR"
        }
        """
        if not isinstance(data, dict):
            raise TransformerException(f"Expected dict, got {type(data).__name__}")

        conditions = self.config.get("conditions", [])
        logic = self.config.get("logic", "AND").upper()

        if not conditions:
            return data

        results = []
        for condition in conditions:
            result = self._evaluate_condition(data, condition)
            results.append(result)

        # Apply logic
        if logic == "AND":
            passes = all(results)
        elif logic == "OR":
            passes = any(results)
        else:
            raise TransformerException(f"Unsupported logic: {logic}. Use 'AND' or 'OR'")

        return data if passes else None

    def _evaluate_condition(self, data: dict, condition: dict) -> bool:
        """Evaluate a single condition."""
        field = condition.get("field")
        operator = condition.get("operator")
        expected_value = condition.get("value")

        if not field or not operator:
            raise TransformerException("Condition must have 'field' and 'operator'")

        if operator not in self.SUPPORTED_OPERATORS:
            raise TransformerException(
                f"Unsupported operator: {operator}. "
                f"Supported: {', '.join(self.SUPPORTED_OPERATORS.keys())}"
            )

        # Get field value, support nested fields with dot notation
        actual_value = self._get_nested_value(data, field)

        # Apply operator
        operator_func = self.SUPPORTED_OPERATORS[operator]

        # For operators that don't need a comparison value
        if operator in ["is_null", "is_not_null"]:
            return operator_func(actual_value, None)

        return operator_func(actual_value, expected_value)

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

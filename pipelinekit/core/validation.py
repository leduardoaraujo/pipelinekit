"""Schema validation for ETL data."""

from typing import Any, Optional

import structlog
from pydantic import BaseModel, ValidationError, create_model

logger = structlog.get_logger()


class SchemaValidator:
    """Validate data against Pydantic schemas.

    Args:
        schema: Pydantic model class or dict defining the schema
        strict: Whether to use strict validation

    Example:
        from pydantic import BaseModel

        class UserSchema(BaseModel):
            id: int
            name: str
            email: str

        validator = SchemaValidator(UserSchema)
        result = validator.validate(data)
    """

    def __init__(self, schema: type[BaseModel] | dict, strict: bool = False):
        if isinstance(schema, dict):
            # Create Pydantic model from dict
            self.schema = create_model("DynamicSchema", **schema)
        else:
            self.schema = schema

        self.strict = strict

    def validate(self, data: Any) -> tuple[bool, Optional[dict], Optional[list[str]]]:
        """Validate data against schema.

        Args:
            data: Data to validate

        Returns:
            Tuple of (is_valid, validated_data, errors)
        """
        try:
            if isinstance(data, list):
                # Validate list of items
                validated = [self.schema(**item).model_dump() for item in data]
                logger.debug("schema_validation_success", count=len(validated))
                return True, validated, None
            else:
                # Validate single item
                validated = self.schema(**data).model_dump()
                logger.debug("schema_validation_success")
                return True, validated, None

        except ValidationError as e:
            errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
            logger.warning("schema_validation_failed", errors=errors)
            return False, None, errors

        except Exception as e:
            logger.error("schema_validation_error", error=str(e))
            return False, None, [str(e)]

    def validate_or_raise(self, data: Any) -> dict | list[dict]:
        """Validate data and raise exception on failure.

        Args:
            data: Data to validate

        Returns:
            Validated data

        Raises:
            ValidationError: If validation fails
        """
        is_valid, validated, errors = self.validate(data)

        if not is_valid:
            raise ValidationError(f"Schema validation failed: {errors}")

        return validated


class DataQualityValidator:
    """Validate data quality rules.

    Args:
        rules: List of validation rules

    Example:
        rules = [
            {"field": "age", "min": 0, "max": 150},
            {"field": "email", "pattern": r"^[\\w.-]+@[\\w.-]+\\.\\w+$"},
        ]
        validator = DataQualityValidator(rules)
        is_valid, errors = validator.validate(data)
    """

    def __init__(self, rules: list[dict]):
        self.rules = rules

    def validate(self, data: dict | list[dict]) -> tuple[bool, list[str]]:
        """Validate data against quality rules.

        Args:
            data: Data to validate (dict or list of dicts)

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []

        items = data if isinstance(data, list) else [data]

        for idx, item in enumerate(items):
            for rule in self.rules:
                field = rule.get("field")
                if not field:
                    continue

                value = item.get(field)

                # Check min/max
                if "min" in rule and value is not None:
                    if value < rule["min"]:
                        errors.append(f"Row {idx}: {field} ({value}) < min ({rule['min']})")

                if "max" in rule and value is not None:
                    if value > rule["max"]:
                        errors.append(f"Row {idx}: {field} ({value}) > max ({rule['max']})")

                # Check required
                if rule.get("required") and value is None:
                    errors.append(f"Row {idx}: {field} is required but missing")

                # Check pattern (regex)
                if "pattern" in rule and value is not None:
                    import re

                    if not re.match(rule["pattern"], str(value)):
                        errors.append(
                            f"Row {idx}: {field} does not match pattern {rule['pattern']}"
                        )

                # Check enum values
                if "enum" in rule and value is not None:
                    if value not in rule["enum"]:
                        errors.append(
                            f"Row {idx}: {field} ({value}) not in allowed values {rule['enum']}"
                        )

        is_valid = len(errors) == 0

        if is_valid:
            logger.debug("data_quality_validation_success", items=len(items))
        else:
            logger.warning("data_quality_validation_failed", errors=errors)

        return is_valid, errors

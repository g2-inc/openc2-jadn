"""
Basic functions
"""
from typing import List

from .codec.codec import Codec
from . import (
    jadn
)


def validate_schema(schema: dict):
    """
    Validate a JADN Schema
    :param schema: JADN schema to validate
    :return: list of errors
    """
    schema = jadn.jadn_loads(schema)
    jadn_analysis = jadn.jadn_analyze(schema)
    rtn = []

    if len(jadn_analysis['undefined']):
        rtn.append(ReferenceError(f"schema contains undefined types: {', '.join(jadn_analysis['undefined'])}"))

    return rtn


def validate_instance(schema: dict, instance: dict, _type: str = None) -> List[Exception]:
    schema_validate = validate_schema(schema)
    rtn = []

    if len(schema_validate) > 0:
        rtn.extend(schema_validate)
    else:
        pass

    return rtn

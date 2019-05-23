"""
Base JADN Schema Converter
"""
import json
import os
import re

from typing import Callable, Union

from ... import (
    enums,
    jadn_defs,
    jadn_utils,
    utils
)


class JADNConverterBase(object):
    """
    Base JADN Converter
    """
    _indent = ' ' * 4

    _escape_chars = ('-', ' ')

    _meta_order = jadn_defs.META_ORDER

    _space_start = re.compile(r"^\s+", re.MULTILINE)

    _structure_formats = dict(
        Record='_formatRecord',
        Choice='_formatChoice',
        Map='_formatMap',
        Enumerated='_formatEnumerated',
        Array='_formatArray',
        ArrayOf='_formatArrayOf'
    )

    _table_field_headers = utils.FrozenDict({
        '#': 'opts',
        'Description': 'desc',
        'ID': 'id',
        'Name': ('name', 'value'),
        'Type': 'type',
        'Value': 'value'
    })

    def __init__(self, jadn, comm=enums.CommentLevels.ALL):
        """
        Schema Converter Init
        :param jadn: str or dict of the JADN schema
        :param comm: Comment level
        """
        if isinstance(jadn, str):
            if os.path.isfile(jadn):
                with open(jadn, 'rb') as f:
                    jadn = json.load(f)
            else:
                jadn = json.loads(jadn)
        elif isinstance(jadn, dict):
            pass
        else:
            raise TypeError('JADN improperly formatted')

        jadn = utils.toFrozen(jadn_utils.jadn_idx2key(jadn))
        self.comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL

        self._meta = jadn.get('meta', {})
        self._types = []
        self._custom = []
        self._customFields = {}

        for type_def in jadn.get('types', []):
            self._customFields[type_def.name] = type_def.type
            if type_def.type in self._structure_formats.keys():
                self._types.append(type_def)
            else:
                self._custom.append(type_def)

    def _makeStructures(self, default=None):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        :rtype list
        """
        structs = []
        for t in self._types:
            df = getattr(self, f"_format{t.type}", None)
            structs.append(df(t) if df else default)

        return structs

    # Helper Functions
    def formatStr(self, s: str) -> str:
        """
        Formats the string for use in schema
        :param s: string to format
        :return: formatted string
        """
        escape_chars = list(filter(None, self._escape_chars))
        if s == '*':
            return 'unknown'
        elif len(escape_chars) > 0:
            return re.compile(rf"[{''.join(escape_chars)}]").sub('_', s)
        else:
            return s

    def _structFun(self, _type: str, default: str = None) -> Union[Callable, None]:
        """
        Get the conversion function for the given structure
        :param _type: type of structure
        :return: structure conversion function
        """
        fun = self._structure_formats.get(_type)
        if fun:
            return getattr(self, fun, default)

        return None

    def _is_optional(self, opts: dict) -> bool:
        """
        Check if the field is optional
        :param opts: field options
        :return: bool - optional
        """
        return opts.get('min', 1) == 0

    def _is_array(self, opts: dict) -> bool:
        """
        Check if the field is an array
        :param opts: field options
        :return: bool - optional
        """
        return opts.get('max', 1) != 1

"""
Base JADN Schema Converter
"""
import json
import os
import re

from typing import Callable, Union

from ...enums import CommentLevels
from ...jadn_defs import COLUMN_KEYS, META_ORDER
from ...utils import FrozenDict


class JADNConverterBase(object):
    """
    Base JADN Converter
    """
    _indent = ' ' * 4

    _escape_chars = ['-', ' ']

    _meta_order = META_ORDER

    _space_start = re.compile(r"^\s+", re.MULTILINE)

    _structure_formats = dict(
        Record='_formatRecord',
        Choice='_formatChoice',
        Map='_formatMap',
        Enumerated='_formatEnumerated',
        Array='_formatArray',
        ArrayOf='_formatArrayOf'
    )

    _table_field_headers = {
        '#': 'opts',
        'Description': 'desc',
        'ID': 'id',
        'Name': ('name', 'value'),
        'Type': 'type',
        'Value': 'value'
    }

    def __init__(self, jadn, comm=CommentLevels.ALL):
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

        self.comm = comm if comm in CommentLevels.values() else CommentLevels.ALL

        self._meta = jadn.get('meta', {})
        self._types = []
        self._custom = []
        self._customFields = {}

        for t in jadn['types']:
            t = dict(zip(COLUMN_KEYS.Structure, t))
            if 'fields' in t:
                t['fields'] = [FrozenDict(zip(COLUMN_KEYS['Enum_Def' if t['type'] == 'Enumerated' else 'Gen_Def'], f)) for f in t['fields']]
            t = FrozenDict(t)

            self._customFields[t.name] = t.type
            if t.type in self._structure_formats.keys():
                self._types.append(t)
            else:
                self._custom.append(t)

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
            escape_regex = re.compile(rf"[{''.join(escape_chars)}]")
            return escape_regex.sub('_', s)
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

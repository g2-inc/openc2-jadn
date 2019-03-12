"""
Base JADN Schema Converter
"""
import json
import re

from ...enums import CommentLevels
from ...utils import FrozenDict


class JADNConverterBase(object):
    """
    Base JADN Converter
    """
    _indent = ' ' * 4

    _escape_chars = ['-', ' ']

    _meta_order = ['title', 'module', 'description', 'imports', 'exports', 'patch']

    _keys = {
        # Structures
        'structure': ['name', 'type', 'opts', 'desc', 'fields'],
        # Definitions
        'def': ['id', 'name', 'type', 'opts', 'desc'],
        'enum_def': ['id', 'value', 'desc'],
    }

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
        if type(jadn) is str:
            try:
                jadn = json.loads(jadn)
            except Exception as e:
                raise e
        elif type(jadn) is dict:
            pass

        else:
            raise TypeError('JADN improperly formatted')

        self.comm = comm if comm in CommentLevels.values() else CommentLevels.ALL

        self._meta = jadn.get('meta', {})
        self._types = []
        self._custom = []
        self._customFields = {}

        for t in jadn['types']:
            t = dict(zip(self._keys['structure'], t))
            if 'fields' in t:
                t['fields'] = [FrozenDict(zip(self._keys['enum_def' if t['type'] == 'Enumerated' else 'def'], f)) for f in t['fields']]
            t = FrozenDict(t)

            self._customFields[t.name] = t.type
            if t.type in self._structure_formats.keys():
                self._types.append(t)
            else:
                self._custom.append(t)

    def _structFun(self, _type, default=None):
        """
        Get the conversion function for the given structure
        :param _type: type of structure
        :return: structure conversion function
        """
        fun = self._structure_formats.get(_type)
        if fun:
            return getattr(self, fun, default)

        return None

    # Helper Functions
    def formatStr(self, s):
        """
        Formats the string for use in schema
        :param s: string to format
        :type s: str
        :return: formatted string
        :rtype str
        """
        escape_chars = list(filter(None, self._escape_chars))
        if s == '*':
            return 'unknown'
        elif len(escape_chars) > 0:
            escape_regex = re.compile(rf"[{''.join(escape_chars)}]")
            return escape_regex.sub('_', s)
        else:
            return s

    def _is_optional(self, opts):
        """
        Check if the field is optional
        :param opts: field options
        :return: bool - optional
        """
        return opts.get('min', 1) == 0

    def _is_array(self, opts):
        """
        Check if the field is an array
        :param opts: field options
        :return: bool - optional
        """
        return opts.get('max', 1) != 1

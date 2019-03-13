import datetime
import json
import re

from ..base_dump import JADNConverterBase
from .... import (
    enums,
    jadn_utils,
    utils
)


class JADNtoThrift(JADNConverterBase):
    _fieldMap = {
        'Binary': 'binary',
        'Boolean': 'bool',
        'Integer': 'i64',
        'Number': 'double',
        'Null': 'null',
        'String': 'string'
    }

    _imports = []

    def thrift_dump(self, comm=enums.CommentLevels.ALL):
        """
        Converts the JADN schema to Thrift
        :param comm: Level of comments to include in converted schema
        :return: Thrift schema
        """
        if comm:
            self.comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL

        imports = ''.join([f'import \"{imp}\";\n' for imp in self._imports])
        jadn_fields = ',\n'.join([self._indent+json.dumps(utils.default_decode(list(field.values()))) for field in self._custom])

        return f'{self.makeHeader()}{imports}{self.makeStructures()}\n/* JADN Custom Fields\n[\n{jadn_fields}\n]\n*/'

    def makeHeader(self):
        """
        Create the header for the schema
        :return: header for schema
        """
        header_regex = re.compile(r'(^\"|\"$)')
        header = [
            '/*',
            *[f" * meta: {k} - {header_regex.sub('', json.dumps(utils.default_decode(v)))}" for k, v in self._meta.items()],
            '*/'
        ]

        return '\n'.join(header) + '\n\n'

    def makeStructures(self):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        :rtype str
        """
        tmp = ''
        for t in self._types:
            df = self._structFun(t.type, None)

            if df is not None:
                tmp += df(t)

        return tmp

    # Structure Formats
    def _formatRecord(self, itm):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        """
        properties = []
        for prop in itm.fields:
            opts = {'type': prop.type}
            if len(prop.opts) > 0: opts['options'] = jadn_utils.topts_s2d(prop.opts)

            optional = 'optional' if self._is_optional(opts.get('options', {})) else 'required'
            comment = self._formatComment(prop.desc, jadn_opts=opts)
            properties.append(f'{self._indent}{prop.id}: {optional} {self._fieldType(prop.type)} {self.formatStr(prop.name)}; {comment}\n')

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        comment = self._formatComment('' if itm.desc == '' else itm.desc, jadn_opts=opts)
        properties = ''.join(properties)
        return f'\nstruct {self.formatStr(itm.name)} {{ {comment}\n{properties}}}\n'

    def _formatChoice(self, itm):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        """
        # Thrift does not use choice, using struct
        properties = []
        for prop in itm.fields:
            opts = {'type': prop.type}
            if len(prop.opts) > 0: opts['options'] = jadn_utils.fopts_s2d(prop.opts)

            comment = self._formatComment(prop.desc, jadn_opts=opts)
            properties.append(f'{self._indent}{prop.id}: optional {self._fieldType(prop.type)} {self.formatStr(prop.name)}; {comment}\n')

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        comment = self._formatComment('' if itm.desc == '' else itm.desc, jadn_opts=opts)
        properties = ''.join(properties)
        return f'\nstruct {self.formatStr(itm.name)} {{ {comment}\n{properties}}}\n'

    def _formatMap(self, itm):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        """
        # Thrift does not use maps in same way, using struct
        return self._formatChoice(itm)

    def _formatEnumerated(self, itm):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        """
        properties = []
        for prop in itm.fields:
            prop_name = self.formatStr(prop.value or f'Unknown_{self.formatStr(itm.name)}_{prop.id}')
            properties.append(f'{self._indent}{prop_name} = {prop.id}; {self._formatComment(prop.desc)}\n')

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        comment = self._formatComment(itm.desc, jadn_opts=opts)
        properties = ''.join(properties)
        return f'\nenum {self.formatStr(itm.name)} {{ {comment}\n{properties}}}\n'

    def _formatArray(self, itm):
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        :rtype str
        """
        # Best method for creating some type of array
        return self._formatArrayOf(itm)

    def _formatArrayOf(self, itm):
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :return: formatted arrayof
        """
        # Best method for creating some type of array
        field_opts = jadn_utils.topts_s2d(itm.opts)
        opts = {
            'type': itm.type,
            'options': field_opts
        }

        nested_type = self.formatStr(field_opts.get('rtype', 'string'))
        comment = self._formatComment(itm.desc, jadn_opts=opts)
        nested_def = f'{self._indent}1: optional list<{nested_type}> item; {comment}\n'
        return f'\nstruct {self.formatStr(itm.name)} {{\n{nested_def}}}\n'

    # Helper Functions
    def _fieldType(self, f):
        """
        Determines the field type for the schema
        :param f: current type
        :return: type mapped to the schema
        """
        if f in self._customFields and f not in [c.name for c in self._custom]:
            rtn = self.formatStr(f)

        elif f in self._fieldMap.keys():
            rtn = self.formatStr(self._fieldMap.get(f, f))

        else:
            rtn = 'string'
        return rtn

    def _formatComment(self, msg, **kargs):
        """
        Format a comment for the given schema
        :param msg: comment text
        :param kargs: key/value comments
        :return: formatted comment
        """
        if self.comm == enums.CommentLevels.NONE:
            return ''

        com = '//'
        if msg not in ['', None, ' ']:
            com += f' {msg}'

        for k, v in kargs.items():
            com += f' #{k}:{json.dumps(v)}'
        return '' if re.match(r'^\/\/\s+$', com) else com


def thrift_dumps(jadn, comm=enums.CommentLevels.ALL):
    """
    Produce Thrift schema from JADN schema
    :param jadn: JADN Schema to convert
    :param comm: Level of comments to include in converted schema
    :return: Thrift schema
    """
    comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL
    return JADNtoThrift(jadn).thrift_dump(comm)


def thrift_dump(jadn, fname, source="", comm=enums.CommentLevels.ALL):
    """
    Produce Thrift scheema from JADN schema and write to file provided
    :param jadn: JADN Schema to convert
    :param fname: Name of file to write
    :param source: Name of the original JADN schema file
    :param comm: Level of comments to include in converted schema
    :return: None
    """
    comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL
    with open(fname, "w") as f:
        if source:
            f.write(f"// Generated from {source}, {datetime.ctime(datetime.now())}\n")
        f.write(thrift_dumps(jadn, comm))

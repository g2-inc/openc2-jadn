import json
import re

from datetime import datetime

from ..base_dump import JADNConverterBase
from .... import (
    enums,
    jadn_utils,
    utils
)


class JADNtoCDDL(JADNConverterBase):
    _escape_chars = []

    _fieldMap = {
        'Binary': 'bstr',
        'Boolean': 'bool',
        'Integer': 'int64',
        'Number': 'float64',
        'Null': 'null',
        'String': 'bstr'
    }

    def cddl_dump(self, comm=enums.CommentLevels.ALL):
        """
        Converts the JADN schema to CDDL
        :param comm: Level of comments to include in converted schema
        :return: CDDL schema
        """
        if comm:
            self.comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL

        doubleEmpty = re.compile('^$\n?^$', re.MULTILINE)
        return re.sub(doubleEmpty, '', f'{self.makeHeader()}{self.makeStructures()}\n{self.makeCustom()}\n')

    def makeHeader(self):
        """
        Create the header for the schema
        :return: header for schema
        """
        header_regex = re.compile(r'(^\"|\"$)')
        header = [f"; meta: {k} - {header_regex.sub('', json.dumps(utils.default_decode(v)))}" for k, v in self._meta.items()]

        return '\n'.join(header) + '\n'

    def makeStructures(self):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        """
        tmp = ''
        for t in self._types:
            df = self._structFun(t.type, None)

            if df is not None:
                tmp += df(t)
        return tmp

    def makeCustom(self):
        defs = [f'{self.formatStr(field.name)} = {self._fieldType(field.type)} ; {field.desc}' for field in self._custom]
        return '\n'.join(defs)

    # Structure Formats
    def _formatRecord(self, itm):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        """
        i = len(itm.fields)
        properties = []
        for prop in itm.fields:
            opts = {'type': prop.type, 'field': prop.id}
            if len(prop.opts) > 0: opts['options'] = jadn_utils.fopts_s2d(prop.opts)

            optional = '? ' if self._is_optional(opts.get('options', {})) else ''
            comment = (', ' if i > 1 else ' ') + self._formatComment(prop.desc, jadn_opts=opts)
            properties.append(f'{self._indent}{optional}{self.formatStr(prop.name)}: {self._fieldType(prop.type)}{comment}\n')
            i -= 1

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        comment = self._formatComment(itm.desc, jadn_opts=opts)
        properties = ''.join(properties)
        return f'\n{self.formatStr(itm.name)} = {{ {comment}\n{properties}}}\n'

    def _formatChoice(self, itm):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        """
        i = len(itm.fields)
        properties = []
        for prop in itm.fields:
            opts = {'type': prop.type, 'field': prop.id}
            if len(prop.opts) > 0: opts['options'] = jadn_utils.fopts_s2d(prop.opts)

            comment = ('// ' if i > 1 else '') + self._formatComment(prop.desc, jadn_opts=opts)
            properties.append(f"{self.formatStr(prop.name)}: {self._fieldType(prop.type)} {comment}")
            i -= 1

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        comment = self._formatComment(itm.desc, jadn_opts=opts)
        properties = f'\n{self._indent}'.join(properties)
        return f'\n{self.formatStr(itm.name)} = ( {comment}\n{self._indent}{properties}\n)\n'

    def _formatMap(self, itm):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        """
        i = len(itm.fields)
        properties = []
        for prop in itm.fields:
            opts = {'type': prop.type, 'field': prop.id}
            if len(prop.opts) > 0: opts['options'] = jadn_utils.fopts_s2d(prop.opts)

            optional = '? ' if self._is_optional(opts.get('options', {})) else ''
            comment = (', ' if i > 1 else ' ') + self._formatComment(prop.desc, jadn_opts=opts)
            properties.append(f'{self._indent}{optional}{self.formatStr(prop.name)}: {self._fieldType(prop.type)}{comment}\n')
            i -= 1

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        comment = self._formatComment(itm.desc, jadn_opts=opts)
        properties = ''.join(properties)
        return f'\n{self.formatStr(itm.name)} = [ {comment}\n{properties}]\n'

    def _formatEnumerated(self, itm):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        :rtype str
        """
        enum_name = self.formatStr(itm.name)
        properties = []
        for prop in itm.fields:
            opts = {'field': prop.id}
            value = self.formatStr(prop.value or f'Unknown_{enum_name}_{prop.id}')
            properties.append(f'\"{value}\" {self._formatComment(prop.desc, jadn_opts=opts)}\n')

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        comment = self._formatComment(itm.desc, jadn_opts=opts)
        properties = f'{enum_name} /= '.join(properties)
        return f'\n{comment}\n{enum_name} = {properties}'

    def _formatArray(self, itm):  # TODO: what should this do??
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        """
        type_opts = {'type': itm.type}
        if len(itm.opts) > 0: type_opts['options'] = jadn_utils.fopts_s2d(itm.opts)

        i = len(itm.fields)
        properties = []
        for prop in itm.fields:
            opts = {'type': prop.type, 'field': prop.id}
            if len(prop.opts) > 0: opts['options'] = jadn_utils.fopts_s2d(prop.opts)

            optional = '? ' if self._is_optional(opts.get('options', {})) else ''
            comment = (', ' if i > 1 else ' ') + self._formatComment(prop.desc, jadn_opts=opts)
            properties.append(f'{self._indent}{optional}{self.formatStr(prop.name)}: {self._fieldType(prop.type)}{comment}\n')
            i -= 1

        comment = self._formatComment(itm.desc, jadn_opts=type_opts)
        properties = ''.join(properties)
        return f'\n{self.formatStr(itm.name)} = [ {comment}\n{properties}]\n'

    def _formatArrayOf(self, itm):  # TODO: what should this do??
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :return: formatted arrayof
        """
        field_opts = jadn_utils.topts_s2d(itm.opts)

        field_type = f"[{field_opts.get('min', '')}*{field_opts.get('max', '')} {self.formatStr(field_opts.get('rtype', 'string'))}]"

        type_opts = {'type': itm.type}

        return f'\n{self.formatStr(itm.name)} = {field_type} {self._formatComment(itm.desc, jadn_opts=type_opts)}\n'

    # Helper Functions
    def _fieldType(self, f):
        """
        Determines the field type for the schema
        :param f: current type
        :return: type mapped to the schema
        """
        if f in self._customFields:
            rtn = self.formatStr(f)

        elif f in self._fieldMap.keys():
            rtn = self.formatStr(self._fieldMap.get(f, f))

        else:
            rtn = 'bstr'
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

        com = ';'
        if msg not in ['', None, ' ']:
            com += f' {msg}'

        for k, v in kargs.items():
            com += f' #{k}:{json.dumps(v)}'
        return '' if re.match(r'^;\s+$', com) else com


def cddl_dumps(jadn, comm=enums.CommentLevels.ALL):
    """
    Produce CDDL schema from JADN schema
    :param jadn: JADN Schema to convert
    :param comm: Level of comments to include in converted schema
    :return: CDDL schema
    """
    comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL
    return JADNtoCDDL(jadn).cddl_dump(comm)


def cddl_dump(jadn, fname, source="", comm=enums.CommentLevels.ALL):
    """
    Produce CDDL schema from JADN schema and write to file provided
    :param jadn: JADN Schema to convert
    :param fname: Name of file to write
    :param source: Name of the original JADN schema file
    :param comm: Level of comments to include in converted schema
    :return: None
    """
    comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL

    with open(fname, "w") as f:
        if source:
            f.write(f"; Generated from {source}, {datetime.ctime(datetime.now())}\n")
        f.write(cddl_dumps(jadn, comm))

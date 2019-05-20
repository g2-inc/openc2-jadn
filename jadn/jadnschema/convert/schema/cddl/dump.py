import json
import re

from beautifultable import BeautifulTable
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
        'String': 'tstr'
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
        header = [f"; meta: {k} - {header_regex.sub('', json.dumps(utils.default_encoding(v)))}" for k, v in self._meta.items()]

        return '\n'.join(header) + '\n'

    def makeStructures(self):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        """
        return ''.join(self._makeStructures(default=''))

    def makeCustom(self):
        defs = BeautifulTable(default_alignment=BeautifulTable.ALIGN_LEFT, max_width=500)
        defs.set_style(BeautifulTable.STYLE_NONE)
        for field in self._custom:
            defs.append_row([
                f"{self.formatStr(field.name)} =",
                self._fieldType(field.type),
                f"; {field.desc}"
            ])

        return self._space_start.sub('', str(defs))

    # Structure Formats
    def _formatRecord(self, itm):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        """
        i = len(itm.fields)
        properties = BeautifulTable(default_alignment=BeautifulTable.ALIGN_LEFT, max_width=500)
        properties.set_style(BeautifulTable.STYLE_NONE)

        for prop in itm.fields:
            opts = {'type': prop.type, 'field': prop.id}
            if len(prop.opts) > 0: opts['options'] = jadn_utils.fopts_s2d(prop.opts)
            properties.append_row([
                f"{'? ' if self._is_optional(opts.get('options', {})) else ''}{self.formatStr(prop.name)}:",
                f"{self._fieldType(prop.type)}{',' if i > 1 else ''}",
                self._formatComment(prop.desc, jadn_opts=opts)
            ])
            i -= 1

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        comment = self._formatComment(itm.desc, jadn_opts=opts)
        properties = self._space_start.sub(self._indent, str(properties))
        return f'\n{self.formatStr(itm.name)} = {{ {comment}\n{properties}\n}}\n'

    def _formatChoice(self, itm):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        """
        i = len(itm.fields)
        properties = BeautifulTable(default_alignment=BeautifulTable.ALIGN_LEFT, max_width=500)
        properties.set_style(BeautifulTable.STYLE_NONE)

        for prop in itm.fields:
            opts = {'type': prop.type, 'field': prop.id}
            if len(prop.opts) > 0: opts['options'] = jadn_utils.fopts_s2d(prop.opts)

            properties.append_row([
                f"{self.formatStr(prop.name)}:",
                f"{self._fieldType(prop.type)}{' // ' if i > 1 else ''}",
                self._formatComment(prop.desc, jadn_opts=opts)
            ])

            i -= 1

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        comment = self._formatComment(itm.desc, jadn_opts=opts)
        properties = self._space_start.sub(self._indent, str(properties))
        return f'\n{self.formatStr(itm.name)} = ( {comment}\n{properties}\n)\n'

    def _formatMap(self, itm):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        """
        i = len(itm.fields)
        properties = BeautifulTable(default_alignment=BeautifulTable.ALIGN_LEFT, max_width=500)
        properties.set_style(BeautifulTable.STYLE_NONE)

        for prop in itm.fields:
            opts = {'type': prop.type, 'field': prop.id}
            if len(prop.opts) > 0: opts['options'] = jadn_utils.fopts_s2d(prop.opts)

            properties.append_row([
                f"{'? ' if self._is_optional(opts.get('options', {})) else ''}{self.formatStr(prop.name)}:",
                f"{self._fieldType(prop.type)}{', ' if i > 1 else ''}",
                self._formatComment(prop.desc, jadn_opts=opts)
            ])
            i -= 1

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        comment = self._formatComment(itm.desc, jadn_opts=opts)
        properties = self._space_start.sub(self._indent, str(properties))
        return f'\n{self.formatStr(itm.name)} = [ {comment}\n{properties}]\n'

    def _formatEnumerated(self, itm):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        :rtype str
        """
        enum_name = self.formatStr(itm.name)
        properties = BeautifulTable(default_alignment=BeautifulTable.ALIGN_LEFT, max_width=500)
        properties.set_style(BeautifulTable.STYLE_NONE)

        i = len(itm.fields)
        for prop in itm.fields:
            opts = {'field': prop.id}
            value = self.formatStr(prop.value or f'Unknown_{enum_name}_{prop.id}')

            properties.append_row([
                f"{enum_name} {'' if i == len(itm.fields) else '/'}=",
                f"\"{value}\"",
                self._formatComment(prop.desc, jadn_opts=opts)
            ])
            i -= 1

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        comment = self._formatComment(itm.desc, jadn_opts=opts)
        properties = self._space_start.sub('', str(properties))
        return f'\n{comment}\n{properties}\n'

    def _formatArray(self, itm):  # TODO: what should this do??
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        """
        type_opts = {'type': itm.type}
        if len(itm.opts) > 0: type_opts['options'] = jadn_utils.fopts_s2d(itm.opts)
        properties = BeautifulTable(default_alignment=BeautifulTable.ALIGN_LEFT, max_width=500)
        properties.set_style(BeautifulTable.STYLE_NONE)

        i = len(itm.fields)
        for prop in itm.fields:
            opts = {'type': prop.type, 'field': prop.id}
            if len(prop.opts) > 0: opts['options'] = jadn_utils.fopts_s2d(prop.opts)

            properties.append_row([
                f"{'? ' if self._is_optional(opts.get('options', {})) else ''}{self.formatStr(prop.name)}:",
                f"{self._fieldType(prop.type)}{', ' if i > 1 else ''}",
                self._formatComment(prop.desc, jadn_opts=opts)
            ])
            i -= 1

        comment = self._formatComment(itm.desc, jadn_opts=type_opts)
        properties = self._space_start.sub(self._indent, str(properties))
        return f'\n{self.formatStr(itm.name)} = [ {comment}\n{properties}\n]\n'

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

        elif f in self._fieldMap:
            rtn = self.formatStr(self._fieldMap.get(f, f))

        else:
            rtn = 'tstr'
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

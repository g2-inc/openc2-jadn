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


class JADNtoProto3(JADNConverterBase):
    _fieldMap = {
        'Binary': 'string',
        'Boolean': 'bool',
        'Integer': 'int64',
        'Number': 'string',
        'Null': 'string',
        'String': 'string'
    }

    _imports = []

    def proto_dump(self, com=enums.CommentLevels.ALL):
        """
        Converts the JADN schema to ProtoBuf3
        :param com: Level of comments to include in converted schema
        :return: Protobuf3 schema
        """
        if com:
            self.comm = com if com in enums.CommentLevels.values() else enums.CommentLevels.ALL

        imports = ''.join([f'import \"{imp}\";\n' for imp in self._imports])
        jadn_fields = ',\n'.join([self._indent+json.dumps(utils.default_encoding(list(field.values()))) for field in self._custom])

        return f"{self.makeHeader()}{imports}{self.makeStructures()}\n/* JADN Custom Fields\n[\n{jadn_fields}\n]\n*/"

    def makeHeader(self):
        """
        Create the header for the schema
        :return: header for schema
        """
        header_regex = re.compile(r'(^\"|\"$)')
        pkg_regex = re.compile(r'[.\-/]+')
        header = [
            'syntax = "proto3";',
            '',
            f"package {pkg_regex.sub('_', self._meta.get('module', 'JADN_ProtoBuf_Schema'))};",
            '',
            '/*',
            *[f" * meta: {k} - {header_regex.sub('', json.dumps(utils.default_encoding(v)))}" for k, v in self._meta.items()],
            '*/'
        ]

        return '\n'.join(header) + '\n\n'

    def makeStructures(self):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        """
        return ''.join(self._makeStructures(default=''))

    # Structure Formats
    def _formatRecord(self, itm):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        """
        properties = BeautifulTable(default_alignment=BeautifulTable.ALIGN_LEFT, max_width=500)
        properties.set_style(BeautifulTable.STYLE_NONE)
        for prop in itm.fields:
            opts = {'type': prop.type}
            if len(prop.opts) > 0: opts['options'] = jadn_utils.fopts_s2d(prop.opts)

            properties.append_row([
                self._fieldType(prop.type),
                f"{self.formatStr(prop.name)} =",
                f"{prop.id};",
                self._formatComment(prop.desc, jadn_opts=opts)
            ])

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        comment = self._formatComment(itm.desc, jadn_opts=opts)
        properties = self._space_start.sub(self._indent, str(properties))
        return f'\nmessage {self.formatStr(itm.name)} {{ {comment}\n{properties}\n}}\n'

    def _formatChoice(self, itm):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        """
        properties = BeautifulTable(default_alignment=BeautifulTable.ALIGN_LEFT, max_width=500)
        properties.set_style(BeautifulTable.STYLE_NONE)
        for prop in itm.fields:
            opts = {'type': prop.type}
            if len(prop.opts) > 0: opts['options'] = jadn_utils.fopts_s2d(prop.opts)

            properties.append_row([
                self._fieldType(prop.type),
                f"{self.formatStr(prop.name)} =",
                f"{prop.id};",
                self._formatComment(prop.desc, jadn_opts=opts)
            ])

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        comment = self._formatComment(itm.desc, jadn_opts=opts)
        properties = self._space_start.sub(self._indent, str(properties))
        return self._wrapAsRecord(f'\noneof {self.formatStr(itm.name)} {{ {comment}\n{properties}\n}}\n')

    def _formatMap(self, itm):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        """
        return self._formatRecord(itm)

    def _formatEnumerated(self, itm):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        """
        properties = BeautifulTable(default_alignment=BeautifulTable.ALIGN_LEFT, max_width=500)
        properties.set_style(BeautifulTable.STYLE_NONE)
        default = True
        for prop in itm.fields:
            if prop.id == 0: default = False
            properties.append_row([
                f"{self.formatStr(prop.value or f'Unknown_{self.formatStr(itm.name)}_{prop.id}')} =",
                f"{prop.id};",
                self._formatComment(prop.desc)
            ])

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        if default:
            properties.insert_row(0, [
                f"Unknown_{itm.name.replace('-', '_')} =",
                "0;",
                "// required starting enum number for protobuf3\n"
            ])

        comment = self._formatComment(itm.desc, jadn_opts=opts)
        properties = self._space_start.sub(self._indent, str(properties))
        return f'\nenum {self.formatStr(itm.name)} {{ {comment}\n{properties}\n}}\n'

    def _formatArray(self, itm):  # TODO: what should this do??
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        """
        print(f'Array: {itm}')
        return ''

    def _formatArrayOf(self, itm):  # TODO: what should this do??
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :return: formatted arrayof
        """
        opts = {
            'type': 'arrayOf',
            'options': jadn_utils.topts_s2d(itm.opts)
        }
        rtype = self.formatStr(opts['options'].setdefault('rtype', 'String'))
        comment = self._formatComment(itm.desc, jadn_opts=opts)
        return f'\nmessage {self.formatStr(itm.name)} {{\n{self._indent}repeated {rtype} {rtype.lower()} = 1; {comment}\n}}\n'

    # Helper Functions
    def _fieldType(self, f):
        """
        Determines the field type for the schema
        :param f: current type
        :return: type mapped to the schema
        """
        rtn = 'string'
        if re.search(r'(datetime|date|time)', f):
            if 'google/protobuf/timestamp.proto' not in self._imports:
                self._imports.append('google/protobuf/timestamp.proto')
            rtn = 'google.protobuf.Timestamp'

        if f in self._customFields and f not in [c.name for c in self._custom]:
            rtn = self.formatStr(f)

        elif f in self._fieldMap.keys():
            rtn = self.formatStr(self._fieldMap.get(f, f))
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

    def _wrapAsRecord(self, itm):
        """
        wraps the given item as a record for the schema
        :param itm: item to wrap
        :return: item wrapped as a record for the schema
        """
        lines = itm.split('\n')[1:-1]
        if len(lines) > 1:
            n = re.search(r'\s[\w\d\_]+\s', lines[0]).group()[1:-1]
            lines = '\n'.join(f'{self._indent}{l}' for l in lines)
            return f"\nmessage {self.formatStr(n)} {{\n{lines}\n}}\n"
        return ''


def proto_dumps(jadn, comm=enums.CommentLevels.ALL):
    """
    Produce Protobuf3 schema from JADN schema
    :param jadn: JADN Schema to convert
    :param comm: Level of comments to include in converted schema
    :return: Protobuf3 schema
    """
    comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL
    return JADNtoProto3(jadn).proto_dump(comm)


def proto_dump(jadn, fname, source="", comm=enums.CommentLevels.ALL):
    """
    Produce ProtoBuf schema from JADN schema and write to file provided
    :param jadn: JADN Schema to convert
    :param fname: Name of file to write
    :param source: Name of the original JADN schema file
    :param comm: Level of comments to include in converted schema
    :return: N/A
    """
    comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL
    with open(fname, "w") as f:
        if source:
            f.write(f"// Generated from {source}, { datetime.ctime(datetime.now())}\n")
        f.write(proto_dumps(jadn, comm))

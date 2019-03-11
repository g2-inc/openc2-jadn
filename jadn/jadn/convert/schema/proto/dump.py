import json
import re

from datetime import datetime

from jadn.jadn_utils import fopts_s2d, topts_s2d
from jadn.enums import CommentLevels
from jadn.utils import Utils
from ..base_dump import JADNConverterBase


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

    def proto_dump(self, com=CommentLevels.ALL):
        """
        Converts the JADN schema to ProtoBuf3
        :param com: Level of comments to include in converted schema
        :return: Protobuf3 schema
        """
        if com:
            self.com = com if com in CommentLevels.values() else CommentLevels.ALL

        imports = ''.join(['import \"{}\";\n'.format(i) for i in self._imports])
        jadn_fields = ',\n'.join([self._indent+json.dumps(Utils.defaultDecode(list(field.values()))) for field in self._custom])

        return f"{self.makeHeader()}{imports}{self.makeStructures()}\n/* JADN Custom Fields\n[\n{jadn_fields}\n]\n*/"

    def makeHeader(self):
        """
        Create the header for the schema
        :return: header for schema
        """
        header_regex = re.compile(r'(^\"|\"$)')
        header = list([
            'syntax = "proto3";',
            '',
            'package {};'.format(re.sub(r'[.\-/]+', '_', self._meta.get('module', 'JADN_ProtoBuf_Schema'))),
            '',
            '/*',
            *[f" * meta: {k} - {header_regex.sub('', json.dumps(Utils.defaultDecode(v)))}" for k, v in self._meta.items()],
            '*/'
        ])

        return '\n'.join(header) + '\n\n'

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
        if self.com == CommentLevels.NONE:
            return ''

        com = '//'
        if msg not in ['', None, ' ']:
            com += ' {msg}'.format(msg=msg)

        for k, v in kargs.items():
            com += ' #{k}:{v}'.format(
                k=k,
                v=json.dumps(v)
            )
        return '' if re.match(r'^\/\/\s+$', com) else com

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
            if len(prop.opts) > 0: opts['options'] = fopts_s2d(prop.opts)

            properties.append('{idn}{type} {name} = {num}; {com}\n'.format(
                idn=self._indent,
                type=self._fieldType(prop.type),
                name=self.formatStr(prop.name),
                num=prop.id,
                com=self._formatComment(prop.desc, jadn_opts=opts)
            ))

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = topts_s2d(itm.opts)

        return '\nmessage {name} {{ {com}\n{req}}}\n'.format(
            name=self.formatStr(itm.name),
            req=''.join(properties),
            com=self._formatComment(itm.desc, jadn_opts=opts)
        )

    def _formatChoice(self, itm):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        """
        properties = []
        for prop in itm.fields:
            opts = {'type': prop.type}
            if len(prop.opts) > 0: opts['options'] = fopts_s2d(prop.opts)

            properties.append('{idn}{type} {name} = {num}; {com}\n'.format(
                idn=self._indent,
                type=self._fieldType(prop.type),
                name=self.formatStr(prop.name),
                num=prop.id,
                com=self._formatComment(prop.desc, jadn_opts=opts)
            ))

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = topts_s2d(itm.opts)

        return self._wrapAsRecord('\noneof {name} {{ {com}\n{req}}}\n'.format(
            idn=self._indent,
            name=self.formatStr(itm.name),
            com=self._formatComment(itm.desc, jadn_opts=opts),
            req=''.join(properties)
        ))

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
        properties = []
        default = True
        for prop in itm.fields:
            if prop.id == 0: default = False
            properties.append('{idn}{name} = {num}; {com}\n'.format(
                idn=self._indent,
                name=self.formatStr(prop.value or 'Unknown_{}_{}'.format(self.formatStr(itm.name), prop.id)),
                num=prop.id,
                com=self._formatComment(prop.desc)
            ))

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = topts_s2d(itm.opts)

        return '\nenum {name} {{ {com}\n{default}{enum}}}\n'.format(
            idn=self._indent,
            name=self.formatStr(itm.name),
            com=self._formatComment(itm.desc, jadn_opts=opts),
            default='{}Unknown_{} = 0; // required starting enum number for protobuf3\n'.format(self._indent, itm.name.replace('-', '_')) if default else '',
            enum=''.join(properties)
        )

    def _formatArray(self, itm):  # TODO: what should this do??
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        """
        print('Array: {}'.format(itm))
        return ''

    def _formatArrayOf(self, itm):  # TODO: what should this do??
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :return: formatted arrayof
        """

        opts = {
            'type': 'arrayOf',
            'options': topts_s2d(itm.opts)
        }
        rtype = opts['options'].setdefault('rtype', 'String')
        
        return '\nmessage {name} {{\n{idn}repeated {type} {field} = 1; {com}\n}}\n'.format(
            idn=self._indent,
            name=self.formatStr(itm.name),
            type=self.formatStr(rtype),
            field=self.formatStr(rtype).lower(),
            com=self._formatComment(itm.desc, jadn_opts=opts)
        )


def proto_dumps(jadn, comm=CommentLevels.ALL):
    """
    Produce Protobuf3 schema from JADN schema
    :param jadn: JADN Schema to convert
    :type jadn: str or dict
    :param comm: Level of comments to include in converted schema
    :type comm: str of enums.CommentLevel
    :return: Protobuf3 schema
    :rtype str
    """
    comm = comm if comm in CommentLevels.values() else CommentLevels.ALL
    return JADNtoProto3(jadn).proto_dump(comm)


def proto_dump(jadn, fname, source="", comm=CommentLevels.ALL):
    """
    Produce ProtoBuf schema from JADN schema and write to file provided
    :param jadn: JADN Schema to convert
    :type jadn: str or dict
    :param fname: Name of file to write
    :type fname: str
    :param source: Name of the original JADN schema file
    :type source: str
    :param comm: Level of comments to include in converted schema
    :type comm: str of enums.CommentLevel
    :return: N/A
    """
    comm = comm if comm in CommentLevels.values() else CommentLevels.ALL
    with open(fname, "w") as f:
        if source:
            f.write(f"// Generated from {source}, { datetime.ctime(datetime.now())}\n")
        f.write(proto_dumps(jadn, comm))

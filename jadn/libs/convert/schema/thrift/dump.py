import datetime
import json
import re

from libs.codec.codec_utils import fopts_s2d, topts_s2d
from libs.enums import CommentLevels
from libs.utils import Utils


class JADNtoThrift(object):
    def __init__(self, jadn):
        """
        Schema Converter for JADN to thrift
        :param jadn: str or dict of the JADN schema
        :type jadn: str or dict
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

        self.comments = CommentLevels.ALL

        self.indent = '    '

        self._fieldMap = {
            'Binary': 'binary',
            'Boolean': 'bool',
            'Integer': 'i64',
            'Number': 'double',
            'Null': 'null',
            'String': 'string'
        }
        self._structFormats = {
            'Record': self._formatRecord,
            'Choice': self._formatChoice,
            'Map': self._formatMap,
            'Enumerated': self._formatEnumerated,
            'Array': self._formatArray,
            'ArrayOf': self._formatArrayOf,
        }

        self._imports = []
        self._meta = jadn['meta'] or []
        self._types = []
        self._custom = []
        self._customFields = []  # [t[0] for t in self._types]

        for t in jadn['types']:
            if t[1] in self._structFormats.keys():
                self._types.append(t)
                self._customFields.append(t[0])
            else:
                self._custom.append(t)

    def thrift_dump(self, comm=CommentLevels.ALL):
        """
        Converts the JADN schema to Thrift
        :param comm: Level of comments to include in converted schema
        :type comm: str of enums.CommentLevel
        :return: Thrift schema
        :rtype str
        """
        self.comments = comm if comm in CommentLevels.values() else CommentLevels.ALL

        return '{header}{imports}{defs}\n/* JADN Custom Fields\n[\n{jadn_fields}\n]\n*/'.format(
            idn=self.indent,
            header=self.makeHeader(),
            defs=self.makeStructures(),
            imports=''.join(['import \"{}\";\n'.format(i) for i in self._imports]),
            jadn_fields=',\n'.join([self.indent+json.dumps(f) for f in Utils.defaultDecode(self._custom)])
        )

    def formatStr(self, s):
        """
        Formats the string for use in schema
        :param s: string to format
        :type s: str
        :return: formatted string
        :rtype str
        """
        if s == '*':
            return 'unknown'
        else:
            return re.sub(r'[\- ]', '_', s)

    def makeHeader(self):
        """
        Create the header for the schema
        :return: header for schema
        :rtype str
        """
        header = list([
            '/*'
        ])

        header.extend([' * meta: {} - {}'.format(k, re.sub(r'(^\"|\"$)', '', json.dumps(Utils.defaultDecode(v)))) for k, v in self._meta.items()])

        header.append('*/')

        return '\n'.join(header) + '\n\n'

    def makeStructures(self):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        :rtype str
        """
        tmp = ''
        for t in self._types:
            df = self._structFormats.get(t[1], None)

            if df is not None:
                tmp += df(t)

        return tmp

    def _fieldType(self, f):
        """
        Determines the field type for the schema
        :param f: current type
        :return: type mapped to the schema
        :rtype str
        """
        if f in self._customFields:
            rtn = self.formatStr(f)

        elif f in self._fieldMap.keys():
            rtn = self.formatStr(self._fieldMap.get(f, f))

        else:
            rtn = 'string'
        return rtn

    def _formatComment(self, msg, **kargs):
        if self.comments == CommentLevels.NONE:
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
        :rtype str
        """

        lines = []
        for l in itm[-1]:
            opts = {'type': l[2]}
            if len(l[-2]) > 0:
                opts['options'] = fopts_s2d(l[-2])
                lines.append('{idn}{num}: {choice} {type} {name}; {com}\n'.format(
                    idn=self.indent,
                    choice='optional',
                    type=self._fieldType(l[2]),
                    name=self.formatStr(l[1]),
                    num=l[0],
                    com=self._formatComment(l[-1], jadn_opts=opts)
                ))
            else:
                lines.append('{idn}{num}: {choice} {type} {name}; {com}\n'.format(
                    idn=self.indent,
                    choice='required',
                    type=self._fieldType(l[2]),
                    name=self.formatStr(l[1]),
                    num=l[0],
                    com=self._formatComment(l[-1], jadn_opts=opts)
                ))

        opts = {'type': itm[1]}
        if len(itm[2]) > 0: opts['options'] = topts_s2d(itm[2])

        return '\nstruct {name} {{ {com}\n{req}}}\n'.format(
            name=self.formatStr(itm[0]),
            req=''.join(lines),
            com=self._formatComment('' if itm[-2] == '' else itm[-2], jadn_opts=opts)
        )

    def _formatChoice(self, itm):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        :rtype str
        """
        # Thrift does not use choice, using struct
        lines = []
        for l in itm[-1]:
            opts = {'type': l[2]}
            if len(l[-2]) > 0: opts['options'] = fopts_s2d(l[-2])

            lines.append('{idn}{num}: {choice} {type} {name}; {com}\n'.format(
                idn=self.indent,
                choice='optional',
                type=self._fieldType(l[2]),
                name=self.formatStr(l[1]),
                num=l[0],
                com=self._formatComment(l[-1], jadn_opts=opts)
            ))

        opts = {'type': itm[1]}
        if len(itm[2]) > 0: opts['options'] = topts_s2d(itm[2])

        return '\nstruct {name} {{ {com}\n{req}}}\n'.format(
            name=self.formatStr(itm[0]),
            req=''.join(lines),
            com=self._formatComment(itm[-2], jadn_opts=opts)
        )

    def _formatMap(self, itm):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        :rtype str
        """
        # Thrift does not use maps in same way, using struct

        return self._formatChoice(itm)

    def _formatEnumerated(self, itm):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        :rtype str
        """

        lines = []
        default = True
        for l in itm[-1]:
            a = l[-1].split('-', 1)[0]
            if l[0] == 0: default = False
            lines.append('{idn}{name} = {num}; {com}\n'.format(
                idn=self.indent,
                name=self.formatStr(l[1] or '{}'.format(a[0:-1])),
                num=l[0],
                com=self._formatComment(l[-1])
            ))

        opts = {'type': itm[1]}
        if len(itm[2]) > 0: opts['options'] = topts_s2d(itm[2])

        return '\nenum {name} {{ {com}\n{enum}}}\n'.format(
            idn=self.indent,
            name=self.formatStr(itm[0]),
            com=self._formatComment(itm[-2], jadn_opts=opts),
            enum=''.join(lines)
        )

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
        :rtype str
        """
        # Best method for creating some type of array

        field_opts = topts_s2d(itm[2])
        opts = {
            'type': itm[1],
            'options': topts_s2d(itm[2])
        }

        return '\nstruct {name} {{\n{req}}}\n'.format(
            name=self.formatStr(itm[0]),
            req='{idn}{num}: {choice} list<{type}> {name}; {com}\n'.format(
                idn=self.indent,
                num='1',
                choice='optional',
                type=self.formatStr(field_opts.get('rtype', 'string')),
                name='item',
                com=self._formatComment(itm[3], jadn_opts=opts)
            ),
        )


def thrift_dumps(jadn, comm=CommentLevels.ALL):
    """
    Produce Thrift schema from JADN schema
    :arg jadn: JADN Schema to convert
    :type jadn: str or dict
    :param comm: Level of comments to include in converted schema
    :type comm: str of enums.CommentLevel
    :return: Thrift schema
    :rtype str
    """
    comm = comm if comm in CommentLevels.values() else CommentLevels.ALL
    return JADNtoThrift(jadn).thrift_dump(comm)


def thrift_dump(jadn, fname, source="", comm=CommentLevels.ALL):
    """
    Produce Thrift scheema from JADN schema and write to file provided
    :param jadn: JADN Schema to convert
    :type jadn: str or dict
    :param fname: Name of file to write
    :tyoe fname: str
    :param source: Name of the original JADN schema file
    :type source: str
    :param comm: Level of comments to include in converted schema
    :type comm: str of enums.CommentLevel
    :return: N/A
    """
    comm = comm if comm in CommentLevels.values() else CommentLevels.ALL
    with open(fname, "w") as f:
        if source:
            f.write("// Generated from {}, {}\n".format(source, datetime.ctime(datetime.now())))
        f.write(thrift_dumps(jadn, comm))

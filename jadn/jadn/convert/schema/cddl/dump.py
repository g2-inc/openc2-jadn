import json
import re

from datetime import datetime

from jadn.codec.codec_utils import fopts_s2d, topts_s2d
from jadn.enums import CommentLevels
from jadn.utils import Utils


class JADNtoCDDL(object):
    def __init__(self, jadn):
        """
        Schema Converter for JADN to CDDL
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

        self.indent = '  '

        self._fieldMap = {
            'Binary': 'bstr',
            'Boolean': 'bool',
            'Integer': 'int64',
            'Number': 'float64',
            'Null': 'null',
            'String': 'bstr'
        }

        self._structFormats = {
            'Record': self._formatRecord,
            'Choice': self._formatChoice,
            'Map': self._formatMap,
            'Enumerated': self._formatEnumerated,
            'Array': self._formatArray,
            'ArrayOf': self._formatArrayOf,
        }

        self._meta = jadn['meta'] or []
        self._types = []
        self._custom = []
        self._customFields = []

        for t in jadn['types']:
            self._customFields.append(t[0])
            if t[1] in self._structFormats.keys():
                self._types.append(t)

            else:
                self._custom.append(t)

    def cddl_dump(self, comm=CommentLevels.ALL):
        """
        Converts the JADN schema to CDDL
        :param comm: Level of comments to include in converted schema
        :type comm: str of enums.CommentLevel
        :return: CDDL schema
        :rtype str
        """
        self.comments = comm if comm in CommentLevels.values() else CommentLevels.ALL

        doubleEmpty = re.compile('^$\n?^$', re.MULTILINE)
        return re.sub(doubleEmpty, '', '{header}{defs}\n{custom}\n'.format(
            header=self.makeHeader(),
            defs=self.makeStructures(),
            custom=self.makeCustom()
        ))

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
        header = ['; meta: {} - {}'.format(k, re.sub(r'(^\"|\"$)', '', json.dumps(Utils.defaultDecode(v)))) for k, v in self._meta.items()]

        return '\n'.join(header) + '\n'

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

    def makeCustom(self):
        defs = []
        for field in self._custom:
            line = '{name} = {type} ; {com}'.format(
                name=self.formatStr(field[0]),
                type=self._fieldType(field[1]),
                com=field[-1]
            )
            defs.append(line)

        return '\n'.join(defs)

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
            rtn = 'bstr'

        # print(f, rtn)
        return rtn

    def _formatComment(self, msg, **kargs):
        if self.comments == CommentLevels.NONE:
            return ''

        com = ';'
        if msg not in ['', None, ' ']:
            com += ' {msg}'.format(msg=msg)

        for k, v in kargs.items():
            com += ' #{k}:{v}'.format(
                k=k,
                v=json.dumps(v)
            )
        return '' if re.match(r'^;\s+$', com) else com

    # Structure Formats
    def _formatRecord(self, itm):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        :rtype str
        """
        lines = []
        i = 1
        for l in itm[-1]:
            opts = {'type': l[2], 'field': l[0]}
            if len(l[-2]) > 0: opts['options'] = fopts_s2d(l[-2])

            lines.append('{idn}{pre_opts}{name}: {fType}{c} {com}\n'.format(
                idn=self.indent,
                pre_opts='? ' if '[0' in l[-2] else '',
                name=self.formatStr(l[1]),
                fType=self._fieldType(l[2]),
                c=',' if i < len(itm[-1]) else '',
                com=self._formatComment(l[-1], jadn_opts=opts)
            ))
            i += 1
        opts = {'type': itm[1]}
        if len(itm[2]) > 0: opts['options'] = topts_s2d(itm[2])

        return '\n{name} = {{ {com}\n{req}}}\n'.format(
            name=self.formatStr(itm[0]),
            com=self._formatComment(itm[-2], jadn_opts=opts),
            req=''.join(lines)
        )

    def _formatChoice(self, itm):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        :rtype str
        """
        lines = []
        i = 1
        for l in itm[-1]:
            opts = {'type': l[2], 'field': l[0]}
            if len(l[-2]) > 0: opts['options'] = fopts_s2d(l[-2])

            lines.append('{name}: {type}{c} {com}'.format(
                name=self.formatStr(l[1]),
                type=self._fieldType(l[2]),
                c=' //' if i < len(itm[-1]) else '',
                com=self._formatComment(l[-1], jadn_opts=opts)
            ))
            i += 1

        opts = {'type': itm[1]}
        if len(itm[2]) > 0: opts['options'] = topts_s2d(itm[2])

        return '\n{name} = ( {com}\n{idn}{defs}\n)\n'.format(
            name=self.formatStr(itm[0]),
            com=self._formatComment(itm[-2], jadn_opts=opts),
            idn=self.indent,
            defs='\n{}'.format(self.indent).join(lines)
        )

    def _formatMap(self, itm):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        :rtype str
        """
        lines = []
        i = 1
        for l in itm[-1]:
            opts = {'type': l[2], 'field': l[0]}
            if len(l[-2]) > 0: opts['options'] = fopts_s2d(l[-2])

            lines.append('{idn}{pre_opts}{name}: {fType}{c} {com}\n'.format(
                idn=self.indent,
                pre_opts='? ' if '[0' in l[-2] else '',
                name=self.formatStr(l[1]),
                fType=self._fieldType(l[2]),
                c=',' if i < len(itm[-1]) else '',
                com=self._formatComment(l[-1], jadn_opts=opts)
            ))
            i += 1

        opts = {'type': itm[1]}
        if len(itm[2]) > 0: opts['options'] = topts_s2d(itm[2])

        return '\n{name} = [ {com}\n{defs}]\n'.format(
            name=self.formatStr(itm[0]),
            com=self._formatComment(itm[-2], jadn_opts=opts),
            defs=''.join(lines)
        )

    def _formatEnumerated(self, itm):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        :rtype str
        """
        lines = []
        for l in itm[-1]:
            opts = {'field': l[0]}

            lines.append('\"{name}\" {com}\n'.format(
                name=self.formatStr(l[1] or 'Unknown_{}_{}'.format(self.formatStr(itm[0]), l[0])),
                com=self._formatComment(l[-1], jadn_opts=opts)
            ))

        opts = {'type': itm[1]}
        if len(itm[2]) > 0: opts['options'] = topts_s2d(itm[2])

        return '\n{com}\n{init}{rem}'.format(
            com=self._formatComment(itm[-2], jadn_opts=opts),
            init='{} = '.format(self.formatStr(itm[0])),
            rem='{} /= '.format(self.formatStr(itm[0])).join(lines)
        )

    def _formatArray(self, itm):  # TODO: what should this do??
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        :rtype str
        """
        field_opts = topts_s2d(itm[2])

        field_type = '[{min}*{max} {type}]'.format(
            min=field_opts.get('min', ''),
            max=field_opts.get('max', ''),
            type=self.formatStr(field_opts.get('rtype', 'string'))
        )

        return '\n{name} = {type} {com}\n'.format(
            name=self.formatStr(itm[0]),
            type=field_type,
            com=self._formatComment(itm[-1])
        )

    def _formatArrayOf(self, itm):  # TODO: what should this do??
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :return: formatted arrayof
        :rtype str
        """
        field_opts = topts_s2d(itm[2])

        field_type = '[{min}*{max} {type}]'.format(
            min=field_opts.get('min', ''),
            max=field_opts.get('max', ''),
            type=self.formatStr(field_opts.get('rtype', 'string'))
        )

        return '\n{name} = {type} {com}\n'.format(
            name=self.formatStr(itm[0]),
            type=field_type,
            com=self._formatComment(itm[-1])
        )


def cddl_dumps(jadn, comm=CommentLevels.ALL):
    """
    Produce CDDL schema from JADN schema
    :param jadn: JADN Schema to convert
    :type jadn: str or dict
    :param comm: Level of comments to include in converted schema
    :type comm: str of enums.CommentLevel
    :return: CDDL schema
    :rtype str
    """
    comm = comm if comm in CommentLevels.values() else CommentLevels.ALL
    return JADNtoCDDL(jadn).cddl_dump(comm)


def cddl_dump(jadn, fname, source="", comm=CommentLevels.ALL):
    """
    Produce CDDL schema from JADN schema and write to file provided
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
            f.write("; Generated from {}, {}\n".format(source, datetime.ctime(datetime.now())))
        f.write(cddl_dumps(jadn, comm))

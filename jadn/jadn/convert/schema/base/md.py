import json

from datetime import datetime

from jadn.codec.codec_utils import fopts_s2d, topts_s2d


class JADNtoMD(object):
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

        self._structFormats = {
            'Record': self._formatRecord,
            'Choice': self._formatChoice,
            'Map': self._formatMap,
            'Enumerated': self._formatEnumerated,
            'Array': self._formatArray,
            'ArrayOf': self._formatArrayOf,
        }

        self._meta = jadn['meta'] or {}
        self._types = []
        self._custom = []
        self._customFields = []

        for t in jadn['types']:
            self._customFields.append(t[0])
            if t[1] in self._structFormats.keys():
                self._types.append(t)

            else:
                self._custom.append(t)

    def md_dump(self):
        md = self.makeHeader()

        md += self.makeStructures()

        md += self.makeCustom()

        return md

    def formatStr(self, s):
        """
        Formats the string for use in schema
        :param s: string to format
        :type s: str
        :return: formatted string
        :rtype str
        """
        return 'unknown' if s == '*' else s

    def makeHeader(self):
        """
        Create the header for the schema
        :return: header for schema
        :rtype object - BeautifulSoup
        """
        header = '## Schema\n'

        meta_order = ['title', 'module', 'description', 'exports', 'imports', 'patch']

        header += self._makeTableHeader([
            ('.  ', 'r'),
            ('.  ', 'l')
        ])

        for meta in meta_order:
            header += meta + ': | '
            val = self._meta.get(meta, '')

            if type(val) is list:
                header += ', '.join(['**{}**: {}'.format(*imp) for imp in val] if type(val[0]) is list else val)
            else:
                header += val

            header += '\n'

        return header + '\n'

    def makeStructures(self):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        :rtype object - BeautifulSoup
        """
        structure = '##3.2 Structure Types\n'

        i = 1
        for t in self._types:
            df = self._structFormats.get(t[1], None)

            if df is not None:
                structure += df(t, i)
                i += 1

        return structure

    def makeCustom(self):
        """
        Create the custom definitions for the schema
        :return: custom definitions for the schema
        :rtype object - BeautifulSoup
        """
        custom = '##3.3 Primitive Types\n\n'

        custom += self._makeTableHeader([
            ('Name', ),
            ('Type', ),
            ('Description', )
        ])

        body = []
        for row in self._custom:
            opts = topts_s2d(row[2])
            fmt = ''
            if 'format' in opts:
                fmt = ' ({})'.format(opts['format'])

            body.append([row[0], '{}{}'.format(row[1], fmt), row[3]])

        custom += self._makeTableBody(body)
        return custom + '\n'

    def _makeTableHeader(self, headers):
        header = []
        align = []

        for column in headers:
            header.append(column[0])
            if len(column) > 1:
                if column[1].startswith('r'):
                    align.append('---:')
                elif column[1].startswith('c'):
                    align.append(':---:')
                else:
                    align.append(':---')
            else:
                align.append(':---')

        return '{}\n{}\n'.format(' | '.join(header), ' | '.join(align))

    def _makeTableBody(self, rows, exclude=()):
        md_rows = []

        for row in rows:
            tmp_row = []
            i = 0
            for column in row:

                if i not in exclude:
                    if type(column) is list:
                        opts = fopts_s2d(column)
                        tmp_str = str(opts['min']) if 'min' in opts else '1'
                        tmp_str += ('..' + str('n' if opts['max'] == 0 else opts['max'])) if 'max' in opts else ('..1' if 'min' in opts else '')
                        # TODO: More options
                        tmp_row.append(tmp_str)
                    else:
                        tmp_str = str(column)
                        tmp_row.append(' ' if tmp_str == '' else tmp_str)

                i += 1
            md_rows.append(' | '.join(tmp_row))

        return '\n'.join(md_rows) + '\n'

    # Structure Formats
    def _formatRecord(self, itm, idx):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        :rtype object - BeautifulSoup
        """
        record = '###3.2.{idx} {name}\n'.format(idx=idx, name=self.formatStr(itm[0]))

        if itm[-2] != '':
            record += itm[-2] + '\n'

        record += '\n**{} (Record)**\n\n'.format(self.formatStr(itm[0]))

        record += self._makeTableHeader([
            ('ID', 'r'),
            ('Name', ),
            ('Type', ),
            ('#', 'r'),
            ('Description', )
        ])

        record += self._makeTableBody(itm[-1])
        return record + '\n'

    def _formatChoice(self, itm, idx):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        :rtype object - BeautifulSoup
        """
        choice = '###3.2.{idx} {name}\n'.format(idx=idx, name=self.formatStr(itm[0]))

        if itm[-2] != '':
            choice += '\n' + itm[-2] + '\n'

        opts = topts_s2d(itm[2])
        choice += '\n**{name} (Choice{opts})**\n\n'.format(name=self.formatStr(itm[0]), opts=('' if len(opts.keys()) == 0 else ' ' + json.dumps(opts)))

        choice += self._makeTableHeader([
            ('ID', 'r'),
            ('Name',),
            ('Type',),
            ('Description',)
        ])

        choice += self._makeTableBody(itm[-1], exclude=(3, ))
        return choice + '\n'

    def _formatMap(self, itm, idx):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        :rtype object - BeautifulSoup
        """
        map = '###3.2.{idx} {name}\n'.format(idx=idx, name=self.formatStr(itm[0]))

        if itm[-2] != '':
            map += itm[-2] + '\n'

        opts = topts_s2d(itm[2])
        map += '\n**{name} (Map{opts})**\n\n'.format(name=self.formatStr(itm[0]), opts=('' if len(opts.keys()) == 0 else ' ' + json.dumps(opts)))

        map += self._makeTableHeader([
            ('ID', 'r'),
            ('Name',),
            ('Type',),
            ('#', 'r'),
            ('Description',)
        ])

        map += self._makeTableBody(itm[-1])

        return map + '\n'

    def _formatEnumerated(self, itm, idx):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        :rtype object - BeautifulSoup
        """
        enumerated = '###3.2.{idx} {name}\n'.format(idx=idx, name=self.formatStr(itm[0]))

        if itm[-2] != '':
            enumerated += itm[-2] + '\n'

        opts = topts_s2d(itm[2])
        enumerated += '\n**{name} (Enumerated{compact})**\n\n'.format(name=self.formatStr(itm[0]), compact=('.Tag' if 'compact' in opts else ''))

        if 'compact' in opts:
            enumerated += self._makeTableHeader([
                ('Value', 'r'),
                ('Description', )
            ])

            enumerated += self._makeTableBody(
                [[row[0], '{} -- {}'.format(row[1], row[2])] for row in itm[-1]]
            )
        else:
            enumerated += self._makeTableHeader([
                ('ID', 'r'),
                ('Name', ),
                ('Description', )
            ])
            enumerated += self._makeTableBody(itm[-1])
        
        return enumerated + '\n'

    def _formatArray(self, itm, idx):  # TODO: what should this do??
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        :rtype object - BeautifulSoup
        """
        array = '###3.2.{idx} {name}\n'.format(idx=idx, name=self.formatStr(itm[0]))

        if itm[-2] != '':
            array += '\n' + itm[-2] + '\n'

        array += '\n**{} (Array)**\n\n'.format(self.formatStr(itm[0]))

        array += self._makeTableHeader([
            ('ID', 'r'),
            ('Type', ),
            ('#', 'r'),
            ('Description', )
        ])

        array += self._makeTableBody([[row[0], row[2], row[3], '"{}": {}'.format(row[1], row[4])] for row in itm[-1]])
        return array + '\n'

    def _formatArrayOf(self, itm, idx):  # TODO: what should this do??
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :return: formatted arrayof
        :rtype object - BeautifulSoup
        """
        arrayOf = '###3.2.{idx} {name}\n'.format(idx=idx, name=self.formatStr(itm[0]))

        if itm[-1] != '':
            arrayOf += '\n' + itm[-1] + '\n'

        field_opts = topts_s2d(itm[2])
        arrayOf += '\n**{name} (ArrayOf.{type} [\'max\', \'min\'])**\n'.format(
            name=self.formatStr(itm[0]),
            min=field_opts.get('min', ''),
            max=field_opts.get('max', ''),
            type=self.formatStr(field_opts.get('rtype', 'string'))
        )

        return arrayOf + '\n'


def md_dumps(jadn):
    """
    Produce CDDL schema from JADN schema
    :arg jadn: JADN Schema to convert
    :type jadn: str or dict
    :return: Protobuf3 schema
    :rtype str
    """
    return JADNtoMD(jadn).md_dump()


def md_dump(jadn, fname, source=""):
    with open(fname, "w") as f:
        if source:
            f.write("<!-- Generated from {}, {} -->\n".format(source, datetime.ctime(datetime.now())))
        f.write(md_dumps(jadn))

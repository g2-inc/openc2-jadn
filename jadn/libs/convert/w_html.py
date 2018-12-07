import json
import lesscpy
import re
import os

from bs4 import BeautifulSoup
from datetime import datetime
from html5print import CSSBeautifier

from ..codec.codec_utils import fopts_s2d, topts_s2d


class JADNtoHTML(object):
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

        self._themeFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'theme.css')  # Default theme

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

        for t in jadn['types']:
            if t[1] in self._structFormats.keys():
                self._types.append(t)

            else:
                self._custom.append(t)

    def _format_html(self, html):
        formatted = ''
        nested_tags = []

        tmp_format = []
        for elm in str(html).replace('\n', '').split('><'):
            elm = '<' + elm if not elm.startswith('<') else elm
            elm = elm + '>' if not elm.endswith('>') else elm
            tmp_format.append(elm)

        i = 0
        while i < len(tmp_format):
            line = tmp_format[i].strip()
            tag = re.sub(r'\s*?<\/?(?P<tag>[\w]+)(\s|>).*$', '\g<tag>', str(line))

            if tag == 'style':
                styles = line[line.index('>')+1:line.rindex('<')]
                styles_formatted = CSSBeautifier.beautify(styles, 5)
                if styles_formatted == '':
                    formatted += '{indent}{initTag}</style>\n'.format(
                        indent='\t'*len(nested_tags),
                        initTag=line
                    )
                    i += 1
                else:
                    formatted += '{indent}{initTag}\n{styles}\n{indent}{closeTag}\n'.format(
                        indent='\t'*(len(nested_tags)),
                        initTag=line[:line.index('>')+1],
                        styles=re.sub(r'^(?P<start>.)', '{}\g<start>'.format('\t'*(len(nested_tags)+1)), str(styles_formatted), flags=re.M),
                        closeTag=line[line.rindex('<'):]
                    )

            elif re.match(r'^<{tag}.*?<\/{tag}>$'.format(tag=tag), str(line)):
                formatted += ('\t' * len(nested_tags)) + line + '\n'

            elif line.startswith('<!') or line.endswith('/>'):
                formatted += ('\t'*len(nested_tags)) + line + '\n'

            elif line.endswith('</' + (nested_tags[-1] if len(nested_tags) > 0 else '') + '>'):
                nested_tags.pop()
                formatted += ('\t'*len(nested_tags)) + line + '\n'

            else:
                formatted += ('\t' * len(nested_tags)) + line + '\n'
                if not line.endswith('{tag}/>'.format(tag=tag)):
                    nested_tags.append(tag)
            i += 1

        return formatted

    def html_dump(self, styles=''):
        html = BeautifulSoup('''
            <!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <title>{title} v.{version}</title>
                    <style type="text/css">{theme}</style>
                </head>
                <body>
                    <div id='schema'>
                        <h1>Schema</h1>
                        <div id='meta'></div>
                        <div id='types'></div>
                    </div>
                </body>
            </html>
        '''.format(
            title=self._meta.get('module', 'JADN Schema Conversion'),
            version=self._meta.get('version', '0'),
            theme=self.loadStyles(styles)
        ), 'lxml')

        html.body.select('div#meta')[0].append(self.makeHeader())

        html.body.select('div#types')[0].append(self.makeStructures())

        html.body.select('div#types')[0].append(self.makeCustom())

        return self._format_html(html)

    def loadStyles(self, styles):
        if styles in ['', ' ', None]:
            # Check is theme exists
            return open(self._themeFile, 'r').read() if os.path.isfile(self._themeFile) else ''

        fname, ext = os.path.splitext(styles)
        if ext not in ['.css', '.less']:
            raise TypeError('Styles are not in css or less format')

        if os.path.isfile(styles):
            if ext == '.css':
                return open(styles, 'r').read()
            elif ext == '.less':
                return lesscpy.compile(open(styles, 'r'))
            else:
                raise ValueError('The style format specified is an unknown format')
        else:
            raise IOError('The style file specified does not exist: {}'.format(styles))

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
        header_html = BeautifulSoup('', 'lxml')

        meta_table = header_html.new_tag('table')
        meta_order = ['title', 'module', 'description', 'exports', 'imports', 'patch']

        def mkrow(k, v):
            tr = header_html.new_tag('tr')

            key = header_html.new_tag('td')
            key.string = k + ':'
            key['class'] = 'h'
            tr.append(key)

            value = header_html.new_tag('td')
            if type(v) is list:
                value.string = ', '.join(['**{}**: {}'.format(*imp) for imp in v] if type(v[0]) is list else v)
            else:
                value.string = v
            value['class'] = 's'
            tr.append(value)

            meta_table.append(tr)

        for meta in meta_order:
            mkrow(meta, self._meta.get(meta, ''))

        header_html.append(meta_table)

        return header_html

    def makeStructures(self):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        :rtype object - BeautifulSoup
        """
        structure_html = BeautifulSoup('', 'lxml')

        header = structure_html.new_tag('h2')
        header.string = '3.2 Structure Types'
        structure_html.append(header)

        i = 1
        for t in self._types:
            df = self._structFormats.get(t[1], None)

            if df is not None:
                structure_html.append(df(t, i))
                i += 1

        return structure_html

    def makeCustom(self):
        """
        Create the custom definitions for the schema
        :return: custom definitions for the schema
        :rtype object - BeautifulSoup
        """
        custom_html = BeautifulSoup('', 'lxml')

        header = custom_html.new_tag('h2')
        header.string = '3.3 Primitive Types'
        custom_html.append(header)

        fields_table = custom_html.new_tag('table')

        fields_table.append(self._makeTableHeader([
            ('Name', {'class': 's'}),
            ('Type', {'class': 's'}),
            ('Description', {'class': 's'})
        ]))

        body = []
        for row in self._custom:
            opts = topts_s2d(row[2])
            fmt = ''
            if 'format' in opts:
                fmt = ' ({})'.format(opts['format'])

            body.append([row[0], '{}{}'.format(row[1], fmt), row[3]])

        fields_table.append(self._makeTableBody(
            body,
            columnAttr=[
                {'class': 's'},
                {'class': 's'},
                {'class': 's'},
            ]
        ))

        custom_html.append(fields_table)
        return custom_html

    def _makeTableHeader(self, headers):
        header_html = BeautifulSoup('', 'lxml')

        field_header_row = header_html.new_tag('tr')
        for column in headers:
            header_column = header_html.new_tag('th')
            header_column.string = column[0]

            for arg, val in (column[1] or {}).items():
                header_column[arg] = val

            field_header_row.append(header_column)

        field_header = header_html.new_tag('thead')
        field_header.append(field_header_row)
        header_html.append(field_header)

        return header_html

    def _makeTableBody(self, rows, columnAttr=[], exclude=()):
        body_html = BeautifulSoup('', 'lxml')
        field_body = body_html.new_tag('tbody')

        for row in rows:
            i = 0
            field_row = body_html.new_tag('tr')

            for column in row:
                if i not in exclude:
                    row_column = body_html.new_tag('td')
                    if type(column) is list:
                        opts = fopts_s2d(column)
                        tmp_str = str(opts['min']) if 'min' in opts else '1'
                        tmp_str += ('..' + str('n' if opts['max'] == 0 else opts['max'])) if 'max' in opts else ('..1' if 'min' in opts else '')
                        # TODO: More options
                        row_column.string = tmp_str
                    else:
                        tmp_str = str(column)
                        row_column.string = ' ' if tmp_str == '' else tmp_str

                    for arg, val in (columnAttr[i] if len(columnAttr) > i else {}).items():
                        row_column[arg] = val
                i += 1
                field_row.append(row_column)
            field_body.append(field_row)

        body_html.append(field_body)
        return body_html

    # Structure Formats
    def _formatRecord(self, itm, idx):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        :rtype object - BeautifulSoup
        """
        record_html = BeautifulSoup('', 'lxml')
        header = record_html.new_tag('h3')
        header.string = '3.2.{idx} {name}'.format(idx=idx, name=self.formatStr(itm[0]))
        record_html.append(header)

        if itm[-2] != '':
            comment = record_html.new_tag('h4')
            comment.string = itm[-2]
            record_html.append(comment)

        fields_table = record_html.new_tag('table')

        field_caption = record_html.new_tag('caption')
        field_caption.string = '{} (Record)'.format(self.formatStr(itm[0]))
        fields_table.append(field_caption)

        fields_table.append(self._makeTableHeader([
            ('ID', {'class': 'n'}),
            ('Name', {'class': 's'}),
            ('Type', {'class': 's'}),
            ('#', {'class': 'n'}),
            ('Description', {'class': 's'})
        ]))
        fields_table.append(self._makeTableBody(itm[-1], columnAttr=[
            {'class': 'n'},
            {'class': 's'},
            {'class': 's'},
            {'class': 'n'},
            {'class': 's'}
        ]))

        record_html.append(fields_table)
        return record_html

    def _formatChoice(self, itm, idx):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        :rtype object - BeautifulSoup
        """
        choice_html = BeautifulSoup('', 'lxml')
        header = choice_html.new_tag('h3')
        header.string = '3.2.{idx} {name}'.format(idx=idx, name=self.formatStr(itm[0]))
        choice_html.append(header)

        if itm[-2] != '':
            comment = choice_html.new_tag('h4')
            comment.string = itm[-2]
            choice_html.append(comment)

        fields_table = choice_html.new_tag('table')

        field_caption = choice_html.new_tag('caption')
        opts = topts_s2d(itm[2])
        field_caption.string = '{name} (Choice{opts})'.format(name=self.formatStr(itm[0]), opts=('' if len(opts.keys()) == 0 else ' ' + json.dumps(opts)))
        fields_table.append(field_caption)

        fields_table.append(self._makeTableHeader([
            ('ID', {'class': 'n'}),
            ('Name', {'class': 's'}),
            ('Type', {'class': 's'}),
            ('Description', {'class': 's'})
        ]))
        fields_table.append(self._makeTableBody(itm[-1], columnAttr=[
            {'class': 'n'},
            {'class': 's'},
            {'class': 's'},
            {},
            {'class': 's'},
        ], exclude=(3, )))

        choice_html.append(fields_table)
        return choice_html

    def _formatMap(self, itm, idx):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        :rtype object - BeautifulSoup
        """
        map_html = BeautifulSoup('', 'lxml')
        header = map_html.new_tag('h3')
        header.string = '3.2.{idx} {name}'.format(idx=idx, name=self.formatStr(itm[0]))
        map_html.append(header)

        if itm[-2] != '':
            comment = map_html.new_tag('h4')
            comment.string = itm[-2]
            map_html.append(comment)

        fields_table = map_html.new_tag('table')

        field_caption = map_html.new_tag('caption')
        opts = topts_s2d(itm[2])
        field_caption.string = '{name} (Map{opts})'.format(name=self.formatStr(itm[0]), opts=('' if len(opts.keys()) == 0 else ' ' + json.dumps(opts)))
        fields_table.append(field_caption)

        fields_table.append(self._makeTableHeader([
            ('ID', {'class': 'n'}),
            ('Name', {'class': 's'}),
            ('Type', {'class': 's'}),
            ('#', {'class': 'n'}),
            ('Description', {'class': 's'})
        ]))
        fields_table.append(self._makeTableBody(itm[-1], columnAttr=[
            {'class': 'n'},
            {'class': 's'},
            {'class': 's'},
            {'class': 'n'},
            {'class': 's'},
        ]))

        map_html.append(fields_table)
        return map_html

    def _formatEnumerated(self, itm, idx):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        :rtype object - BeautifulSoup
        """
        enumerated_html = BeautifulSoup('', 'lxml')
        header = enumerated_html.new_tag('h3')
        header.string = '3.2.{idx} {name}'.format(idx=idx, name=self.formatStr(itm[0]))
        enumerated_html.append(header)

        if itm[-2] != '':
            comment = enumerated_html.new_tag('h4')
            comment.string = itm[-2]
            enumerated_html.append(comment)

        fields_table = enumerated_html.new_tag('table')

        field_caption = enumerated_html.new_tag('caption')
        opts = topts_s2d(itm[2])
        field_caption.string = '{name} (Enumerated{compact})'.format(name=self.formatStr(itm[0]), compact=('.Tag' if 'compact' in opts else ''))
        fields_table.append(field_caption)

        bodyAttr = [
            {'class': 'n'},
            {'class': 's'},
            {'class': 's'},
        ]

        if 'compact' in opts:
            fields_table.append(self._makeTableHeader([
                ('Value', {'class': 'n'}),
                ('Description', {'class': 's'})
            ]))
            fields_table.append(self._makeTableBody(
                [[row[0], '{} -- {}'.format(row[1], row[2])] for row in itm[-1]],
                columnAttr=bodyAttr
            ))
        else:
            fields_table.append(self._makeTableHeader([
                ('ID', {'class': 'n'}),
                ('Name', {'class': 's'}),
                ('Description', {'class': 's'})
            ]))
            fields_table.append(self._makeTableBody(itm[-1], columnAttr=bodyAttr))

        enumerated_html.append(fields_table)
        return enumerated_html

    def _formatArray(self, itm, idx):  # TODO: what should this do??
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        :rtype object - BeautifulSoup
        """
        array_html = BeautifulSoup('', 'lxml')
        header = array_html.new_tag('h3')
        header.string = '3.2.{idx} {name}'.format(idx=idx, name=self.formatStr(itm[0]))
        array_html.append(header)

        if itm[-2] != '':
            comment = array_html.new_tag('h4')
            comment.string = itm[-2]
            array_html.append(comment)

        fields_table = array_html.new_tag('table')

        field_caption = array_html.new_tag('caption')
        field_caption.string = '{} (Array)'.format(self.formatStr(itm[0]))
        fields_table.append(field_caption)

        fields_table.append(self._makeTableHeader([
            ('ID', {'class': 'n'}),
            ('Type', {'class': 's'}),
            ('#', {'class': 'n'}),
            ('Description', {'class': 's'})
        ]))
        fields_table.append(self._makeTableBody(
            [[row[0], row[2], row[3], '"{}": {}'.format(row[1], row[4])] for row in itm[-1]],
            columnAttr=[
                {'class': 'n'},
                {'class': 's'},
                {'class': 'n'},
                {'class': 's'},
            ]
        ))

        array_html.append(fields_table)
        return array_html

    def _formatArrayOf(self, itm, idx):  # TODO: what should this do??
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :return: formatted arrayof
        :rtype object - BeautifulSoup
        """
        arrayOf_html = BeautifulSoup('', 'lxml')
        header = arrayOf_html.new_tag('h3')
        header.string = '3.2.{idx} {name}'.format(idx=idx, name=self.formatStr(itm[0]))
        arrayOf_html.append(header)

        if itm[-1] != '':
            comment = arrayOf_html.new_tag('h4')
            comment.string = itm[-1]
            arrayOf_html.append(comment)

        options = arrayOf_html.new_tag('p')
        field_opts = topts_s2d(itm[2])
        options.string = '{name} (ArrayOf.{type} [\'max\', \'min\'])'.format(
            name=self.formatStr(itm[0]),
            min=field_opts.get('min', ''),
            max=field_opts.get('max', ''),
            type=self.formatStr(field_opts.get('rtype', 'string'))
        )

        arrayOf_html.append(options)
        return arrayOf_html


def html_dumps(jadn, styles=''):
    """
    Produce CDDL schema from JADN schema
    :arg jadn: JADN Schema to convert
    :type jadn: str or dict
    :return: Protobuf3 schema
    :rtype str
    """
    return JADNtoHTML(jadn).html_dump(styles)


def html_dump(jadn, fname, source="", styles=''):
    with open(fname, "w") as f:
        if source:
            f.write("<!-- Generated from {}, {} -->\n".format(source, datetime.ctime(datetime.now())))
        f.write(html_dumps(jadn, styles))

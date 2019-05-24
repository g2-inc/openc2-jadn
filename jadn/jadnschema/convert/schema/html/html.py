import json
import lesscpy
import re
import os

from datetime import datetime

from ..base_dump import JADNConverterBase


class JADNtoHTML(JADNConverterBase):
    _themeFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'theme.css')  # Default theme

    def html_dump(self, styles=''):
        """
        Convert the given JADN schema to HTML Tables
        :param styles: CSS or Less styles to add to the HTML
        :return: formatted HTML tables of the given JADN Schema
        """
        html = f'''<!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <title>{self._meta.get('module', 'JADN Schema Convert')} v.{self._meta.get('version', '0')}</title>
                    <style type="text/css">{self._loadStyles(styles)}</style>
                </head>
                <body>
                    <div id='schema'>
                        <h1>Schema</h1>
                        <div id='meta'>{self.makeHeader()}</div>
                        <div id='types'>
                            {self.makeStructures()}
                            {self.makeCustom()}
                        </div>
                    </div>
                </body>
            </html>'''

        return self._format_html(html)

    def makeHeader(self):
        """
        Create the headers for the schema
        :return: header for schema
        """
        def mkrow(k, v):
            if type(v) is list:
                v = ', '.join(['**{}**: {}'.format(*i) for i in v] if type(v[0]) is list else v) if len(v) > 0 else 'N/A'
            return f"<tr><td class='h'>{k}:</td><td class='s'>{v}</td></tr>"

        meta_rows = ''.join([mkrow(meta, self._meta.get(meta, '')) for meta in self._meta_order])
        return f'<table>{meta_rows}</table>'

    def makeStructures(self):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        """
        structure_html = '<h2>3.2 Structure Types</h2>'

        i = 1
        for t in self._types:
            df = getattr(self, f"_format{t.type}", None)

            if df is not None:
                structure_html += df(t, i)
                i += 1

        return structure_html

    def makeCustom(self):
        """
        Create the custom definitions for the schema
        :return: custom definitions for the schema
        """
        custom_html = f'<h2>3.3 Primitive Types</h2>'

        table_headers = dict(
            Name={'class': 's'},
            Type={'class': 's'},
            Description={'class': 's'}
        )

        body = []
        for row in self._custom:
            opts = row.opts
            fmt = f" ({opts['format']})" if 'format' in opts else ''

            body.append(dict(
                Name=row['name'],
                Type=f'{row.type}{fmt}',
                Description=row.desc
            ))

        return custom_html + self._makeTable(table_headers, body)

    # Structure Formats
    def _formatRecord(self, itm, idx):
        """
        Formats records for the given schema type
        :param itm: record to format
        :param idx: index of the record item
        :return: formatted record
        """
        record_html = f'<h3>3.2.{idx} {self.formatStr(itm.name)}</h3>'

        if itm.desc != '':
            record_html += f'<h4>{itm.desc}</h4>'

        caption = f'{self.formatStr(itm.name)} (Record)'

        table_opts = {
            'ID': {'class': 'n'},
            'Name': {'class': 's'},
            'Type': {'class': 's'},
            '#': {'class': 'n'},
            'Description': {'class': 's'},
        }

        return record_html + self._makeTable(table_opts, itm.fields, caption)

    def _formatChoice(self, itm, idx):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :param idx: index of the choice item
        :return: formatted choice
        """
        choice_html = f'<h3>3.2.{idx} {self.formatStr(itm.name)}</h3>'

        if itm.desc != '':
            choice_html += f'<h4>{itm.desc}</h4>'

        caption = f"{self.formatStr(itm.name)} (Choice{'' if len(itm.opts.keys()) == 0 else f' {json.dumps(itm.opts)}'})"

        table_opts = {
            'ID': {'class': 'n'},
            'Name': {'class': 's'},
            'Type': {'class': 's'},
            'Description': {'class': 's'}
        }

        return choice_html + self._makeTable(table_opts, itm.fields, caption)

    def _formatMap(self, itm, idx):
        """
        Formats map for the given schema type
        :param itm: map to format
        :param idx: index of the map item
        :return: formatted map
        """
        map_html = f'<h3>3.2.{idx} {self.formatStr(itm.name)}</h3>'

        if itm.desc != '':
            map_html += f'<h4>{itm.desc}</h4>'

        caption = f"{self.formatStr(itm.name)} (Map{'' if len(itm.opts.keys()) == 0 else f' {json.dumps(itm.opts)}'})"

        table_opts = {
            'ID': {'class': 'n'},
            'Name': {'class': 's'},
            'Type': {'class': 's'},
            '#': {'class': 'n'},
            'Description': {'class': 's'},
        }

        return map_html + self._makeTable(table_opts, itm.fields, caption)

    def _formatEnumerated(self, itm, idx):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :param idx: index of the enumerated item
        :return: formatted enum
        """
        enumerated_html = f'<h3>3.2.{idx} {self.formatStr(itm.name)}</h3>'

        if itm.desc != '':
            enumerated_html += f'<h4>{itm.desc}</h4>'

        caption = f"{self.formatStr(itm.name)} (Enumerated{'.ID' if 'id' in itm.opts else ''})"

        if 'compact' in itm.opts:
            table_opts = dict(
                Value={'class': 'n'},
                Description={'class': 's'}
            )
            body = [{'Value': row.id, 'Description': f'{row.value} -- {row.desc}'} for row in itm.fields]

        else:
            table_opts = dict(
                ID={'class': 'n'},
                Name={'class': 's'},
                Description={'class': 's'}
            )
            body = [{'ID': row.id, 'Name': row.value, 'Description': row.desc} for row in itm.fields]

        return enumerated_html + self._makeTable(table_opts, body, caption)

    def _formatArray(self, itm, idx):  # TODO: what should this do??
        """
        Formats array for the given schema type
        :param itm: array to format
        :param idx: index of the array item
        :return: formatted array
        """
        array_html = f'<h3>3.2.{idx} {self.formatStr(itm.name)}</h3>'

        if itm.desc != '':
            array_html += f'<h4>{itm.desc}</h4>'

        caption = f'{self.formatStr(itm.name)} (Array)'

        table_opts = {
            'ID': {'class': 'n'},
            'Type': {'class': 's'},
            '#': {'class': 'n'},
            'Description': {'class': 's'},
        }
        body = [{'ID': row.id, 'Type': row.type, '#': row.opts, 'Description': f'"{row.name}": {row.desc}'} for row in itm.fields]

        return array_html + self._makeTable(table_opts, body, caption)

    def _formatArrayOf(self, itm, idx):  # TODO: what should this do??
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :param idx: index of the arrayof item
        :return: formatted arrayof
        """
        arrayOf_html = f'<h3>3.2.{idx} {self.formatStr(itm.name)}</h3>'

        if itm.desc != '':
            arrayOf_html += f'<h4>{itm.desc}</h4>'

        options = f"<p>{self.formatStr(itm.name)} (ArrayOf.{self.formatStr(itm.opts.get('rtype', 'string'))} [\'{itm.opts.get('max', '1')}\', \'{itm.opts.get('min', '1')}\'])</p>"

        arrayOf_html += options
        return arrayOf_html

    # Helper Functions
    def _format_html(self, html):
        """
        Format the HTML to a predefined standard
        :param html: HTML string to format
        :return: formatted HTML
        """
        html = ''.join(l.strip() for l in html.split('\n'))
        html_formatted = ''
        nested_tags = []

        tmp_format = []
        for elm in html.split('><'):
            elm = '<' + elm if not elm.startswith('<') else elm
            elm = elm + '>' if not elm.endswith('>') else elm
            tmp_format.append(elm)

        i = 0
        while i < len(tmp_format):
            line = tmp_format[i].strip()
            tag = re.sub(r'\s*?<\/?(?P<tag>[\w]+)(\s|>).*$', '\g<tag>', str(line))
            indent = '\t' * len(nested_tags)

            if tag == 'style':
                styles = line[line.index('>')+1:line.rindex('<')]
                styles_formatted = self._format_css(styles)
                if styles_formatted == '':
                    html_formatted += f'{indent}{line}</style>\n'
                    i += 1
                else:
                    styles_indent = '\t' * (len(nested_tags) + 1)
                    styles = re.sub(r'^(?P<start>.)', f"{styles_indent}\g<start>", str(styles_formatted), flags=re.M)
                    html_formatted += f"{indent}{line[:line.index('>')+1]}\n{styles}\n{indent}{line[line.rindex('<'):]}\n"

            elif re.match(rf'^<{tag}.*?<\/{tag}>$', str(line)):
                html_formatted += f'{indent}{line}\n'

            elif line.startswith('<!') or line.endswith('/>'):
                html_formatted += f'{indent}{line}\n'

            elif line.endswith('</' + (nested_tags[-1] if len(nested_tags) > 0 else '') + '>'):
                nested_tags.pop()
                indent = '\t' * len(nested_tags)
                html_formatted += f'{indent}{line}\n'

            else:
                html_formatted += f'{indent}{line}\n'
                if not line.endswith(f'{tag}/>'):
                    nested_tags.append(tag)
            i += 1

        return html_formatted

    def _format_css(self, css):
        """
        Format the CSS to a predefined standard
        :param css: CSS string to format
        :return: formatted CSS
        """
        line_breaks = ('\*/', '{', '}', ';')
        css_formatted = re.sub(rf"(?P<term>{'|'.join(line_breaks)})", '\g<term>\n', css)
        css_formatted = css_formatted[:-1]

        return '\n'.join(re.sub(r'\s{4}', '\t', line) for line in css_formatted.split('\n'))

    def _loadStyles(self, styles):
        """
        Load the given styles
        :param styles: the CSS or Less file location
        :return:
        """
        if styles in ['', ' ', None]:  # Check if theme exists
            return open(self._themeFile, 'r').read() if os.path.isfile(self._themeFile) else ''

        fname, ext = os.path.splitext(styles)
        if ext not in ['.css', '.less']:  # Check valid theme format
            raise TypeError('Styles are not in css or less format')

        if os.path.isfile(styles):
            if ext == '.css':
                return open(styles, 'r').read()
            elif ext == '.less':
                return lesscpy.compile(open(styles, 'r'))
            else:
                raise ValueError('The style format specified is an unknown format')
        else:
            raise IOError(f'The style file specified does not exist: {styles}')

    def _makeTable(self, headers={}, rows=[], caption=''):
        """
        Create a table using the given header and row values
        :param headers: table header names and attributes
        :param rows: row values
        :return: formatted HTML table
        """
        table_contents = []

        # Caption
        if caption not in ['', ' ', None]:
            table_contents.append(f'<caption>{caption}</caption>')

        # Headers
        column_headers = []
        for column, opts in headers.items():
            attrs = ' '.join(f'{arg}="{val}"' for arg, val in opts.items())
            column_headers.append(f'<th {attrs}>{column}</th>')

        table_contents.append(f"<thead><tr>{''.join(column_headers)}</tr></thead>")

        # Body
        table_body = []
        for row in rows:
            field_row = ''
            for column, opts in headers.items():
                column = column if column in row else self._table_field_headers.get(column, column)
                if isinstance(column, str):
                    cell = row.get(column, '')
                else:
                    cell = list(filter(None, [row.get(c, None) for c in column]))
                    cell = cell[0] if len(cell) == 1 else ''

                if type(cell) is list:
                    opts = cell
                    # TODO: Validate cardinality
                    tmp_str = str(opts['min']) if 'min' in opts else '1'
                    tmp_str += ('..' + str('n' if opts['max'] == 0 else opts['max'])) if 'max' in opts else ('..1' if 'min' in opts else '')
                    # TODO: More options
                    cell_val = tmp_str
                else:
                    tmp_str = str(cell)
                    cell_val = ' ' if tmp_str == '' else tmp_str

                attrs = ' '.join(f'{arg}="{val}"' for arg, val in headers.get(column, {}).items())
                field_row += f'<td {attrs}>{cell_val}</td>'

            table_body.append(f'<tr>{field_row}</tr>')

        table_contents.append(f"<tbody>{''.join(table_body)}</tbody>")

        table_contents = ''.join(table_contents)
        return f'<table>{table_contents}</table>'


def html_dumps(jadn, styles=''):
    """
    Produce HTML schema from JADN schema
    :param jadn: JADN Schema to convert
    :param styles: CSS or Less styles to add to the converted HTML
    :return: HTML Table schema
    """
    return JADNtoHTML(jadn).html_dump(styles)


def html_dump(jadn, fname, source="", styles=''):
    """
    Produce HTML tables from the given JADN schema and write to file provided
    :param jadn: JADN Schema to convert
    :param fname: Name of file to write
    :param source: Name of the original JADN schema file
    :param styles: CSS or Less styles to add to the converted HTML
    :return: None
    """
    with open(fname, "w") as f:
        if source:
            f.write(f"<!-- Generated from {source}, {datetime.ctime(datetime.now())} -->\n")
        f.write(html_dumps(jadn, styles))

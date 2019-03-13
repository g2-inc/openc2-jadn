import json
import lesscpy
import re
import os

from bs4 import BeautifulSoup
from datetime import datetime
from html5print import CSSBeautifier


from ..base_dump import JADNConverterBase
from .... import (
    jadn_utils
)


class JADNtoHTML(JADNConverterBase):
    def __init__(self, jadn):
        """
        Schema Converter Init
        :param jadn: str or dict of the JADN schema
        """
        super(JADNtoHTML, self).__init__(jadn)
        self._themeFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'theme.css')  # Default theme

    def html_dump(self, styles=''):
        """
        Convert the given JADN schema to HTML Tables
        :param styles: CSS or Less styles to add to the HTML
        :return: formatted HTML tables of the given JADN Schema
        """
        html = BeautifulSoup(f'''
            <!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <title>{self._meta.get('module', 'JADN Schema Convert')} v.{self._meta.get('version', '0')}</title>
                    <style type="text/css">{self._loadStyles(styles)}</style>
                </head>
                <body>
                    <div id='schema'>
                        <h1>Schema</h1>
                        <div id='meta'></div>
                        <div id='types'></div>
                    </div>
                </body>
            </html>
        ''', 'html.parser')

        html.body.select('div#meta')[0].append(self.makeHeader())
        html.body.select('div#types')[0].append(self.makeStructures())
        html.body.select('div#types')[0].append(self.makeCustom())

        return self._format_html(html)

    def makeHeader(self):
        """
        Create the headers for the schema
        :return: header for schema
        """
        header_html = BeautifulSoup('', 'html.parser')

        meta_table = header_html.new_tag('table')

        def mkrow(k, v):
            tr = header_html.new_tag('tr')

            key = header_html.new_tag('td')
            key.string = k + ':'
            key['class'] = 'h'
            tr.append(key)

            value = header_html.new_tag('td')
            if type(v) is list:
                v = ', '.join(['**{}**: {}'.format(*imp) for imp in v] if type(v[0]) is list else v) if len(v) > 0 else 'N/A'

            value.string = v
            value['class'] = 's'
            tr.append(value)

            meta_table.append(tr)

        for meta in self._meta_order:
            mkrow(meta, self._meta.get(meta, ''))

        header_html.append(meta_table)

        return header_html

    def makeStructures(self):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        """
        structure_html = BeautifulSoup('', 'html.parser')

        header = structure_html.new_tag('h2')
        header.string = '3.2 Structure Types'
        structure_html.append(header)

        i = 1
        for t in self._types:
            df = self._structFun(t.type)

            if df is not None:
                structure_html.append(df(t, i))
                i += 1

        return structure_html

    def makeCustom(self):
        """
        Create the custom definitions for the schema
        :return: custom definitions for the schema
        """
        custom_html = BeautifulSoup('', 'html.parser')

        header = custom_html.new_tag('h2')
        header.string = '3.3 Primitive Types'
        custom_html.append(header)

        table_headers = dict(
            Name={'class': 's'},
            Type={'class': 's'},
            Description={'class': 's'}
        )

        body = []
        for row in self._custom:
            opts = jadn_utils.topts_s2d(row.opts)
            fmt = f" ({opts['format']})" if 'format' in opts else ''

            body.append(dict(
                Name=row['name'],
                Type=f'{row.type}{fmt}',
                Description=row.desc
            ))

        custom_html.append(self._makeTable(table_headers, body))
        return custom_html

    # Structure Formats
    def _formatRecord(self, itm, idx):
        """
        Formats records for the given schema type
        :param itm: record to format
        :param idx: index of the record item
        :return: formatted record
        """
        record_html = BeautifulSoup('', 'html.parser')
        header = record_html.new_tag('h3')
        header.string = f'3.2.{idx} {self.formatStr(itm.name)}'
        record_html.append(header)

        if itm.desc != '':
            comment = record_html.new_tag('h4')
            comment.string = itm.desc
            record_html.append(comment)

        fields_table = record_html.new_tag('table')

        field_caption = record_html.new_tag('caption')
        field_caption.string = f'{self.formatStr(itm.name)} (Record)'
        fields_table.append(field_caption)

        table_opts = {
            'ID': {'class': 'n'},
            'Name': {'class': 's'},
            'Type': {'class': 's'},
            '#': {'class': 'n'},
            'Description': {'class': 's'},
        }

        fields_table.append(self._makeTable(table_opts, itm.fields))

        record_html.append(fields_table)
        return record_html

    def _formatChoice(self, itm, idx):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :param idx: index of the choice item
        :return: formatted choice
        """
        choice_html = BeautifulSoup('', 'html.parser')
        header = choice_html.new_tag('h3')
        header.string = f'3.2.{idx} {self.formatStr(itm.name)}'
        choice_html.append(header)

        if itm.desc != '':
            comment = choice_html.new_tag('h4')
            comment.string = itm.desc
            choice_html.append(comment)

        fields_table = choice_html.new_tag('table')

        field_caption = choice_html.new_tag('caption')
        opts = jadn_utils.topts_s2d(itm.opts)
        field_caption.string = f"{self.formatStr(itm.name)} (Choice{'' if len(opts.keys()) == 0 else f' {json.dumps(opts)}'})"
        fields_table.append(field_caption)

        table_opts = {
            'ID': {'class': 'n'},
            'Name': {'class': 's'},
            'Type': {'class': 's'},
            'Description': {'class': 's'}
        }

        fields_table.append(self._makeTable(table_opts, itm.fields))

        choice_html.append(fields_table)
        return choice_html

    def _formatMap(self, itm, idx):
        """
        Formats map for the given schema type
        :param itm: map to format
        :param idx: index of the map item
        :return: formatted map
        """
        map_html = BeautifulSoup('', 'html.parser')
        header = map_html.new_tag('h3')
        header.string = f'3.2.{idx} {self.formatStr(itm.name)}'
        map_html.append(header)

        if itm.desc != '':
            comment = map_html.new_tag('h4')
            comment.string = itm.desc
            map_html.append(comment)

        fields_table = map_html.new_tag('table')

        field_caption = map_html.new_tag('caption')
        opts = jadn_utils.topts_s2d(itm.opts)
        field_caption.string = f"{self.formatStr(itm.name)} (Map{'' if len(opts.keys()) == 0 else f' {json.dumps(opts)}'})"
        fields_table.append(field_caption)

        table_opts = {
            'ID': {'class': 'n'},
            'Name': {'class': 's'},
            'Type': {'class': 's'},
            '#': {'class': 'n'},
            'Description': {'class': 's'},
        }

        fields_table.append(self._makeTable(table_opts, itm.fields))

        map_html.append(fields_table)
        return map_html

    def _formatEnumerated(self, itm, idx):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :param idx: index of the enumerated item
        :return: formatted enum
        """
        enumerated_html = BeautifulSoup('', 'html.parser')
        header = enumerated_html.new_tag('h3')
        header.string = f'3.2.{idx} {self.formatStr(itm.name)}'
        enumerated_html.append(header)

        if itm.desc != '':
            comment = enumerated_html.new_tag('h4')
            comment.string = itm.desc
            enumerated_html.append(comment)

        fields_table = enumerated_html.new_tag('table')

        field_caption = enumerated_html.new_tag('caption')
        opts = jadn_utils.topts_s2d(itm.opts)
        field_caption.string = f"{self.formatStr(itm.name)} (Enumerated{'.Tag' if 'compact' in opts else ''})"
        fields_table.append(field_caption)

        if 'compact' in opts:
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

        fields_table.append(self._makeTable(table_opts, body))
        enumerated_html.append(fields_table)
        return enumerated_html

    def _formatArray(self, itm, idx):  # TODO: what should this do??
        """
        Formats array for the given schema type
        :param itm: array to format
        :param idx: index of the array item
        :return: formatted array
        """
        array_html = BeautifulSoup('', 'html.parser')
        header = array_html.new_tag('h3')
        header.string = f'3.2.{idx} {self.formatStr(itm.name)}'
        array_html.append(header)

        if itm.desc != '':
            comment = array_html.new_tag('h4')
            comment.string = itm.desc
            array_html.append(comment)

        fields_table = array_html.new_tag('table')

        field_caption = array_html.new_tag('caption')
        field_caption.string = f'{self.formatStr(itm.name)} (Array)'
        fields_table.append(field_caption)

        table_opts = {
            'ID': {'class': 'n'},
            'Type': {'class': 's'},
            '#': {'class': 'n'},
            'Description': {'class': 's'},
        }
        body = [{'ID': row.id, 'Type': row.type, '#': row.opts, 'Description': f'"{row.name}": {row.desc}'} for row in itm.fields]

        fields_table.append(self._makeTable(table_opts, body))

        array_html.append(fields_table)
        return array_html

    def _formatArrayOf(self, itm, idx):  # TODO: what should this do??
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :param idx: index of the arrayof item
        :return: formatted arrayof
        """
        arrayOf_html = BeautifulSoup('', 'html.parser')
        header = arrayOf_html.new_tag('h3')
        header.string = f'3.2.{idx} {self.formatStr(itm.name)}'
        arrayOf_html.append(header)

        if itm.desc != '':
            comment = arrayOf_html.new_tag('h4')
            comment.string = itm.desc
            arrayOf_html.append(comment)

        options = arrayOf_html.new_tag('p')
        field_opts = jadn_utils.topts_s2d(itm.opts)
        options.string = f"{self.formatStr(itm.name)} (ArrayOf.{self.formatStr(field_opts.get('rtype', 'string'))} [\'{field_opts.get('max', '')}\', \'{field_opts.get('min', '')}\'])"

        arrayOf_html.append(options)
        return arrayOf_html

    # Helper Functions
    def _format_html(self, html):
        """
        Format the HTML to a predefined standard
        :param html: HTML string to format
        :return: formatted HTML
        """
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
            indent = '\t' * len(nested_tags)

            if tag == 'style':
                styles = line[line.index('>')+1:line.rindex('<')]
                styles_formatted = CSSBeautifier.beautify(styles, 5)
                if styles_formatted == '':
                    formatted += f'{indent}{line}</style>\n'
                    i += 1
                else:
                    styles_indent = '\t' * (len(nested_tags) + 1)
                    styles = re.sub(r'^(?P<start>.)', f"{styles_indent}\g<start>", str(styles_formatted), flags=re.M)
                    formatted += f"{indent}{line[:line.index('>')+1]}\n{styles}\n{indent}{line[line.rindex('<'):]}\n"

            elif re.match(rf'^<{tag}.*?<\/{tag}>$', str(line)):
                formatted += f'{indent}{line}\n'

            elif line.startswith('<!') or line.endswith('/>'):
                formatted += f'{indent}{line}\n'

            elif line.endswith('</' + (nested_tags[-1] if len(nested_tags) > 0 else '') + '>'):
                nested_tags.pop()
                formatted += f'{indent}{line}\n'

            else:
                formatted += f'{indent}{line}\n'
                if not line.endswith(f'{tag}/>'):
                    nested_tags.append(tag)
            i += 1

        return formatted

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

    def _makeTable(self, headers={}, rows=[]):
        """
        Create a table using the given header and row values
        :param headers: table header names and attributes
        :param rows: row values
        :return: formatted HTML table
        """
        _table = BeautifulSoup('', 'html.parser')
        table_html = _table.new_tag('table')

        # Headers
        table_head = _table.new_tag('thead')
        header_row = _table.new_tag('tr')
        for column, opts in headers.items():
            header_column = _table.new_tag('th')
            header_column.string = column

            for arg, val in opts.items():
                header_column[arg] = val

            header_row.append(header_column)
        table_head.append(header_row)

        # Body
        table_body = _table.new_tag('tbody')
        for row in rows:
            field_row = _table.new_tag('tr')
            for column, opts in headers.items():
                column = column if column in row else self._table_field_headers.get(column, column)
                if isinstance(column, str):
                    cell = row.get(column, '')
                else:
                    cell = list(filter(None, [row.get(c, None) for c in column]))
                    cell = cell[0] if len(cell) == 1 else ''
                row_cell = _table.new_tag('td')

                if type(cell) is list:
                    opts = jadn_utils.fopts_s2d(cell)
                    tmp_str = str(opts['min']) if 'min' in opts else '1'
                    tmp_str += ('..' + str('n' if opts['max'] == 0 else opts['max'])) if 'max' in opts else ('..1' if 'min' in opts else '')
                    # TODO: More options
                    row_cell.string = tmp_str
                else:
                    tmp_str = str(cell)
                    row_cell.string = ' ' if tmp_str == '' else tmp_str

                for arg, val in headers.get(column, {}).items():
                    row_cell[arg] = val

                field_row.append(row_cell)
            table_body.append(field_row)

        table_html.append(table_head)
        table_html.append(table_body)
        _table.append(table_html)
        return _table


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

import json

from datetime import datetime

from ..base_dump import JADNConverterBase
from .... import (
    jadn_utils
)


class JADNtoMD(JADNConverterBase):
    def md_dump(self):
        """
        Convert the given JADN schema to MarkDown Tables
        :return: formatted MarkDown tables of the given JADN Schema
        """
        return self.makeHeader() + self.makeStructures() + self.makeCustom()

    def makeHeader(self):
        """
        Create the headers for the schema
        :return: header for schema
        """
        def mkrow(k, v):
            if type(v) is list:
                v = ', '.join([f'**{i[0]}**: {i[1]}' for i in v] if type(v[0]) is list else v) if len(v) > 0 else 'N/A'
            return f'{k} | {v}'

        return '\n'.join([
            '## Schema',
            '. | .',
            ':--- | ---:',
            *[mkrow(meta, self._meta.get(meta, '')) for meta in self._meta_order]
        ]) + '\n\n'

    def makeStructures(self):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        """
        structure = '##3.2 Structure Types\n'

        i = 1
        for t in self._types:
            df = self._structFun(t.type)

            if df is not None:
                structure += df(t, i)
                i += 1

        return structure

    def makeCustom(self):
        """
        Create the custom definitions for the schema
        :return: custom definitions for the schema
        """
        custom = '##3.3 Primitive Types\n\n'

        table_headers = dict(
            Name={},
            Type={},
            Description={}
        )

        body = []
        for row in self._custom:
            opts = jadn_utils.topts_s2d(row.opts)
            fmt = f" ({opts['format']})" if 'format' in opts else ''

            body.append(dict(
                Name=row.name,
                Type=f'{row.type}{fmt}',
                Description=row.desc
            ))

        custom += self._makeTable(table_headers, body)
        return custom + '\n'

    # Structure Formats
    def _formatRecord(self, itm, idx):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        """
        record = '###3.2.{idx} {name}\n'.format(idx=idx, name=self.formatStr(itm.name))
        record += f'{itm.desc}\n' if itm.desc != '' else ''
        record += '\n**{} (Record)**\n\n'.format(self.formatStr(itm.name))

        table_headers = {
            'ID': {'align': 'r'},
            'Name': {},
            'Type': {},
            '#': {'align': 'r'},
            'Description': {}
        }

        record += self._makeTable(table_headers, itm.fields)
        return record + '\n'

    def _formatChoice(self, itm, idx):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        """
        choice = '###3.2.{idx} {name}\n'.format(idx=idx, name=self.formatStr(itm.name))
        choice += f'{itm.desc}\n' if itm.desc != '' else ''

        opts = jadn_utils.topts_s2d(itm.opts)
        choice += '\n**{name} (Choice{opts})**\n\n'.format(name=self.formatStr(itm.name), opts=('' if len(opts.keys()) == 0 else ' ' + json.dumps(opts)))

        table_headers = {
            'ID': {'align': 'r'},
            'Name': {},
            'Type': {},
            'Description': {}
        }

        choice += self._makeTable(table_headers, itm.fields)
        return choice + '\n'

    def _formatMap(self, itm, idx):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        """
        map = '###3.2.{idx} {name}\n'.format(idx=idx, name=self.formatStr(itm.name))
        map += f'{itm.desc}\n' if itm.desc != '' else ''

        opts = jadn_utils.topts_s2d(itm.opts)
        map += '\n**{name} (Map{opts})**\n\n'.format(name=self.formatStr(itm.name), opts=('' if len(opts.keys()) == 0 else ' ' + json.dumps(opts)))

        table_headers = {
            'ID': {'align': 'r'},
            'Name': {},
            'Type': {},
            '#': {'align': 'r'},
            'Description': {}
        }

        map += self._makeTable(table_headers, itm.fields)
        return map + '\n'

    def _formatEnumerated(self, itm, idx):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        """
        enumerated = '###3.2.{idx} {name}\n'.format(idx=idx, name=self.formatStr(itm.name))
        enumerated += f'{itm.desc}\n' if itm.desc != '' else ''

        opts = jadn_utils.topts_s2d(itm.opts)
        enumerated += '\n**{name} (Enumerated{compact})**\n\n'.format(name=self.formatStr(itm.name), compact=('.Tag' if 'compact' in opts else ''))

        if 'compact' in opts:
            table_headers = dict(
                Value={'align': 'r'},
                Description={}
            )
            body = [dict(Value=row.id, Description='{} -- {}'.format(row.value, row.desc)) for row in itm.fields]
        else:
            table_headers = dict(
                ID={'align': 'r'},
                Name={},
                Description={}
            )
            body = itm.fields

        enumerated += self._makeTable(table_headers, body)
        return enumerated + '\n'

    def _formatArray(self, itm, idx):
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        """
        array = '###3.2.{idx} {name}\n'.format(idx=idx, name=self.formatStr(itm.name))
        array += f'{itm.desc}\n' if itm.desc != '' else ''
        array += '\n**{} (Array)**\n\n'.format(self.formatStr(itm.name))

        table_headers = {
            'ID': {'align': 'r'},
            'Type': {},
            '#': {'align': 'r'},
            'Description': {}
        }
        body = [{'ID': row.id, 'Type': row.type, '#': row.opts, 'Description': '"{}": {}'.format(row.name, row.desc)} for row in itm.fields]

        array += self._makeTable(table_headers, body)
        return array + '\n'

    def _formatArrayOf(self, itm, idx):
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :return: formatted arrayof
        """
        arrayOf = '###3.2.{idx} {name}\n'.format(idx=idx, name=self.formatStr(itm.name))
        arrayOf += f'{itm.desc}\n' if itm.desc != '' else ''

        field_opts = jadn_utils.topts_s2d(itm.opts)
        arrayOf += f"\n**{self.formatStr(itm.name)} (ArrayOf.{self.formatStr(field_opts.get('rtype', 'string'))} [\'{field_opts.get('max', '')}\', \'{field_opts.get('min', '')}\'])**\n"

        return arrayOf + '\n'

    # Helper Functions
    def _makeTable(self, headers={}, rows=[]):
        """
        Create a table using the given header and row values
        :param headers: table header names and attributes
        :param rows: row values
        :return: formatted MarkDown table
        """
        table_md = []

        # Headers
        header = []
        header_align = []
        for column, opts in headers.items():
            header.append(column)
            align = opts.get('align', 'left')
            header_align.append('---:' if align.startswith('r') else (':---:' if align.startswith('c') else ':---'))

        table_md.append(' | '.join(header))
        table_md.append(' | '.join(header_align))

        # Body
        for row in rows:
            tmp_row = []
            for column, opts in headers.items():
                column = column if column in row else self._table_field_headers.get(column, column)
                if isinstance(column, str):
                    cell = row.get(column, '')
                else:
                    cell = list(filter(None, [row.get(c, None) for c in column]))
                    cell = cell[0] if len(cell) == 1 else ''

                if type(cell) is list:
                    opts = jadn_utils.fopts_s2d(cell)
                    tmp_str = str(opts['min']) if 'min' in opts else '1'
                    tmp_str += ('..' + str('n' if opts['max'] == 0 else opts['max'])) if 'max' in opts else ('..1' if 'min' in opts else '')
                    # TODO: More options
                    tmp_row.append(tmp_str)
                else:
                    tmp_str = str(cell)
                    tmp_row.append(' ' if tmp_str == '' else tmp_str)

            table_md.append(' | '.join(tmp_row))

        return '\n'.join(table_md) + '\n'


def md_dumps(jadn):
    """
    Produce CDDL schema from JADN schema
    :arg jadn: JADN Schema to convert
    :return: MarkDown Table schema
    """
    return JADNtoMD(jadn).md_dump()


def md_dump(jadn, fname, source=""):
    """
    Produce MarkDown tables from the given JADN schema and write to file provided
    :param jadn: JADN Schema to convert
    :param fname: Name of file to write
    :param source: Name of the original JADN schema file
    :return: None
    """
    with open(fname, "w") as f:
        if source:
            f.write(f"<!-- Generated from {source}, {datetime.ctime(datetime.now())} -->\n")
        f.write(md_dumps(jadn))

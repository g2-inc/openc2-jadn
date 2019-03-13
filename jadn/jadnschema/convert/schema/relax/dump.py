import json
import re
import xml.dom.minidom as md

from datetime import datetime

from ..base_dump import JADNConverterBase
from .... import (
    enums,
    jadn_utils,
    utils
)


class JADNtoRelaxNG(JADNConverterBase):
    _fieldMap = {
        'Binary': 'base64Binary',
        'Boolean': 'boolean',
        'Integer': 'integer',
        'Number': 'float',
        'Null': '',
        'String': 'string'
    }

    def relax_dump(self, comm=enums.CommentLevels.ALL):
        """
        Converts the JADN schema to RelaxNG
        :param com: Level of comments to include in converted schema
        :return: RelaxNG schema
        """
        if comm:
            self.comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL

        records = [t.name for t in self._types if t.type == 'Record']  # self._meta.get('exports', [])
        # TODO: What should be here??
        exports = [self._formatTag('element', self._fieldType(r), name='message') for r in records]

        root_cont = list(
            self._formatTag(
                'start',
                self._formatTag('choice', exports)
            )
        )

        root_cont.extend(self.makeStructures())
        root_cont.append(self._formatComment('Custom Defined Types'))
        root_cont.extend(self.makeCustom())

        root = self._formatTag(
            'grammar',
            root_cont,
            datatypeLibrary="http://www.w3.org/2001/XMLSchema-datatypes",
            xmlns="http://relaxng.org/ns/structure/1.0"
        )

        doubleEmpty = re.compile('^$\n?^$', re.MULTILINE)
        return re.sub(doubleEmpty, '', f'{self.makeHeader()}{self._formatPretty(root)}\n')

    def makeHeader(self):
        """
        Create the header for the schema
        :return: header for schema
        """
        header_regex = re.compile(r'(^\"|\"$)')
        header = []
        for k in self._meta_order:
            if k in self._meta:
                header.append(f"<!-- meta: {k} - {header_regex.sub('', json.dumps(utils.default_decode(self._meta[k])))} -->")

        return '\n'.join(header) + '\n\n'

    def makeStructures(self):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        """
        defs = []
        for t in self._types:
            df = self._structFun(t.type, None)

            if df is not None:
                defs.append(df(t))

        return defs

    def makeCustom(self):
        defs = []
        for field in self._custom:
            com = '' if field.desc == '' else field.desc

            if len(field.opts) >= 1:
                opts = {'options': jadn_utils.topts_s2d(field.opts)}
                com += f' #jadn_opts:{json.dumps(opts)}'

            c = self._formatTag(
                'define',
                self._fieldType(field.type),
                name=self.formatStr(field.name),
                com=com
            )
            defs.append(c)

        return defs

    # Structure Formats
    def _formatRecord(self, itm):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        """
        properties = []
        for prop in itm.fields:
            opts = {'type': prop.type, 'field': prop.id}
            if len(prop.opts) > 0: opts['options'] = jadn_utils.fopts_s2d(prop.opts)

            ltmp = self._formatTag(
                'element',
                self._fieldType(prop.type),
                name=self.formatStr(prop.name),
                com=self._formatComment(prop.desc, jadn_opts=opts)
            )

            if self._is_optional(opts.get('options', {})):
                properties.append(self._formatTag('optional', ltmp))
            else:
                properties.append(ltmp)

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(prop.opts)

        return self._formatTag(
            'define',
            self._formatTag('interleave', properties),
            com=self._formatComment(itm.desc, jadn_opts=opts),
            name=self.formatStr(itm.name)
        )

    def _formatChoice(self, itm):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        """
        properties = []
        for prop in itm.fields:
            n = self.formatStr(prop.name or f'Unknown_{self.formatStr(itm.name)}_{prop.id}')
            opts = {'type': prop.type, 'field': prop.id}
            if len(prop.opts) > 0: opts['options'] = jadn_utils.fopts_s2d(prop.opts)

            properties.append(self._formatTag(
                'element',
                self._fieldType(prop.type),
                com=self._formatComment(prop.desc, jadn_opts=opts),
                name=n
            ))

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        return self._formatTag(
            'define',
            self._formatTag('choice', properties),
            com=self._formatComment(itm.desc, jadn_opts=opts),
            name=self.formatStr(itm.name)
        )

    def _formatMap(self, itm):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        """
        properties = []
        for prop in itm.fields:
            opts = {'type': prop.type, 'field': prop.id}
            if len(prop.opts) > 0: opts['options'] = jadn_utils.fopts_s2d(prop.opts)

            ltmp = self._formatTag(
                'element',
                self._fieldType(prop.type),
                name=self.formatStr(prop.name),
                com=self._formatComment(prop.desc, jadn_opts=opts)
            )

            if self._is_optional(opts.get('options', {})):
                properties.append(self._formatTag('optional', ltmp))
            else:
                properties.append(ltmp)

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        return self._formatTag(
            'define',
            self._formatTag('interleave', properties),
            com=self._formatComment(itm.desc, jadn_opts=opts),
            name=self.formatStr(itm.name)
        )

    def _formatEnumerated(self, itm):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        """
        properties = []
        for prop in itm.fields:
            opts = {'field': prop.id}
            properties.append(self._formatTag(
                'value',
                self.formatStr(prop.value or f'Unknown_{self.formatStr(itm.name)}_{prop.id}'),
                com=self._formatComment(prop.desc, jadn_opts=opts)
            ))

        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        return self._formatTag(
            'define',
            self._formatTag('choice', properties),
            com=self._formatComment(itm.desc, jadn_opts=opts),
            name=self.formatStr(itm.name)
        )

    def _formatArray(self, itm):  # TODO: what should this do??
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        """
        opts = {'type': itm.type}
        if len(itm.opts) > 0: opts['options'] = jadn_utils.topts_s2d(itm.opts)

        properties = []
        for prop in itm.fields:
            opts = {'type': prop.type, 'field': prop.id}
            if len(prop.opts) > 0: opts['options'] = jadn_utils.fopts_s2d(prop.opts)

            ltmp = self._formatTag(
                'element',
                self._fieldType(prop.type),
                name=self.formatStr(prop.name),
                com=self._formatComment(prop.desc, jadn_opts=opts)
            )

            if self._is_optional(opts.get('options', {})):
                properties.append(self._formatTag('optional', ltmp))
            else:
                properties.append(ltmp)

        return self._formatTag(
            'define',
            self._formatTag(
                'interleave',
                properties
            ),
            com=self._formatComment(itm.desc, jadn_opts=opts),
            name=self.formatStr(itm.name)
        )

    def _formatArrayOf(self, itm):  # TODO: what should this do??
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :return: formatted arrayof
        """
        field_opts = jadn_utils.topts_s2d(itm.opts)

        opts = {'type': itm.type}
        if len(field_opts.keys()) > 0: opts['options'] = field_opts

        return self._formatTag(
            'define',
            self._formatTag(
                'oneOrMore' if opts['options'] and len(opts['options']) > 0 else 'zeroOrMore',
                self._fieldType(field_opts.get('rtype', 'string'))
            ),
            com=self._formatComment(itm.desc, jadn_opts=opts),
            name=self.formatStr(itm.name)
        )

    # Helper Functions
    def _formatPretty(self, xml):
        """
        Format the XML in a human readable format
        :param xml: XML string to format
        :return: formatted XML
        """
        rtn_xml = '\n'.join([line for line in md.parseString(xml).toprettyxml(indent=self._indent).split('\n') if line.strip()])
        rtn_xml = re.sub(r'^<\?xml.*?\?>\n', '', rtn_xml)
        return rtn_xml

    def _formatTag(self, tag, contents='', com='', **kargs):
        """
        Format a tag using the given information
        :param tag: tag name
        :param contents: contents of the tag
        :param com: comment to add with the tag
        :param kargs: key/value attributes of the tag
        :return: formatted tag
        """
        ign = ['', None]
        attrs = ''.join([f' {k}={json.dumps(v)}' for k, v in kargs.items()])

        if contents in ign and com in ign:
            elm = f'<{tag}{attrs}/>'

        else:
            elm = f'<{tag}{attrs}>'
            if com != '' and re.match(r'^<!--.*?-->', com):
                elm += com
            elif com != '':
                elm += self._formatComment(com)

            if isinstance(contents, (str, int, float, complex)):
                elm += utils.toStr(contents)

            elif isinstance(contents, list):
                elm += ''.join(itm for itm in contents if type(itm) is str)

            elif isinstance(contents, dict):
                elm += ''.join(self._formatTag(k, v) for k, v in contents.items())

            else:
                print(f'unprepared type: {type(contents)}')

            elm += f'</{tag}>'

        return elm

    def _formatComment(self, msg, **kargs):
        """
        Format a comment for the given schema
        :param msg: comment text
        :param kargs: key/value comments
        :return: formatted comment
        """
        if self.comm == enums.CommentLevels.NONE:
            return ''

        if isinstance(msg, str):
            msg = re.sub(r'([\w\d])--([\w\d])', r'\1 - \2', msg)

        elm = '<!--'
        if msg not in ['', None, ' ']:
            elm += f' {msg}'

        for k, v in kargs.items():
            elm += f' #{k}:{json.dumps(v)}'

        elm += ' -->'

        return '' if re.match(r'^<!--\s+-->$', elm) else elm

    def _fieldType(self, f):
        """
        Determines the field type for the schema
        :param f: current type
        :return: type mapped to the schema
        """
        if f in self._customFields:
            rtn = self._formatTag('ref', name=self.formatStr(f))

        elif f in self._fieldMap.keys():
            rtn = self.formatStr(self._fieldMap.get(f, f))
            rtn = self._formatTag('text') if rtn == '' else self._formatTag('data', type=rtn)

        else:
            rtn = self._formatTag('text')

        return rtn


def relax_dumps(jadn, comm=enums.CommentLevels.ALL):
    """
    Produce CDDL schema from JADN schema
    :param jadn: JADN Schema to convert
    :param com: Level of comments to include in converted schema
    :return: Protobuf3 schema
    """
    comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL
    return JADNtoRelaxNG(jadn).relax_dump(comm)


def relax_dump(jadn, fname, source="", comm=enums.CommentLevels.ALL):
    """
    Produce RelaxNG scheema from JADN schema and write to file provided
    :param jadn: JADN Schema to convert
    :param fname: Name of file to write
    :param source: Name of the original JADN schema file
    :param comm: Level of comments to include in converted schema
    :return: None
    """
    comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL
    with open(fname, "w") as f:
        if source:
            f.write(f"<!-- Generated from {source}, {datetime.ctime(datetime.now())} -->\n")
        f.write(relax_dumps(jadn, comm))

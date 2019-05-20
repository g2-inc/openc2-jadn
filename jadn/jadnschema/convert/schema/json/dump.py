import json
import re

from datetime import datetime


from ..base_dump import JADNConverterBase
from .... import (
    enums,
    jadn_utils,
    utils
)


class JADNtoJSON(JADNConverterBase):
    _escape_chars = (' ',)

    _fieldMap = {
        'Binary': 'string',
        'Boolean': 'bool',
        'Integer': 'integer',
        'Number': 'number',
        'Null': 'null',
        'String': 'string'
    }

    _ignoreOpts = (
        'rtype'
    )

    _optKeys = {
        ('array',): {
            'min': 'minItems',
            'max': 'maxItems'
        },
        ('integer', 'number'): {
            'minc': 'minimum',
            'maxc': 'maximum',
            'format': 'format'
        },
        ('choice', 'map', 'object'): {
            'minv': 'minItems',
            'maxv': 'maxItems'
        },
        ('binary', 'enumerated', 'string'): {
            'format': 'format',
            'minc': 'minLength',
            'maxc': 'maxLength',
            'pattern': 'pattern'
        }
    }

    _validationMap = {
        'ipv4-addr': 'ipv4',  # ipv4
        'ipv6-addr': 'ipv6',  # ipv6
        'x': 'binary',
        'b': 'binary',
    }

    def json_dump(self, com=None):
        """
        Converts the JADN schema to JSON
        :param com: Level of comments to include in converted schema
        :return: JSON schema
        """
        if com:
            self.comm = com if com in enums.CommentLevels.values() else enums.CommentLevels.ALL
        exports = self._meta.get('exports', [])

        rtn = self.makeHeader()
        rtn.update(
            type='object',
            additionalProperties=False,
            oneOf=[self._fieldType(f) for f in exports],  # Exports??
            definitions=self.makeStructures()
        )
        rtn['definitions'].update(**self.makeCustom())

        return rtn

    def makeHeader(self):
        """
        Create the headers for the schema
        :return: header for schema
        """
        header = {}
        if 'title' in self._meta:
            header['title'] = self._meta['title']

        if 'description' in self._meta:
            header['description'] = self._meta['description']

        if 'module' in self._meta:
            header['id'] = ('' if self._meta['module'].startswith('http') else 'http://') + self._meta['module']

        return header

    def makeStructures(self):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        """
        tmp = dict()
        for struct in self._makeStructures(default={}):
            tmp.update(struct)
        return tmp

    def makeCustom(self):
        """
        Create the custom definitions for the schema
        :return: custom definitions for the schema
        """
        defs = {}
        for field in self._custom:
            field_opts = jadn_utils.topts_s2d(field.opts)

            def_field = self._fieldType(field.type)
            def_field.update(self._formatComment(field.desc))
            def_field.update(self._optReformat(field.type, field_opts, True))
            defs[self.formatStr(field.name)] = def_field

        return defs

    # Structure Formats
    def _formatRecord(self, itm):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        """
        itm_opts = jadn_utils.topts_s2d(itm['opts'])
        properties = {}
        required = []

        for prop in itm.fields:
            prop_opts = jadn_utils.fopts_s2d(prop.opts)

            if not self._is_optional(prop_opts):
                required.append(prop.name)

            tmp_def = self._fieldType(prop.type)

            field_type = tmp_def.get('type', '')
            field_type = tmp_def.get('$ref', '') if field_type == '' else field_type
            field_type = self._getType(field_type.split('/')[-1]) if field_type.startswith('#') else field_type
            tmp_def.update(self._optReformat(field_type, prop_opts))

            tmp_def.update(self._formatComment(prop.desc))
            properties[prop.name] = tmp_def

        type_def = dict(
            type="object",
            **self._optReformat('object', itm_opts, True),
            **self._formatComment(itm.desc),
            additionalProperties=False
        )
        if len(required) > 0:
            type_def['required'] = required

        type_def['properties'] = properties

        return {
            self.formatStr(itm.name): type_def
        }

    def _formatChoice(self, itm):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        """
        itm_opts = jadn_utils.topts_s2d(itm['opts'])
        properties = {}

        for prop in itm.fields:
            prop_opts = jadn_utils.fopts_s2d(prop.opts)
            tmp_def = self._fieldType(prop.type)

            field_type = tmp_def.get('type', '')
            field_type = tmp_def.get('$ref', '') if field_type == '' else field_type
            field_type = self._getType(field_type.split('/')[-1]) if field_type.startswith('#') else field_type
            tmp_def.update(self._optReformat(field_type, prop_opts))

            tmp_def.update(self._formatComment(prop.desc))
            properties[prop.name] = tmp_def

        type_def = dict(
            type='object',
            **self._optReformat('object', itm_opts, True),
            **self._formatComment(itm.desc),
            minProperties=1,
            maxProperties=1,
            additionalProperties=False,
            properties=properties,
            patternProperties={
                "^x-[A-Za-z0-9][A-Za-z0-9_]*:[A-Za-z0-9][A-Za-z0-9_]*$": {
                    "description": "Non-OASIS target extensions must start with x- and be separated by a colon",
                    "type": "object"
                }
            }
        )

        return {
            self.formatStr(itm.name): type_def
        }

    def _formatMap(self, itm):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        """
        itm_opts = jadn_utils.topts_s2d(itm['opts'])
        fields = []
        properties = {}
        required = []

        for prop in itm.fields:
            prop_opts = jadn_utils.fopts_s2d(prop.opts)
            fields.append(prop.name)

            if not self._is_optional(prop_opts):
                required.append(prop.name)

            if self._is_array(prop_opts):
                tmp_def = dict(
                    type='array',
                    items=[self._fieldType(prop.type)]
                )
            else:
                tmp_def = self._fieldType(prop.type)

            field_type = tmp_def.get('type', '')
            field_type = tmp_def.get('$ref', '') if field_type == '' else field_type
            field_type = self._getType(field_type.split('/')[-1]) if field_type.startswith('#') else field_type
            tmp_def.update(self._optReformat(field_type, prop_opts))

            tmp_def.update(self._formatComment(prop.desc))
            properties[prop.name] = tmp_def

        type_def = dict(
            type='object',
            **self._optReformat('object', itm_opts, True),
            **self._formatComment(itm.desc),
            additionalProperties=False,
            properties=properties,
            patternProperties={
                "^x-[A-Za-z0-9_]*$": {
                    "description": "Non-OASIS extensions must start with x-",
                    "type": "object"
                }
            }
        )

        if len(required) > 0:
            type_def['required'] = required

        return {
            self.formatStr(itm.name): type_def
        }

    def _formatEnumerated(self, itm):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        """
        itm_opts = jadn_utils.topts_s2d(itm['opts'])
        enum = []
        enum_type = 'string'
        options = []

        for prop in itm.fields:
            if 'compact' in itm_opts:
                enum_type = 'integer'
                val = prop.id
            else:
                val = prop.value

            enum.append(val)
            opt = dict(
                value=val,
                label=prop.value
            )
            if prop.desc != '':
                opt['description'] = prop.desc

            options.append(opt)

        type_def = dict(
            type=enum_type,
            **self._optReformat(enum_type, itm_opts, True),
            **self._formatComment(itm.desc),
            enum=enum
        )

        if self.comm != enums.CommentLevels.NONE:
            type_def['options'] = options

        return {
            self.formatStr(itm.name): type_def
        }

    def _formatArray(self, itm):
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        """
        itm_opts = jadn_utils.topts_s2d(itm['opts'])
        properties = {}
        required = []

        for prop in itm.fields:
            prop_opts = jadn_utils.fopts_s2d(prop.opts)

            if not self._is_optional(prop_opts):
                required.append(prop.name)

            if self._is_array(prop_opts):
                tmp_def = dict(
                    type='array',
                    items=[self._fieldType(prop.type)]
                )
            else:
                tmp_def = self._fieldType(prop.type)

            field_type = tmp_def.get('type', '')
            field_type = tmp_def.get('$ref', '') if field_type == '' else field_type
            field_type = self._getType(field_type.split('/')[-1]) if field_type.startswith('#') else field_type
            tmp_def.update(self._optReformat(field_type, prop_opts))

            tmp_def.update(self._formatComment(prop.desc))
            properties[prop.name] = tmp_def

        type_def = dict(
            type='array',
            **self._formatComment(itm.desc),
            **self._optReformat('array', itm_opts, True),
            items=dict(
                properties=properties
            )
        )

        if len(required) > 0:
            type_def['items']['required'] = required

        return {
            self.formatStr(itm.name): type_def
        }

    def _formatArrayOf(self, itm):
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :return: formatted arrayof
        """
        itm_opts = jadn_utils.topts_s2d(itm['opts'])
        rtype = itm_opts.get('rtype', 'String')

        type_def = dict(
            type='array',
            **self._optReformat('array', itm_opts, True),
            **self._formatComment(itm.desc),
            uniqueItems=True,
            items=[
                self._fieldType(rtype)
            ]
        )

        return {
            self.formatStr(itm.name): type_def
        }

    # Helper Functions
    def _getType(self, name):
        """
        Get the type of the field based of the name
        :param name: name of field to get the type of
        :return: type of the given field name
        """
        type_def = [d for d in self._types if d[0] == name] + [d for d in self._custom if d[0] == name]
        type_def = type_def[0] if len(type_def) == 1 else ['oops...', 'String']
        return type_def[1]

    def _optReformat(self, optType, opts, _type=False):
        """
        Reformat options for the given schema
        :param optType: type to reformat the options for
        :param opts: original options to reformat
        :param _type: is type of field
        :return: dict - reformatted options
        """
        _type = _type if isinstance(_type, bool) else False
        optType = optType.lower()
        optKeys = self._getOptKeys(optType)
        r_opts = {}

        def ignore(k, v):
            if k in ['object', 'array']:
                return False

            return any([
                k == 'minv' and utils.safe_cast(v, int, 1) < 1,
                k == 'maxv' and utils.safe_cast(v, int, 1) < 1,
            ])

        for key, val in opts.items():
            if _type:
                if key in optKeys:
                    val = self._validationMap.get(val, val) if key == 'format' else val
                    r_opts[optKeys[key]] = val
                continue

            if ignore(key, val) or key in self._ignoreOpts:
                continue

            if key in optKeys:
                val = self._validationMap.get(val, val) if key == 'format' else val
                r_opts[optKeys[key]] = val
            else:
                print(f'unknown option for type of {optType}: {key} - {val}')
        return r_opts

    def _fieldType(self, f):
        """
        Determines the field type for the schema
        :param f: current type
        :return: type mapped to the schema
        """
        if f in self._customFields:
            rtn = {
                '$ref': f'#/definitions/{self.formatStr(f)}'
            }

        elif f in self._fieldMap:
            rtn = dict(
                type=self.formatStr(self._fieldMap.get(f, f))
            )
            if f.lower() == 'binary':
                rtn['format'] = 'binary'

        else:
            print(f'unknown type: {f}')
            rtn = dict(
                type='string'
            )

        return rtn

    def _formatComment(self, msg, **kargs):
        """
        Format a comment for the given schema
        :param msg: comment text
        :param kargs: key/value comments
        :return: formatted comment
        """
        if self.comm == enums.CommentLevels.NONE:
            return {}

        com = ''
        if msg not in ['', None, ' ']:
            com += f'{msg}'

        for k, v in kargs.items():
            com += f' #{k}:{json.dumps(v)}'

        return {} if re.match(r'^\s*$', com) else dict(
            description=com
        )

    def _getOptKeys(self, _type):
        """
        Get the option keys for conversion
        :param _type: the type to get the keys of
        :return: dict - option keys for translation
        """
        for opts, conv in self._optKeys.items():
            if _type in opts:
                return conv

        return {}


def json_dumps(jadn, comm=enums.CommentLevels.ALL):
    """
    Produce JSON schema from JADN schema
    :param jadn: JADN Schema to convert
    :param comm: Level of comments to include in converted schema
    :return: JSON schema
    """
    comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL
    return JADNtoJSON(jadn).json_dump(comm)


def json_dump(jadn, fname, source="", comm=enums.CommentLevels.ALL):
    """
    Produce JSON schema from JADN schema and write to file provided
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
    comm = comm if comm in enums.CommentLevels.values() else enums.CommentLevels.ALL

    with open(fname, "w") as f:
        if source:
            f.write(f"; Generated from {source}, {datetime.ctime(datetime.now())}\n")
        f.write(json.dumps(json_dumps(jadn, comm), indent=4))

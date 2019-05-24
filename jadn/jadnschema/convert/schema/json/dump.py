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
        'ktype',
        'vtype'
    )

    _optKeys = {
        ('array',): {
            'minv': 'minItems',
            'maxv': 'maxItems'
        },
        ('integer', 'number'): {
            'minc': 'minimum',
            'maxc': 'maximum',
            'minv': 'minimum',
            'maxv': 'maximum',
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
            'minv': 'minLength',
            'maxv': 'maxLength',
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
            def_field = self._fieldType(field)
            def_field.update(self._formatComment(field.desc))
            def_field.update(self._optReformat(field.type, field.opts, True))
            defs[self.formatStr(field.name)] = def_field

        return defs

    # Structure Formats
    def _formatRecord(self, itm):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        """
        itm_opts = itm['opts']
        properties = {}
        required = []

        for prop in itm.fields:
            if not self._is_optional(prop.opts):
                required.append(prop.name)

            tmp_def = self._fieldType(prop)

            field_type = tmp_def.get('type', '')
            field_type = tmp_def.get('$ref', '') if field_type == '' else field_type
            field_type = self._getType(field_type.split('/')[-1]) if field_type.startswith('#') else field_type
            tmp_def.update(self._optReformat(field_type, prop.opts))

            tmp_def.update(self._formatComment(prop.desc))
            properties[prop.name] = tmp_def

        type_def = dict(
            type="object",
            **self._formatComment(itm.desc),
            **self._optReformat('object', itm_opts, True),
            additionalProperties=False,
            required=required,
            properties=properties
        )

        return {
            self.formatStr(itm.name): self._cleanEmpty(type_def)
        }

    def _formatChoice(self, itm):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        """
        properties = {}

        for prop in itm.fields:
            tmp_def = self._fieldType(prop)

            field_type = tmp_def.get('type', '')
            field_type = tmp_def.get('$ref', '') if field_type == '' else field_type
            field_type = self._getType(field_type.split('/')[-1]) if field_type.startswith('#') else field_type
            tmp_def.update(self._optReformat(field_type, prop.opts))

            tmp_def.update(self._formatComment(prop.desc))
            properties[prop.name] = tmp_def

        type_def = dict(
            type='object',
            **self._formatComment(itm.desc),
            **self._optReformat('object', itm.opts, True),
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
            self.formatStr(itm.name): self._cleanEmpty(type_def)
        }

    def _formatMap(self, itm):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        """
        fields = []
        properties = {}
        required = []

        for prop in itm.fields:
            fields.append(prop.name)

            if not self._is_optional(prop.opts):
                required.append(prop.name)

            if self._is_array(prop.opts):
                tmp_def = dict(
                    type='array',
                    items=[self._fieldType(prop)]
                )
            else:
                tmp_def = self._fieldType(prop)

            field_type = tmp_def.get('type', '')
            field_type = tmp_def.get('$ref', '') if field_type == '' else field_type
            field_type = self._getType(field_type.split('/')[-1]) if field_type.startswith('#') else field_type
            tmp_def.update(self._optReformat(field_type, prop.opts))

            tmp_def.update(self._formatComment(prop.desc))
            properties[prop.name] = tmp_def

        type_def = dict(
            type='object',
            **self._formatComment(itm.desc),
            **self._optReformat('object', itm.opts, True),
            additionalProperties=False,
            required=required,
            properties=properties,
            patternProperties={
                "^x-[A-Za-z0-9_]*$": {
                    "description": "Non-OASIS extensions must start with x-",
                    "type": "object"
                }
            }
        )

        return {
            self.formatStr(itm.name): self._cleanEmpty(type_def)
        }

    def _formatEnumerated(self, itm):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        """
        enum = []
        enum_type = 'string'
        options = []

        for prop in itm.fields:
            if 'id' in itm.opts:
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
            **self._formatComment(itm.desc),
            **self._optReformat(enum_type, itm.opts, True),
            enum=enum,
        )

        if self.comm != enums.CommentLevels.NONE:
            type_def.update(options=options)

        return {
            self.formatStr(itm.name): self._cleanEmpty(type_def)
        }

    def _formatArray(self, itm):
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        """
        properties = {}
        required = []

        for prop in itm.fields:
            if not self._is_optional(prop.opts):
                required.append(prop.name)

            if self._is_array(prop.opts):
                tmp_def = dict(
                    type='array',
                    items=[self._fieldType(prop)]
                )
            else:
                tmp_def = self._fieldType(prop)

            field_type = tmp_def.get('type', '')
            field_type = tmp_def.get('$ref', '') if field_type == '' else field_type
            field_type = self._getType(field_type.split('/')[-1]) if field_type.startswith('#') else field_type
            tmp_def.update(self._optReformat(field_type, prop.opts))

            tmp_def.update(self._formatComment(prop.desc))
            properties[prop.name] = tmp_def

        type_def = dict(
            type='array',
            **self._formatComment(itm.desc),
            **self._optReformat('array', itm.opts, True),
            required=required,
            items=dict(
                properties=properties
            )
        )

        return {
            self.formatStr(itm.name): self._cleanEmpty(type_def)
        }

    def _formatArrayOf(self, itm):
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :return: formatted arrayof
        """
        vtype = itm.opts.get('vtype', 'String')
        if vtype.startswith("$"):
            val_def = list(filter(lambda d: d.name == vtype[1:], self._types))
            val_def = val_def[0] if len(val_def) == 1 else {}
            id_val = val_def.opts.get('id', None)
            enum_val = 'id' if id_val else ('value' if val_def.type == 'Enumerated' else 'name')

            items = dict(
                type='integer' if id_val else 'string',
                enum=[f[enum_val] for f in val_def.fields]
            )
        else:
            items = self._fieldType(vtype)

        type_def = dict(
            type='array',
            **self._formatComment(itm.desc),
            **self._optReformat('array', itm.opts, True),
            uniqueItems=True,
            items=[
                items
            ]
        )

        return {
            self.formatStr(itm.name): self._cleanEmpty(type_def)
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
                k == 'minc' and utils.safe_cast(v, int, 1) < 1,
                k == 'maxc' and utils.safe_cast(v, int, 1) < 1,
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

    def _fieldType(self, field):
        """
        Determines the field type for the schema
        :param field: current type
        :return: type mapped to the schema
        """
        field_type = getattr(field, 'type', field)
        field_type = field_type if isinstance(field_type, str) else 'String'

        if isinstance(field, utils.FrozenDict):
            if field_type == "MapOf":
                # Key type
                key_type = field.opts.get('ktype', None)
                valid_keys = []
                key_def = list(filter(lambda d: d.name == key_type, self._types))
                for key_field in getattr(key_def[0] if len(key_def) == 1 else {}, 'fields', []):
                    valid_keys.append(getattr(key_field, 'value', key_field.name))

                key = f"^({'|'.join(valid_keys)})$" if key_type and key_type != "String" else "^[A-Za-z_][A-Za-z0-9_]*$"

                # Value Type
                value_type = field.opts.get('vtype', None)
                val_def = list(filter(lambda d: d.name == value_type, self._types))
                val_def = val_def[0] if len(val_def) == 1 else {}

                value = dict()
                if val_def and value_type != 'Any':
                    # print(f"Value Def: {val_def}")
                    value.update(dict(
                        type="array",
                        uniqueItems=True,
                        items=[
                            {
                                '$ref': f'#/definitions/{self.formatStr(val_def.name)}'
                            }
                        ]
                    ))

                return dict(
                    type='object',
                    additionalProperties=False,
                    patternProperties={
                        key: value
                    }
                )
            elif field_type == "ArrayOf":
                return self._formatArrayOf(field)

        if field_type in self._customFields:
            return {
                '$ref': f'#/definitions/{self.formatStr(field_type)}'
            }

        elif field_type in self._fieldMap:
            rtn = dict(
                type=self.formatStr(self._fieldMap.get(field_type, field_type))
            )
            rtn.update({'format': 'binary'} if field_type.lower() == 'binary' else {})
            return rtn

        else:
            print(f'unknown type: {field_type}')
            return dict(
                type='string'
            )

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

    def _cleanEmpty(self, itm):
        if isinstance(itm, dict):
            return dict((k, self._cleanEmpty(v)) for k, v in itm.items() if v or isinstance(v, bool))
        else:
            return itm


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

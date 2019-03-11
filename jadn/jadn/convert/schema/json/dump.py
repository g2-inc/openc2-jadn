import json
import re

from datetime import datetime

from jadn.jadn_utils import fopts_s2d, topts_s2d
from jadn.enums import CommentLevels
from jadn.utils import safe_cast, Utils


class JADNtoJSON(object):
    def __init__(self, jadn):
        """
        Schema Converter for JADN to JSON
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

        self._fieldMap = {
            'Binary': 'string',
            'Boolean': 'bool',
            'Integer': 'integer',
            'Number': 'number',
            'Null': 'null',
            'String': 'string'
        }

        self._validationMap = {
            'date-time': 'date-time',
            'email': 'email',
            'hostname': 'hostname',
            'ip-addr': 'ip-addr',  # ipv4/ipv6
            'json-pointer': 'json-pointer',  # Draft 6
            'uri': 'uri',
            'uri-reference': 'uri-reference',  # Draft 6
            'uri-template': 'uri-template',  # Draft 6
        }

        self._structFormats = {
            'Record': self._formatRecord,
            'Choice': self._formatChoice,
            'Map': self._formatMap,
            'Enumerated': self._formatEnumerated,
            'Array': self._formatArray,
            'ArrayOf': self._formatArrayOf,
        }

        self._keys = {
            # Structures
            'structure': ['name', 'type', 'opts', 'desc', 'fields'],
            # Definitions
            'def': ['id', 'name', 'type', 'opts', 'desc'],
            'enum_def': ['id', 'value', 'desc'],
        }

        self._optKeys = {
            ('array', ): {
                'min': 'minItems',
                'max': 'maxItems'
            },
            ('integer', 'number'): {
                'min': 'minimum',
                'max': 'maximum',
                'format': 'format'
            },
            ('choice', 'map', 'object'): {
                'min': 'minItems',
                'max': 'maxItems'
            },
            ('binary', 'enumerated', 'string'): {
                'format': 'format',
                'min': 'minLength',
                'max': 'maxLength',
                'pattern': 'pattern'
            }
        }
        self._ignoreOpts = [
            'rtype'
        ]

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

    def json_dump(self, comm=CommentLevels.ALL):
        """
        Converts the JADN schema to JSON
        :param comm: Level of comments to include in converted schema
        :type comm: str of enums.CommentLevel
        :return: JSON schema
        :rtype str
        """
        self.comments = comm if comm in CommentLevels.values() else CommentLevels.ALL
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

    def formatStr(self, s):
        """
        Formats the string for use in schema
        :param s: string to format
        :type s: str
        :return: formatted string
        :rtype str
        """
        return re.sub(r'[\s]', '_', s)

    def makeHeader(self):
        """
        Create the header for the schema
        :return: header for schema
        :rtype str
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
        :rtype str
        """
        tmp = dict()
        for t in self._types:
            df = self._structFormats.get(t[1], lambda d: dict())

            if df is not None:
                tmp.update(df(t))
        return tmp

    def makeCustom(self):
        defs = {}
        for field in self._custom:
            field = dict(zip(self._keys['structure'], field))
            field['opts'] = topts_s2d(field['opts'])

            def_field = self._fieldType(field['type'])
            def_field.update(self._formatComment(field['desc']))
            def_field.update(self._optReformat(field['type'], field['opts'], True))

            defs[self.formatStr(field['name'])] = def_field

        return defs

    def _fieldType(self, f):
        """
        Determines the field type for the schema
        :param f: current type
        :return: type mapped to the schema
        :rtype str
        """
        if f in self._customFields:
            return {
                '$ref': '#definitions/{}'.format(self.formatStr(f))
            }

        elif f in self._fieldMap:
            rtn = {
                'type': self.formatStr(self._fieldMap.get(f, f))
            }
            if f.lower() == 'binary':
                rtn['format'] = 'binary'
            return rtn

        else:
            print('unknown type: {}'.format(f))
            return {
                'type': 'string'
            }

    def _formatComment(self, msg, **kargs):
        if self.comments == CommentLevels.NONE:
            return {}

        com = ''
        if msg not in ['', None, ' ']:
            com += '{msg}'.format(msg=msg)

        for k, v in kargs.items():
            com += ' #{k}:{v}'.format(
                k=k,
                v=json.dumps(v)
            )

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

    # Structure Formats
    def _formatRecord(self, itm):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        :rtype str
        """
        item = dict(zip(self._keys['structure'], itm))
        item['opts'] = topts_s2d(item['opts'])
        properties = {}
        required = []

        for prop in item['fields']:
            prop = dict(zip(self._keys['def'], prop))
            prop['opts'] = fopts_s2d(prop['opts'])

            if not self._is_optional(prop['opts']):
                required.append(prop['name'])

            tmp_def = self._fieldType(prop['type'])

            field_type = tmp_def.get('type', '')
            field_type = tmp_def.get('$ref', '') if field_type == '' else field_type
            field_type = self._getType(field_type.split('/')[-1]) if field_type.startswith('#') else field_type
            tmp_def.update(self._optReformat(field_type, prop['opts']))

            tmp_def.update(self._formatComment(prop['desc']))
            properties[prop['name']] = tmp_def

        type_def = dict(
            type="object",
            **self._optReformat('object', item['opts'], True),
            **self._formatComment(item['desc']),
            additionalProperties=False
        )
        if len(required) > 0:
            type_def['required'] = required

        type_def['properties'] = properties

        return {
            self.formatStr(item['name']): type_def
        }

    def _formatChoice(self, itm):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        :rtype str
        """
        item = dict(zip(self._keys['structure'], itm))
        item['opts'] = topts_s2d(item['opts'])
        fields = []
        properties = {}

        for prop in item['fields']:
            prop = dict(zip(self._keys['def'], prop))
            prop['opts'] = fopts_s2d(prop['opts'])
            fields.append(prop['name'])

            tmp_def = self._fieldType(prop['type'])

            field_type = tmp_def.get('type', '')
            field_type = tmp_def.get('$ref', '') if field_type == '' else field_type
            field_type = self._getType(field_type.split('/')[-1]) if field_type.startswith('#') else field_type
            tmp_def.update(self._optReformat(field_type, prop['opts']))

            tmp_def.update(self._formatComment(prop['desc']))
            properties[prop['name']] = tmp_def

        type_def = dict(
            type='object',
            **self._optReformat('object', item['opts'], True),
            **self._formatComment(item['desc']),
            additionalProperties=False,
            patternProperties={"^({})$".format('|'.join(fields)): {}},
            oneOf=[
                dict(properties=properties)
            ]
        )

        return {
            self.formatStr(item['name']): type_def
        }

    def _formatMap(self, itm):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        :rtype str
        """
        item = dict(zip(self._keys['structure'], itm))
        item['opts'] = topts_s2d(item['opts'])
        fields = []
        properties = {}
        required = []

        for prop in item['fields']:
            prop = dict(zip(self._keys['def'], prop))
            prop['opts'] = fopts_s2d(prop['opts'])
            fields.append(prop['name'])

            if not self._is_optional(prop['opts']):
                required.append(prop['name'])

            if self._is_array(prop['opts']):
                tmp_def = dict(
                    type='array',
                    items=[self._fieldType(prop['type'])]
                )
            else:
                tmp_def = self._fieldType(prop['type'])

            field_type = tmp_def.get('type', '')
            field_type = tmp_def.get('$ref', '') if field_type == '' else field_type
            field_type = self._getType(field_type.split('/')[-1]) if field_type.startswith('#') else field_type
            tmp_def.update(self._optReformat(field_type, prop['opts']))

            tmp_def.update(self._formatComment(prop['desc']))
            properties[prop['name']] = tmp_def

        type_def = dict(
            type='object',
            **self._optReformat('object', item['opts'], True),
            **self._formatComment(item['desc']),
            additionalProperties=False,
            patternProperties={"^({})$".format('|'.join(fields)): {}},
        )

        if len(required) > 0:
            type_def['required'] = required

        type_def['anyOf'] = [
            dict(
                properties=properties
            )
        ]

        return {
            self.formatStr(item['name']): type_def
        }

    def _formatEnumerated(self, itm):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        :rtype str
        """
        item = dict(zip(self._keys['structure'], itm))
        item['opts'] = topts_s2d(item['opts'])
        enum = []
        enum_type = 'string'
        options = []

        for prop in item['fields']:
            prop = dict(zip(self._keys['enum_def'], prop))
            if 'compact' in item['opts']:
                enum_type = 'integer'
                val = prop['id']
            else:
                val = prop['value']

            enum.append(val)
            opt = dict(
                value=val,
                label=prop['value']
            )
            if prop['desc'] != '':
                opt['description'] = prop['desc']

            options.append(opt)

        type_def = dict(
            type=enum_type,
            **self._optReformat(enum_type, item['opts'], True),
            **self._formatComment(item['desc']),
            enum=enum
        )

        if self.comments != CommentLevels.NONE:
            type_def['options'] = options

        return {
            self.formatStr(item['name']): type_def
        }

    def _formatArray(self, itm):
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        :rtype str
        """
        item = dict(zip(self._keys['structure'], itm))
        item['opts'] = topts_s2d(item['opts'])
        properties = {}
        required = []

        for prop in item['fields']:
            prop = dict(zip(self._keys['def'], prop))
            prop['opts'] = fopts_s2d(prop['opts'])

            if not self._is_optional(prop['opts']):
                required.append(prop['name'])

            if self._is_array(prop['opts']):
                tmp_def = dict(
                    type='array',
                    items=[self._fieldType(prop['type'])]
                )
            else:
                tmp_def = self._fieldType(prop['type'])

            field_type = tmp_def.get('type', '')
            field_type = tmp_def.get('$ref', '') if field_type == '' else field_type
            field_type = self._getType(field_type.split('/')[-1]) if field_type.startswith('#') else field_type
            tmp_def.update(self._optReformat(field_type, prop['opts']))

            tmp_def.update(self._formatComment(prop['desc']))
            properties[prop['name']] = tmp_def

        type_def = dict(
            type='array',
            **self._formatComment(item['desc']),
            **self._optReformat('array', item['opts'], True),
            items=dict(
                properties=properties
            )
        )

        if len(required) > 0:
            type_def['items']['required'] = required

        return {
            self.formatStr(itm[0]): type_def
        }

    def _formatArrayOf(self, itm):
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :return: formatted arrayof
        :rtype str
        """
        item = dict(zip(self._keys['structure'], itm))
        item['opts'] = topts_s2d(item['opts'])
        rtype = item['opts'].get('rtype', 'String')

        type_def = dict(
            type='array',
            **self._optReformat('array', item['opts'], True),
            **self._formatComment(item['desc']),
            items=[
                self._fieldType(rtype)
            ]
        )

        return {
            self.formatStr(item['name']): type_def
        }

    # Helper Functions
    def _is_optional(self, opts):
        """
        Check if the field is optional
        :param opts: field options
        :return: bool - optional
        """
        min_size = opts.get('min', 1)
        return min_size == 0

    def _is_array(self, opts):
        """
        Check if the field is an array
        :param opts: field options
        :return: bool - optional
        """
        max_size = opts.get('max', 1)
        return max_size != 1

    def _getType(self, name):
        """
        Get the type of the field based of the name
        :param name:
        :return:
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
        _type = _type if type(_type) is bool else False
        optType = optType.lower()
        optKeys = self._getOptKeys(optType)
        r_opts = {}

        def ignore(k, v):
            if k in ['object', 'array']:
                return False

            ign = any([
                k == 'min' and safe_cast(v, int, 1) < 1,
                k == 'max' and safe_cast(v, int, 1) < 1,
            ])
            return ign

        for key, val in opts.items():
            if _type:
                if key in optKeys:
                    r_opts[optKeys[key]] = val
            elif not ignore(key, val):
                if key in self._ignoreOpts:
                    pass
                elif key in optKeys:
                    r_opts[optKeys[key]] = val
                else:
                    print(f'unknown option for type of {optType}: {key} - {val}')

        return r_opts


def json_dumps(jadn, comm=CommentLevels.ALL):
    """
    Produce JSON schema from JADN schema
    :param jadn: JADN Schema to convert
    :type jadn: str or dict
    :param comm: Level of comments to include in converted schema
    :type comm: str of enums.CommentLevel
    :return: JSON schema
    :rtype dict
    """
    comm = comm if comm in CommentLevels.values() else CommentLevels.ALL
    return JADNtoJSON(jadn).json_dump(comm)


def json_dump(jadn, fname, source="", comm=CommentLevels.ALL):
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
    comm = comm if comm in CommentLevels.values() else CommentLevels.ALL

    with open(fname, "w") as f:
        if source:
            f.write("; Generated from {}, {}\n".format(source, datetime.ctime(datetime.now())))
        f.write(json.dumps(json_dumps(jadn, comm), indent=4))

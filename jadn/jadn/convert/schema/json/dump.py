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

        self. _optKeys = {
            'array': {
                'min': 'minItems',
                'max': 'maxItems'
            },
            'integer': {
                'min': 'minimum',
                'max': 'maximum',
                'format': 'format'
            },
            'object': {
                'min': 'minItems',
                'max': 'maxItems'
            },
            'string': {
                'format': 'format',
                'min': 'minLength',
                'max': 'maxLength',
                'pattern': 'pattern'
            }
        }
        self._optKeys.update(
            binary=self. _optKeys['string'],
            choice=self._optKeys['object'],
            enumerated=self._optKeys['string'],
            map=self._optKeys['object'],
        )
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
        '''
        patternProperties={
            f"^({'|'.join(exports)})$": dict()
        },
        '''
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
            header['id'] = ('' if self._meta['module'].startswith('http') else 'http://') +  self._meta['module']

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
            def_field.update(self._optReformat(field['type'], field['opts']))

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
            rtn = {
                '$ref': '#definitions/{}'.format(self.formatStr(f))
            }

        elif f in self._fieldMap.keys():
            rtn = {
                'type': self.formatStr(self._fieldMap.get(f, f))
            }
            if f.lower() == 'binary':
                rtn['format'] = 'binary'

        else:
            print('unknown type: {}'.format(f))
            rtn = {
                'type': 'string'
            }

        print(rtn)
        return rtn

    def _formatComment(self, msg, **kargs):
        if self.comments == CommentLevels.NONE:
            return {}

        com = ''
        if msg not in ['', None, ' ']:
            com += ' {msg}'.format(msg=msg)

        for k, v in kargs.items():
            com += ' #{k}:{v}'.format(
                k=k,
                v=json.dumps(v)
            )

        return {} if re.match(r'^\s*$', com) else dict(
            description=com
        )

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

            if 'min' in prop['opts']:
                optional = prop['opts'].get('min', -1) == 0 and prop['opts'].get('max', -1) in [-1, 0]
                if not optional:
                    required.append(prop['name'])
            else:
                required.append(prop['name'])

            properties[prop['name']] = self._fieldType(prop['type'])

            field_type = properties[prop['name']].get('type', '')
            field_type = properties[prop['name']].get('$ref', '') if field_type == '' else field_type
            field_type = self._getType(field_type.split('/')[-1]) if field_type.startswith('#') else field_type
            properties[prop['name']].update(self._optReformat(field_type, prop['opts']))

            properties[prop['name']].update(self._formatComment(prop['desc']))

        type_def = dict(
            type="object",
            properties=properties,
            additionalProperties=False
        )
        type_def.update(self._optReformat('object', item['opts']))
        type_def.update(self._formatComment(item['desc']))

        if len(required) > 0:
            type_def['required'] = required

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

            properties[prop['name']] = self._fieldType(prop['type'])

            field_type = properties[prop['name']].get('type', '')
            field_type = properties[prop['name']].get('$ref', '') if field_type == '' else field_type
            field_type = self._getType(field_type.split('/')[-1]) if field_type.startswith('#') else field_type
            properties[prop['name']].update(self._optReformat(field_type, prop['opts']))

            properties[prop['name']].update(self._formatComment(prop['desc']))

        type_def = dict(
            type='object',
            additionalProperties=False,
            patternProperties={"^({})$".format('|'.join(fields)): {}},
            oneOf=[
                dict(properties=properties)
            ]
        )
        type_def.update(self._optReformat('object', item['opts']))
        type_def.update(self._formatComment(item['desc']))

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

        for prop in item['fields']:
            prop = dict(zip(self._keys['def'], prop))
            prop['opts'] = fopts_s2d(prop['opts'])
            fields.append(prop['name'])

            properties[prop['name']] = self._fieldType(prop['type'])

            field_type = properties[prop['name']].get('type', '')
            field_type = properties[prop['name']].get('$ref', '') if field_type == '' else field_type
            field_type = self._getType(field_type.split('/')[-1]) if field_type.startswith('#') else field_type
            properties[prop['name']].update(self._optReformat(field_type, prop['opts']))

            properties[prop['name']].update(self._formatComment(prop['desc']))

        type_def = dict(
            type='object',
            additionalProperties=False,
            patternProperties={"^({})$".format('|'.join(fields)): {}},
            anyOf=[
                dict(properties=properties)
            ]
        )
        type_def.update(self._optReformat('object', item['opts']))
        type_def.update(self._formatComment(item['desc']))

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
        values = []
        options = []

        for prop in item['fields']:
            prop = dict(zip(self._keys['enum_def'], prop))
            values.append(prop['value'])
            opt = dict(
                value=prop['value'],
                label=prop['value']
            )
            if prop['desc'] != '':
                opt['description'] = prop['desc']

            options.append(opt)

        type_def = dict(
            type='string',
            enum=values
        )

        if self.comments != CommentLevels.NONE:
            type_def['options'] = options

        type_def.update(self._optReformat('string', item['opts']))
        type_def.update(self._formatComment(item['desc']))

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

            if 'min' in prop['opts']:
                optional = prop['opts'].get('min', -1) == 0 and prop['opts'].get('max', -1) in [-1, 0]
                if not optional:
                    required.append(prop['name'])
            else:
                required.append(prop['name'])

            properties[prop['name']] = self._fieldType(prop['type'])

            field_type = properties[prop['name']].get('type', '')
            field_type = properties[prop['name']].get('$ref', '') if field_type == '' else field_type
            field_type = self._getType(field_type.split('/')[-1]) if field_type.startswith('#') else field_type
            properties[prop['name']].update(self._optReformat(field_type, prop['opts']))

            properties[prop['name']].update(self._formatComment(prop['desc']))

        type_def = dict(
            type='array',
            items=dict(
                properties=properties
            )
        )

        if len(required) > 0:
            type_def['items']['required'] = required

        type_def.update(self._formatComment(item['desc']))
        type_def.update(self._optReformat('array', item['opts']))

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
            items=[
                self._fieldType(rtype)
            ]
        )

        type_def.update(self._formatComment(item['desc']))
        type_def.update(self._optReformat('array', item['opts']))

        return {
            self.formatStr(item['name']): type_def
        }

    # Helper Functions
    def _getType(self, name):
        """
        Get the type of the field based of the name
        :param name:
        :return:
        """
        type_def = [d for d in self._types if d[0] == name] + [d for d in self._custom if d[0] == name]
        type_def = type_def[0] if len(type_def) == 1 else ['oops...', 'String']
        return type_def[1]

    def _optReformat(self, optType, opts):
        """
        Reformat options for the given schema
        :param opts:
        :return:
        """
        optType = optType.lower()
        r_opts = {}

        optKeys = self._optKeys.get(optType, {})
        for k, v in opts.items():
            if k in optKeys:
                r_opts[self._optKeys[optType][k]] = v
            elif k in self._ignoreOpts:
                # print(f'option ignored: {k}')
                pass
            else:
                print(f'unknown option for type {optType}: {k} - {v}')

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

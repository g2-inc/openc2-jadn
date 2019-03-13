from __future__ import unicode_literals, print_function

import json
import re

from datetime import datetime

from .... import (
    jadn_utils,
    utils
)


class JSONtoJADN(object):
    def __init__(self, jsn):
        """
        Schema Converter for JADN to JSON
        :param jadn: str or dict of the JADN schema
        :type jadn: str or dict
        """
        if type(jsn) in [str, bytes]:
            try:
                self._schema = json.loads(jsn)
            except Exception as e:
                raise e
        elif type(jsn) is dict:
            self._schema = jsn

        else:
            raise TypeError('JSON improperly formatted')

        self._fieldMap = {
            'binary': 'Binary',
            'integer': 'Integer',
            'null': 'Null',
            'number': 'Number',
            'string': 'String',
        }

        self._optKeys = {
            ('array', ): {
                'minItems': 'min',
                'maxItems': 'max'
            },
            ('integer', ): {
                'minimum': 'min',
                'exclusiveMinimum': 'min',
                'maximum': 'max',
                'exclusiveMaximum': 'max',
                'format': 'format'
            },
            ('object', ): {},
            ('string', ): {
                'format': 'format',
                'minLength': 'min',
                'maxLength': 'max',
                'pattern': 'pattern'
            }
        }

        self._binaryFormats = [
            'binary',
            'ip-addr'
        ]

    def jadn_dump(self):
        return dict(
            meta=self.makeHeader(),
            types=self.makeStructures()
        )

    def makeHeader(self):
        """
        Create the header for the schema
        :return: header for schema
        :rtype dict
        """
        module = self._schema['id'] if 'id' in self._schema else (self._schema['$id'] if '$id' in self._schema else '')
        module = re.sub(r'^https?:\/\/', '', module)
        return dict(
                module=module,
                title=self._schema.get('title', ''),
                description=self._schema.get('description', ''),
                imports=[
                    # ["jadn", "oasis-open.org/openc2/jadn/v1.0"]
                ],
                exports=[e.get('$ref', '').split('/')[-1] for e in self._schema.get('oneOf', {})]
            )

    def makeStructures(self):
        """
        Create the type definitions for the schema
        :return: type definitions for the schema
        :rtype str
        """
        tmp_types = []
        # TODO: process definitions
        for key, val in self._schema.get('definitions', {}).items():
            print(key)
            def_type = val.get('type', '')
            if def_type == 'object':
                print('-- Structure')
                if 'patternProperties' not in val:
                    print('---- Record')
                    tmp_types.append(self._formatRecord(key, val))
                elif 'oneOf' in val:
                    print('---- Choice')
                    tmp_types.append(self._formatChoice(key, val))
                elif 'anyOf' in val:
                    print('---- Map')
                    tmp_types.append(self._formatMap(key, val))
                else:
                    print('---- Unknown')

            elif def_type == 'array':
                print('-- Structure')
                if len(val['items']) == 1:
                    print('---- ArrayOf')
                    tmp_types.append(self._formatArrayOf(key, val))
                else:
                    print('---- Array')
                    tmp_types.append(self._formatArray(key, val))

            elif def_type in ['string', 'integer'] and 'enum' in val:
                print('-- Structure\n---- Enumerated')
                tmp_types.append(self._formatEnumerated(key, val))

            else:
                print('-- Custom Type')
                tmp_types.append(self._formatCustom(key, val))
            print('')

        return tmp_types

    def _fieldType(self, v):
        """
        Determines the field type for the schema
        :param f: current type
        :return: type mapped to the schema
        :rtype str
        """
        t, d = self._getRef(v['$ref']) if '$ref' in v else (v['type'], {})

        if v.get('type', '') == 'string' and v.get('format', '') in self._binaryFormats:
            return 'Binary'
        elif v.get('type', '') == 'array':
            itm = v.get('items', [{'type': 'string'}])[0]
            if '$ref' in itm:
                return itm['$ref'].split('/')[-1]
            else:
                return self._fieldMap.get(itm['type'], t)
        else:
            return self._fieldMap.get(t, t)

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
    def _formatRecord(self, name, itm):
        """
        Formats records for the given schema type
        :param itm: record to format
        :return: formatted record
        :rtype list
        """
        tmp_def = dict(
            name=name,
            type='Record',
            opts={},
            desc=itm.get('description', '').strip(),
            fields=[]
        )

        i = 1
        for k, v in itm.get('properties', {}).items():
            field = dict(
                id=i,
                name=k,
                type=self._fieldType(v),
                opts={},
                desc=v.get('description', '').strip(),
            )
            if k not in itm.get('required', []):
                field['opts']['min'] = 0

            field['opts'] = jadn_utils.fopts_d2s(field['opts'])
            tmp_def['fields'].append(field)
            i += 1

        tmp_def['opts'] = jadn_utils.topts_d2s(tmp_def['opts'])
        tmp_def['fields'] = [list(field.values()) for field in tmp_def['fields']]
        return list(tmp_def.values())

    def _formatChoice(self, name, itm):
        """
        Formats choice for the given schema type
        :param itm: choice to format
        :return: formatted choice
        :rtype list
        """
        tmp_def = dict(
            name=name,
            type='Choice',
            opts={},
            desc=itm.get('description', '').strip(),
            fields=[]
        )

        i = 1
        for option in itm.get('oneOf', {}):
            for k, v in option.get('properties', {}).items():
                field = dict(
                    id=i,
                    name=k,
                    type=self._fieldType(v),
                    opts={},
                    desc=v.get('description', '').strip(),
                )

                field['opts'] = jadn_utils.fopts_d2s(field['opts'])
                tmp_def['fields'].append(field)
                i += 1

        tmp_def['opts'] = jadn_utils.topts_d2s(tmp_def['opts'])
        tmp_def['fields'] = [list(field.values()) for field in tmp_def['fields']]
        return list(tmp_def.values())

    def _formatMap(self, name, itm):
        """
        Formats map for the given schema type
        :param itm: map to format
        :return: formatted map
        :rtype list
        """
        tmp_def = dict(
            name=name,
            type='Map',
            opts={},
            desc=itm.get('description', '').strip(),
            fields=[]
        )

        i = 1
        for option in itm.get('anyOf', {}):
            for k, v in option.get('properties', {}).items():
                field = dict(
                    id=i,
                    name=k,
                    type=self._fieldType(v),
                    opts={},
                    desc=v.get('description', '').strip(),
                )

                if k not in itm.get('required', []):
                    field['opts']['min'] = 0

                field['opts'] = jadn_utils.fopts_d2s(field['opts'])
                tmp_def['fields'].append(field)
                i += 1

        tmp_def['opts'] = jadn_utils.topts_d2s(tmp_def['opts'])
        tmp_def['fields'] = [list(field.values()) for field in tmp_def['fields']]
        return list(tmp_def.values())

    def _formatEnumerated(self, name, itm):
        """
        Formats enum for the given schema type
        :param itm: enum to format
        :return: formatted enum
        :rtype list
        """
        tmp_def = dict(
            name=name,
            type='Enumerated',
            opts={},
            desc=itm.get('description', '').strip(),
            fields=[]
        )

        i = 1
        if 'options' in itm:
            if str(itm['options'][0]['value']).isdigit(): tmp_def['opts']['compact'] = True
            for field in itm['options']:
                tmp_def['fields'].append([utils.safe_cast(field['value'], int, i), field['label'], field['description']])
                i += 1
        else:
            for field in itm['enum']:
                tmp_def['fields'].append([i, field, ''])
                i += 1

        tmp_def['opts'] = jadn_utils.topts_d2s(tmp_def['opts'])
        return list(tmp_def.values())

    def _formatArray(self, name, itm):  # TODO: what should this do??
        """
        Formats array for the given schema type
        :param itm: array to format
        :return: formatted array
        :rtype list
        """
        tmp_def = dict(
            name=name,
            type='Array',
            opts=self._optReformat('array', itm),
            desc=itm.get('description', '').strip(),
            fields=[]
        )

        i = 1
        for k, v in itm.get('items', {}).get('properties', {}).items():
            field_type = self._fieldType(v)
            field = dict(
                id=i,
                name=k,
                type=field_type,
                opts=self._optReformat(field_type, v),
                desc=v.get('description', '').strip(),
            )
            if k not in itm.get('items', {}).get('required', []):
                field['opts']['min'] = 0

            field['opts'] = jadn_utils.fopts_d2s(field['opts'])
            tmp_def['fields'].append(field)
            i += 1

        tmp_def['opts'] = jadn_utils.topts_d2s(tmp_def['opts'])
        tmp_def['fields'] = [list(field.values()) for field in tmp_def['fields']]
        return list(tmp_def.values())

    def _formatArrayOf(self, name, itm):  # TODO: what should this do??
        """
        Formats arrayof for the given schema type
        :param itm: arrayof to format
        :return: formatted arrayof
        :rtype list
        """
        rtype = itm.get('items', [])[0]

        tmp_def = dict(
            name=name,
            type='ArrayOf',
            opts=dict(
                rtype=rtype['$ref'].split('/')[-1] if '$ref' in rtype else self._fieldType(rtype)
            ),
            desc=itm.get('description', '').strip()
        )
        tmp_def['opts'].update(self._optReformat('array', itm, True))

        tmp_def['opts'] = jadn_utils.topts_d2s(tmp_def['opts'])
        return list(tmp_def.values())

    def _formatCustom(self, name, itm):
        """
        Formats custom type for the given schema type
        :param itm: custom type to format
        :return: formatted custom type
        :rtype list
        """
        def_type = self._fieldType(itm)

        tmp_def = dict(
            name=name,
            type=def_type,
            opts=self._optReformat(def_type, itm),
            desc=itm.get('description', '').strip()
        )
        if 'format' in itm and itm['format'] != 'binary':
            tmp_def['opts']['format'] = itm['format']

        tmp_def['opts'] = jadn_utils.topts_d2s(tmp_def['opts'])
        return list(tmp_def.values())

    # Helper Functions
    def _getRef(self, ref):
        """
        get JSON Schema referenced definition
        :param ref: reference
        :return: referenced object
        """
        ref = ref.split('/')
        if ref[0].startswith('#'):
            ref[0] = ref[0][1:]
            tmp_ref = dict(self._schema)

            for k in ref:
                tmp_ref = tmp_ref.get(k, {})

            return ref[-1], tmp_ref
        else:
            return ref[-1], {}

    def _optReformat(self, optType, opts, _type=False):
        """
        Reformat options for the given schema
        :param optType: type to reformat the options for
        :param opts: original options to reformat
        :param _type: is type of field
        :return: dict - reformatted options
        """
        ignoreKeys = ['description', 'items', 'type', '$ref']
        optType = optType.lower()
        r_opts = {}

        optKeys = self._getOptKeys(optType)
        for k, v in opts.items():
            if k not in ignoreKeys:
                if k in optKeys:
                    r_opts[optKeys[k]] = v

        return r_opts


def json_loads(json):
    """
    Produce JADN schema from JSON schema
    :param json: JSON schema to convert
    :return: JADN schema
    :rtype str
    """
    return utils.jadn_format(JSONtoJADN(json).jadn_dump())


def json_load(jsn, fname, source=""):
    with open(fname, "w") as f:
        if source:
            f.write("-- Generated from {}, {}\n".format(source, datetime.ctime(datetime.now())))
        f.write(json_loads(jsn))

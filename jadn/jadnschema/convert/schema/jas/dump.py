"""
Translate JADN to JAS (JADN Abstract Syntax)
"""
from copy import deepcopy
from datetime import datetime
from textwrap import fill

from .... import (
    jadn_defs,
    jadn_utils
)

stype_map = {                       # Map JADN built-in types to JAS type names (Equivalent ASN.1 types in comments)
    'Binary': 'BINARY',             # OCTET STRING
    'Boolean': 'BOOLEAN',           # BOOLEAN
    'Integer': 'INTEGER',           # INTEGER
    'Number': 'REAL',               # REAL
    'Null': 'NULL',                 # NULL
    'String': 'STRING',             # UTF8String
    'Array': 'ARRAY',               # SEQUENCE
    'ArrayOf': 'ARRAY_OF',          # SEQUENCE OF
    'Choice': 'CHOICE',             # CHOICE
    'Enumerated': 'ENUMERATED',     # ENUMERATED
    'Map': 'MAP',                   # SET
    'MapOf': 'MAP_OF',              #
    'Record': 'RECORD'              # SEQUENCE
}


def stype(jtype: str) -> bool:
    return stype_map[jtype] if jtype in stype_map else jtype


def jas_dumps(jadn):
    """
    Produce JAS module from JADN structure

    JAS represents features available in both JADN and ASN.1 using ASN.1 syntax, but adds
    extended datatypes (Record, Map) for JADN types not directly representable in ASN.1.
    With appropriate encoding rules (which do not yet exist), SEQUENCE could replace Record.
    Map could be implemented using ASN.1 table constraints, but for the purpose of representing
    JSON objects, the Map first-class type in JAS is easier to use.
    """

    jas = '/*\n'
    hdrs = jadn['meta']
    hdr_list = ['module', 'patch', 'title', 'description', 'imports', 'exports', 'bounds']
    for h in hdr_list + list(set(hdrs) - set(hdr_list)):
        if h in hdrs:
            if h == 'description':
                jas += fill(hdrs[h], width=80, initial_indent='{0:14} '.format(h+':'), subsequent_indent=15*' ') + '\n'
            elif h == 'imports':
                hh = '{:14} '.format(h+':')
                for imp in hdrs[h]:
                    jas += hh + '{}: {}\n'.format(*imp)
                    hh = 15*' '
            elif h == 'exports':
                jas += '{:14} {}\n'.format(h+':', ', '.join(hdrs[h]))
            else:
                jas += '{:14} {}\n'.format(h+':', hdrs[h])
    jas += '*/\n'

    if set(stype_map) != set(jadn_defs.JADN_TYPES.PRIMITIVES + jadn_defs.JADN_TYPES.STRUCTURES):  # Ensure type list is up to date
        raise TypeError(f"JADN Type list not valid, expected {len(stype_map)} got {len(jadn_defs.JADN_TYPES.PRIMITIVES + jadn_defs.JADN_TYPES.STRUCTURES)}")

    tolist = {'id', 'vtype', 'ktype', 'enum', 'format', 'pattern', 'minv', 'maxv', 'default'}
    if set(jadn_defs.TYPE_CONFIG.OPTIONS.values()) != tolist:  # Ensure type options list is up to date
        raise TypeError("JADN type options are not up to date")

    folist = {'minc', 'maxc', 'tfield', 'flatten', 'ktype', 'vtype', 'format', 'enum'}
    if set(jadn_defs.FIELD_CONFIG.OPTIONS.values()) != folist:  # Ensure field options list is up to date
        raise TypeError("JADN field options are not up to date")

    for td in jadn['types']:                    # 0:type name, 1:base type, 2:type opts, 3:type desc, 4:fields
        tname = td[jadn_defs.TypeName]
        ttype = jadn_utils.basetype(td[jadn_defs.BaseType])
        topts = jadn_utils.topts_s2d(td[jadn_defs.TypeOptions])
        tostr = ''
        if 'minv' in topts or 'maxv' in topts:
            lo = topts['minv'] if 'minv' in topts else 0
            hi = topts['maxv'] if 'maxv' in topts else 0
            range = ''
            if lo or hi:
                range = f"({lo}..{hi if hi else 'MAX'})"

        for opt in tolist:
            if opt in topts:
                ov = topts[opt]
                if opt == 'id':
                    tostr += '.ID'

                elif opt == 'vtype':
                    tostr += f"({ov})"

                elif opt == 'ktype':
                    pass  # fix MapOf(ktype, vtype)

                elif opt == 'pattern':
                    tostr += ' (PATTERN ("' + ov + '"))'

                elif opt == 'format':
                    tostr += ' (CONSTRAINED BY {' + ov + '})'

                elif opt in ('minv', 'maxv'):     # TODO fix to handle both
                    if range:
                        if ttype in ('Integer', 'Number'):
                            tostr += ' ' + range
                        elif ttype in ('ArrayOf', 'Binary', 'String'):
                            tostr += ' (Size ' + range + ')'
                        else:
                            assert False        # Should never get here
                    range = ''

                else:
                    tostr += ' %' + opt + ': ' + str(ov) + '%'

        tdesc = f"    -- {td[jadn_defs.TypeDesc] if td[jadn_defs.TypeDesc] else ''}"
        jas += f"\n{tname} ::= {stype(ttype)}{tostr}"

        field_idx = jadn_defs.column_index('Structure', 'fields')
        if len(td) > field_idx:
            titems = deepcopy(td[field_idx])
            for n, i in enumerate(titems):              # 0:tag, 1:enum item name, 2:enum item desc  (enumerated), or
                if len(i) > jadn_defs.FieldOptions:     # 0:tag, 1:field name, 2:field type, 3: field opts, 4:field desc
                    desc = i[jadn_defs.FieldDesc]
                    i[jadn_defs.FieldType] = stype(i[jadn_defs.FieldType])

                else:
                    desc = i[jadn_defs.EnumDesc]

                desc = f"    -- {desc if desc else ''}"
                i.append(',' + desc if n < len(titems) - 1 else (' ' + desc if desc else ''))  # TODO: fix hacked desc for join
            flen = min(32, max(12, max([len(i[jadn_defs.FieldName]) for i in titems]) + 1 if titems else 0))
            jas += f" {{{tdesc}\n"

            if ttype.lower() == 'enumerated':
                fmt = f"    {{1:{flen}}} ({{0:d}}){{3}}"
                jas += '\n'.join([fmt.format(*i) for i in titems])

            else:
                fmt = '    {1:' + str(flen) + '} [{0:d}] {2}{3}{4}'
                items = []

                if ttype.lower() == 'record':
                    fmt = '    {1:' + str(flen) + '} {2}{3}{4}'

                for n, i in enumerate(titems):
                    ostr = ''
                    opts = jadn_utils.fopts_s2d(i[jadn_defs.FieldOptions])
                    if 'tfield' in opts:
                        ostr += f".&{opts['tfield']}"
                        del opts['tfield']

                    if 'vtype' in opts:
                        ostr += '.*'
                        del opts['vtype']

                    if 'minc' in opts:
                        if opts['minc'] == 0:         # TODO: handle array fields (max != 1)
                            ostr += ' OPTIONAL'
                        del opts['minc']

                    items += [fmt.format(i[jadn_defs.FieldID], i[jadn_defs.FieldName], i[jadn_defs.FieldType], ostr, i[5]) + (' %' + str(opts) if opts else '')]
                jas += '\n'.join(items)
            jas += '\n}\n' if titems else '}\n'
        else:
            jas += tdesc + '\n'
    return jas


def jas_dump(jadn, fname, source=''):
    with open(fname, 'w') as f:
        if source:
            f.write(f"-- Generated from {source}, {datetime.ctime(datetime.now())}\n\n")
        f.write(jas_dumps(jadn))

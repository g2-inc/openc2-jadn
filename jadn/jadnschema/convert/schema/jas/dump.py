"""
Translate JADN to JAS (JADN Abstract Syntax)
"""
from copy import deepcopy
from datetime import datetime

from .... import (
    jadn_defs,
    jadn_utils
)


stype_map = {                   # Map JADN built-in types to JAS type names (Equivalent ASN.1 types in comments)
    'Binary': 'BINARY',           # OCTET STRING
    'Boolean': 'BOOLEAN',         # BOOLEAN
    'Integer': 'INTEGER',         # INTEGER
    'Number': 'REAL',             # REAL
    'Null': 'NULL',               # NULL
    'String': 'STRING',           # UTF8String
    'Array': 'ARRAY',             # SEQUENCE
    'ArrayOf': 'ARRAY_OF',        # SEQUENCE OF
    'Choice': 'CHOICE',           # CHOICE
    'Enumerated': 'ENUMERATED',   # ENUMERATED
    'Map': 'MAP',                 # SET
    'Record': 'RECORD'            # SEQUENCE
}


def stype(jtype):
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
                jas += h + ':   ' + hdrs[h] + '\n'
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

    assert set(stype_map) == set(jadn_defs.TYPES.PRIMITIVES + jadn_defs.TYPES.STRUCTURES)         # Ensure type list is up to date
    tolist = ['compact', 'cvt', 'rtype', 'min', 'max', 'pattern', 'format']
    assert set(jadn_defs.TYPE_OPTIONS.values()) == set(tolist)                # Ensure type options list is up to date
    folist = ['rtype', 'atfield', 'min', 'max', 'etype', 'default']
    assert set(jadn_defs.FIELD_OPTIONS.values()) == set(folist)               # Ensure field options list is up to date
    for td in jadn['types']:                    # 0:type name, 1:base type, 2:type opts, 3:type desc, 4:fields
        tname = td[jadn_defs.TNAME]
        ttype = jadn_utils.basetype(td[jadn_defs.TTYPE])
        topts = jadn_utils.topts_s2d(td[jadn_defs.TOPTS])
        tostr = ''
        if 'min' in topts or 'max' in topts:
            lo = topts['min'] if 'min' in topts else 0
            hi = topts['max'] if 'max' in topts else 0
            range = ''
            if lo or hi:
                range = '(' + str(lo) + '..' + (str(hi) if hi else 'MAX') + ')'
        for opt in tolist:
            if opt in topts:
                ov = topts[opt]
                if opt == 'compact':
                    tostr += '.ID'
                elif opt == 'cvt':
                    if ov not in ('x'):
                        ov = 's:' + ov
                    tostr += '.' + ov
                elif opt =='rtype':
                    tostr += '(' + ov + ')'
                elif opt == 'pattern':
                    tostr += ' (PATTERN ("' + ov + '"))'
                elif opt == 'format':
                    tostr += ' (CONSTRAINED BY {' + ov + '})'
                elif opt in ('min', 'max'):     # TODO fix to handle both
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
        tdesc = '    -- ' + td[jadn_defs.TDESC] if td[jadn_defs.TDESC] else ''
        jas += '\n' + tname + ' ::= ' + stype(ttype) + tostr
        if len(td) > jadn_defs.FIELDS:
            titems = deepcopy(td[jadn_defs.FIELDS])
            for n, i in enumerate(titems):      # 0:tag, 1:enum item name, 2:enum item desc  (enumerated), or
                if len(i) > jadn_defs.FOPTS:              # 0:tag, 1:field name, 2:field type, 3: field opts, 4:field desc
                    desc = i[jadn_defs.FDESC]
                    i[jadn_defs.FTYPE] = stype(i[jadn_defs.FTYPE])
                else:
                    desc = i[jadn_defs.EDESC]
                desc = '    -- ' + desc if desc else ''
                i.append(',' + desc if n < len(titems) - 1 else (' ' + desc if desc else ''))   # TODO: fix hacked desc for join
            flen = min(32, max(12, max([len(i[jadn_defs.FNAME]) for i in titems]) + 1 if titems else 0))
            jas += ' {' + tdesc + '\n'
            if ttype.lower() == 'enumerated':
                fmt = '    {1:' + str(flen) + '} ({0:d}){3}'
                jas += '\n'.join([fmt.format(*i) for i in titems])
            else:
                fmt = '    {1:' + str(flen) + '} [{0:d}] {2}{3}{4}'
                if ttype.lower() == 'record':
                    fmt = '    {1:' + str(flen) + '} {2}{3}{4}'
                items = []
                for n, i in enumerate(titems):
                    ostr = ''
                    opts = jadn_utils.fopts_s2d(i[jadn_defs.FOPTS])
                    if 'atfield' in opts:
                        ostr += '.&' + opts['atfield']
                        del opts['atfield']
                    if 'rtype' in opts:
                        ostr += '.*'
                        del opts['rtype']
                    if 'min' in opts:
                        if opts['min'] == 0:         # TODO: handle array fields (max != 1)
                            ostr += ' OPTIONAL'
                        del opts['min']
                    items += [fmt.format(i[jadn_defs.FTAG], i[jadn_defs.FNAME], i[jadn_defs.FTYPE], ostr, i[5]) + (' %' + str(opts) if opts else '')]
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
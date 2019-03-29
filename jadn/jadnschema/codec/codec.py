"""
Abstract Object Encoder/Decoder

Object schema is specified in JSON Abstract Data Notation (JADN) format.

Codec currently supports three JSON concrete message formats (verbose,
concise, and minified) but can be extended to support XML or binary formats.

Copyright 2016 David Kemp
Licensed under the Apache License, Version 2.0
http://www.apache.org/licenses/LICENSE-2.0
"""

from __future__ import unicode_literals
import numbers
from binascii import b2a_hex

from .codec_format import (
    get_format_function,
    FMT_B2S,
    FMT_CHECK,
    FMT_NAME,
    FMT_S2B
)

from ..jadn_defs import *
from ..jadn_utils import (
    topts_s2d,
    fopts_s2d
)

__version__ = '0.2'

# TODO: add DEFAULT
# TODO: use CHOICE with both explicit (attribute) and implicit (wildcard field) type

# Codec Table fields
C_DEC = 0       # Decode function
C_ENC = 1       # Encode function
C_ETYPE = 2     # Encoded type

# Symbol Table fields
S_TDEF = 0      # JADN type definition
S_CODEC = 1     # CODEC table entry for this type
S_STYPE = 2     # Encoded identifier type (string or tag)
S_FORMAT = 3    # Function to check value constraints
S_TOPT = 4      # Type Options (dict format)
S_VSTR = 5      # Verbose_str
S_DMAP = 6      # Decode: Encoded field key or enum value to API
S_EMAP = 7      # Encode: API field key or enum value to Encoded
S_FLD = 8       # Field entries (definition and decoded options)

# Symbol Table Field Definition fields
S_FDEF = 0      # JADN field definition
S_FOPT = 1      # Field Options (dict format)
S_FNAMES = 2    # Possible field names returned from Choice type


class Codec:
    """
    Serialize (encode) and De-serialize (decode) values based on JADN syntax.

    verbose_rec - True: Record types encoded as JSON objects
                 False: Record types encoded as JSON arrays
    verbose_str - True: Identifiers encoded as JSON strings
                 False: Identifiers encoded as JSON integers (tags)

    Encoding modes: rec,   str     Record Encoding
    --------------  -----  -----  -----------
        'Verbose'  = True,  True    Dict, Name
        'M2M'      = False, False   List, Tag
    unused concise = False, True    List, Name
         unused    = True,  False   Dict, Tag
    """

    def __init__(self, schema, verbose_rec=False, verbose_str=False):
        self.schema = schema
        assert set(enctab) == set(JADN_TYPES.PRIMITIVES + JADN_TYPES.STRUCTURES)
        self.max_array = 100        # Conservative default upper bounds that can be overridden
        self.max_string = 255       # Codec defaults (these) -> Schema defaults (bounds) -> Datatype options (max)
        self.max_binary = 1000

        self.arrays = None          # Array types generated when cardinality > 1.
        self.symtab = None          # Symbol table - pre-computed values for all datatypes
        self.types = None           # Index of defined types
        self.set_mode(verbose_rec, verbose_str)     # Create symbol table based on encoding mode

    def decode(self, datatype, sval):       # Decode serialized value into API value
        try:
            ts = self.symtab[datatype]
        except KeyError:
            raise ValueError(f"datatype \"{datatype}\" is not defined")
        return ts[S_CODEC][C_DEC](ts, sval, self)     # Dispatch to type-specific decoder

    def encode(self, datatype, aval):       # Encode API value into serialized value
        try:
            ts = self.symtab[datatype]
        except KeyError:
            raise ValueError(f"datatype \"{datatype}\" is not defined")
        return ts[S_CODEC][C_ENC](ts, aval, self)     # Dispatch to type-specific encoder

    def set_mode(self, verbose_rec=False, verbose_str=False):
        def _add_dtype(fs, newfs):          # Create datatype needed by a field
            dname = f"${len(self.arrays)}"
            self.arrays.update({dname: newfs})
            fs[S_FDEF] = fs[S_FDEF][:]      # Make a copy to modify
            fs[S_FDEF][FTYPE] = dname       # Redirect field to dynamically generated type
            return dname

        def symf(fld):                      # Build symbol table field entries
            fs = [
                fld,                        # S_FDEF: JADN field definition
                fopts_s2d(fld[FOPTS]),      # S_FOPT: Field options (dict)
                []                          # S_FNAMES: Possible field names returned from Choice type  TODO: not used
            ]
            opts = fs[S_FOPT]
            if fld[FTYPE] == 'Enumerated' and 'rtype' in opts:      # Generate Enumerated from a referenced type
                rt = self.types[opts['rtype']]
                items = [[j[FTAG], j[FNAME], ''] for j in rt[FIELDS]]
                aa = ['', 'Enumerated', rt[TOPTS], '', items]       # Dynamic type definition
                aas = sym(aa)
                aa[TNAME] = _add_dtype(fs, aas)                     # Add to list of dynamically generated types
            if 'max' in opts and opts['max'] != 1:                  # Create ArrayOf for fields with cardinality > 1
                amin = opts['min'] if 'min' in opts and opts['min'] > 1 else 1      # Array cannot be empty
                amax = opts['max'] if opts['max'] > 0 else self.max_array           # Inherit max length if 0
                aa = ['', 'ArrayOf', [], '']                        # Dynamic JADN type definition
                aas = [                             # Symtab entry for dynamic type
                    aa,                             # 0: S_TDEF:  JADN type definition
                    enctab['ArrayOf'],              # 1: S_CODEC: Decoder, Encoder, Encoded type
                    list,                           # 2: S_STYPE: Encoded string type (str or tag)
                    get_format_function('', ''),    # 3: S_FORMAT: Functions that check value constraints
                    {'rtype': fs[S_FDEF][FTYPE], 'min': amin, 'max': amax}  # 4: S_TOPT:  Type Options (dict)
                ]
                aa[TNAME] = _add_dtype(fs, aas)                     # Add to list of dynamically generated types
            return fs

        def sym(t):                 # Build symbol table based on encoding modes
            symval = [
                t,                                  # 0: S_TDEF:  JADN type definition
                enctab[t[TTYPE]],                   # 1: S_CODEC: Decoder, Encoder, Encoded type
                type('') if verbose_str else int,   # 2: S_STYPE: Encoded string type (str or tag)
                [],                                 # 3: S_FORMAT: Functions that check value constraints
                topts_s2d(t[TOPTS]),                # 4: S_TOPT:  Type Options (dict)
                verbose_str,                        # 5: S_VSTR:  Verbose String Identifiers
                {},                                 # 6: S_DMAP: Encoded field key or enum value to API
                {},                                 # 7: S_EMAP: API field key or enum value to Encoded
                {}                                  # 8: S_FLD: Symbol table field entry
            ]
            if t[TTYPE] == 'Record':
                rtype = dict if verbose_rec else list
                symval[S_CODEC] = [_decode_maprec, _encode_maprec, rtype]
            fx = FNAME if verbose_str else FTAG
            if t[TTYPE] in ['Enumerated', 'Choice', 'Map', 'Record']:
                fx, fa = (FTAG, FTAG) if 'compact' in symval[S_TOPT] else (fx, FNAME)
                symval[S_DMAP] = {f[fx]: f[fa] for f in t[FIELDS]}
                symval[S_EMAP] = {f[fa]: f[fx] for f in t[FIELDS]}
                if t[TTYPE] in ['Choice', 'Map', 'Record']:
                    symval[S_FLD] = {f[fx]: symf(f) for f in t[FIELDS]}
            elif t[TTYPE] == 'Array':
                symval[S_FLD] = {f[FTAG]: symf(f) for f in t[FIELDS]}
            elif t[TTYPE] == 'ArrayOf':
                opts = symval[S_TOPT]
                amin = opts['min'] if 'min' in opts else 1
                amax = opts['max'] if 'max' in opts and opts['max'] > 0 else self.max_array
                opts.update({'min': amin, 'max': amax})
            fchk = symval[S_TOPT]['format'] if 'format' in symval[S_TOPT] else ''
            fcvt = symval[S_TOPT]['cvt'] if 'cvt' in symval[S_TOPT] else ''
            symval[S_FORMAT] = get_format_function(fchk, t[TTYPE], fcvt)
            return symval
        # TODO: Add string and binary min and max

        self.arrays = {}
        self.types = {t[TNAME]: t for t in self.schema['types']}        # pre-index types to allow symtab forward refs
        self.symtab = {t[TNAME]: sym(t) for t in self.schema['types']}
        self.symtab.update(self.arrays)                                 # Add generated arrays to symbol table
        self.symtab.update({t: [['', t], enctab[t], enctab[t][C_ETYPE], get_format_function('', t), []] for t in JADN_TYPES.PRIMITIVES})


def _bad_index(ts, k, val):
    td = ts[S_TDEF]
    raise ValueError(f"{td[TNAME]}({td[TTYPE]}): array index {k} out of bounds ({len(ts[S_FLD])}, {len(val)})")


def _bad_choice(ts, val):
    td = ts[S_TDEF]
    raise ValueError(f"{td[TNAME]}: choice must have one value: {val}")


def _bad_value(ts, val, fld=None):
    td = ts[S_TDEF]
    if fld is not None:
        raise ValueError(f"{td[TNAME]}({td[TTYPE]}): missing required field \"{fld[FNAME]}\": {val}")
    else:
        v = next(iter(val)) if type(val) == dict else val
        raise ValueError(f"{td[TNAME]}({td[TTYPE]}): bad value: {v}")


def _check_type(ts, val, vtype, fail=False):      # fail forces rejection of boolean vals for number types
    if vtype is not None:
        if fail or not isinstance(val, vtype):
            td = ts[S_TDEF]
            tn = f"{td[TNAME]} ({td[TTYPE]})" if td else 'Primitive'
            raise TypeError(f"{tn}: {val} is not {vtype}")


def _format(ts, val, fmtop):
    try:
        rval = ts[S_FORMAT][fmtop](val)         # fmtop selects function to check, serialize or deserialize
    except ValueError:
        td = ts[S_TDEF]
        tn = f"{td[TNAME]} ({td[TTYPE]})" if td[TNAME] else td[TTYPE]
        val = b2a_hex(val).decode() if isinstance(val, bytes) else val
        raise ValueError(f"{tn}: {val} is not a valid {ts[S_FORMAT][FMT_NAME]}")
    except NameError:
        td = ts[S_TDEF]
        tn = f"{td[TNAME]}({td[TTYPE]})" if td[TNAME] else td[TTYPE]
        raise ValueError(f"{tn}: {ts[S_FORMAT][FMT_NAME]} is not defined")
    except AttributeError:
        td = ts[S_TDEF]
        tn = f"{td[TNAME]}({td[TTYPE]})" if td[TNAME] else td[TTYPE]
        val = b2a_hex(val).decode() if isinstance(val, bytes) else val
        raise ValueError(f"{tn}: {val} is not supported: {ts[S_FORMAT][FMT_NAME]}")
    return rval


def _check_key(ts, val):
    try:
        return int(val) if isinstance(next(iter(ts[S_DMAP])), int) else val
    except ValueError:
        raise ValueError(f"{ts[S_TDEF][TNAME]}: {val} is not a valid field ID")


def _check_range(ts, val):
    op = ts[S_TOPT]
    tn = ts[S_TDEF][TNAME]
    if 'min' in op and val < op['min']:
        raise ValueError(f"{tn}: {len(val)} < minimum {op['min']}")
    if 'max' in op and val > op['max']:
        raise ValueError(f"{tn}: {len(val)} > maximum {op['max']}")


def _check_size(ts, val):
    op = ts[S_TOPT]
    tn = ts[S_TDEF][TNAME]
    if 'min' in op and len(val) < op['min']:
        raise ValueError(f"{tn}: {len(val)} < minimum {op['min']}")
    if 'max' in op and len(val) > op['max']:
        raise ValueError(f"{tn}: {len(val)} > maximum {op['max']}")


def _extra_value(ts, val, fld):
    td = ts[S_TDEF]
    raise ValueError(f"{td[TNAME]}({td[TTYPE]}): unexpected field: {val} not in {fld}:")


def _decode_array_of(ts, val, codec):
    _check_type(ts, val, list)
    _check_size(ts, val)
    return [codec.decode(ts[S_TOPT]['rtype'], v) for v in val]


def _encode_array_of(ts, val, codec):
    _check_type(ts, val, list)
    _check_size(ts, val)
    return [codec.encode(ts[S_TOPT]['rtype'], v) for v in val]


def _decode_binary(ts, val, codec):         # Decode ASCII string to bytes
    _check_type(ts, val, type(''))
    bval = _format(ts, val, FMT_S2B)        # Convert to bytes
    _check_size(ts, bval)
    return _format(ts, bval, FMT_CHECK)     # Check bytes value


def _encode_binary(ts, val, codec):         # Encode bytes to string
    _check_type(ts, val, bytes)
    _check_size(ts, val)
    val = _format(ts, val, FMT_CHECK)       # Check bytes value
    return _format(ts, val, FMT_B2S)        # Convert to string


def _decode_boolean(ts, val, codec):
    _check_type(ts, val, bool)
    return val


def _encode_boolean(ts, val, codec):
    _check_type(ts, val, bool)
    return val


def _decode_choice(ts, val, codec):         # Map Choice:  val == {key: value}
    _check_type(ts, val, dict)
    if len(val) != 1:
        _bad_choice(ts, val)
    k, v = next(iter(val.items()))
    k = _check_key(ts, k)
    if k not in ts[S_DMAP]:
        _bad_value(ts, val)
    f = ts[S_FLD][k][S_FDEF]
    k = ts[S_DMAP][k]
    return {k: codec.decode(f[FTYPE], v)}


def _encode_choice(ts, val, codec):
    _check_type(ts, val, dict)
    if len(val) != 1:
        _bad_choice(ts, val)
    k, v = next(iter(val.items()))
    if k not in ts[S_EMAP]:
        _bad_value(ts, val)
    k = ts[S_EMAP][k]
    f = ts[S_FLD][k][S_FDEF]
    return {k: codec.encode(f[FTYPE], v)}


def _decode_enumerated(ts, val, codec):
    _check_type(ts, val, type(next(iter(ts[S_DMAP]))))
    if val in ts[S_DMAP]:
        return ts[S_DMAP][val]
    else:
        td = ts[S_TDEF]
        raise ValueError(f"{td[TTYPE]}: {repr(val)} is not a valid {td[TNAME]}")


def _encode_enumerated(ts, val, codec):
    _check_type(ts, val, type(next(iter(ts[S_EMAP]))))
    if val in ts[S_EMAP]:
        return ts[S_EMAP][val]
    else:
        td = ts[S_TDEF]
        raise ValueError(f"{td[TTYPE]}: {repr(val)} is not a valid {td[TNAME]}")


def _decode_integer(ts, val, codec):
    _check_type(ts, val, numbers.Integral, isinstance(val, bool))
    _check_range(ts, val)
    return _format(ts, val, FMT_CHECK)


def _encode_integer(ts, val, codec):
    _check_type(ts, val, numbers.Integral, isinstance(val, bool))
    _check_range(ts, val)
    return _format(ts, val, FMT_CHECK)


def _decode_number(ts, val, codec):
    _check_type(ts, val, numbers.Real, isinstance(val, bool))
    _check_range(ts, val)
    return _format(ts, val, FMT_CHECK)


def _encode_number(ts, val, codec):
    _check_type(ts, val, numbers.Real, isinstance(val, bool))
    _check_range(ts, val)
    return _format(ts, val, FMT_CHECK)


def _decode_maprec(ts, sval, codec):
    _check_type(ts, sval, ts[S_CODEC][C_ETYPE])
    val = sval
    if ts[S_CODEC][C_ETYPE] == dict:
        val = {_check_key(ts, k): v for k, v in sval.items()}
    aval = dict()
    fx = FNAME if ts[S_VSTR] else FTAG  # Verbose or minified identifier strings
    fnames = [k for k in ts[S_FLD]]
    for f in ts[S_TDEF][FIELDS]:
        fs = ts[S_FLD][f[fx]]           # Symtab entry for field
        fd = fs[S_FDEF]                 # JADN field definition from symtab
        fopts = fs[S_FOPT]              # Field options dict
        if type(val) == dict:
            fn = next(iter(set(val) & set(fs[S_FNAMES])), None) if fd[FNAME] == '<' else f[fx]
            sv = val[fn] if fn in val else None
        else:
            fn = fd[FTAG] - 1
            sv = val[fn] if len(val) > fn else None
        if sv is not None:
            if fd[FNAME] == '<':
                if type(val) == dict:
                    aval.update(codec.decode(fd[FTYPE], {fn: sv}))
                    fnames.append(fn)
                else:
                    aval.update(codec.decode(fd[FTYPE], sv))
            elif 'atfield' in fopts:  # Type of this field is specified by contents of another field
                ctf = fopts['atfield']
                choice_type = val[ctf] if isinstance(val, dict) else val[ts[S_EMAP][ctf] - 1]
                av = codec.decode(fd[FTYPE], {choice_type: sv})
                aval[fd[FNAME]] = next(iter(av.values()))
            else:
                aval[fd[FNAME]] = codec.decode(fd[FTYPE], sv)
        else:
            if 'min' not in fopts or fopts['min'] > 0:
                _bad_value(ts, val, fd)
    extra = set(val) - set(fnames) if type(val) == dict else len(val) > len(ts[S_FLD])
    if extra:
        _extra_value(ts, val, extra)
    return aval


def _encode_maprec(ts, aval, codec):
    _check_type(ts, aval, dict)
    sval = ts[S_CODEC][C_ETYPE]()
    assert type(sval) in (list, dict)
    fx = FNAME if ts[S_VSTR] else FTAG  # Verbose or minified identifier strings
    fnames = [f[S_FDEF][FNAME] for f in ts[S_FLD].values()]
    for f in ts[S_TDEF][FIELDS]:
        fs = ts[S_FLD][f[fx]]           # Symtab entry for field
        fd = fs[S_FDEF]                 # JADN field definition from symtab
        fname = fd[FNAME]               # Field name
        fopts = fs[S_FOPT]              # Field options dict
        if fd[FNAME] == '<':            # Pull Choice value up to this level
            fname = next(iter(set(aval) & set(fs[S_FNAMES])), None)
            fnames.append(fname)
            sv = codec.encode(fd[FTYPE], {fname: aval[fname]}) if fname in aval else None
        elif 'atfield' in fopts:        # Type of this field is specified by contents of another field
            choice_type = aval[fopts['atfield']]
            e = codec.encode(fd[FTYPE], {choice_type: aval[fname]})
            sv = next(iter(e.values()))
        else:
            sv = codec.encode(fd[FTYPE], aval[fname]) if fname in aval else None
        if sv is None and ('min' not in fopts or fopts['min'] > 0):     # Missing required field
            _bad_value(ts, aval, fd)
        if type(sval) == list:        # Concise Record
            sval.append(sv)
        elif sv is not None:            # Map or Verbose Record
            if fd[FNAME] == '<':
                sval.update(sv)
            else:
                sval[fd[fx]] = sv

    if set(aval) - set(fnames):
        _extra_value(ts, aval, fnames)
    if type(sval) == list:
        while sval and sval[-1] is None:    # Strip non-populated trailing optional values
            sval.pop()
    return sval


def _decode_array(ts, sval, codec):          # Ordered list of types, returned as a list
    if 'cvt' in ts[S_TOPT]:
        _check_type(ts, sval, type(''))
        val = _format(ts, sval, FMT_S2B)    # Convert string to multipart value (array)
    else:
        val = sval
    _check_type(ts, val, list)
    aval = list()
    extra = len(val) > len(ts[S_FLD])
    if extra:
        _extra_value(ts, val, extra)        # TODO: write sensible display of excess values
    for fn in ts[S_TDEF][FIELDS]:
        f = ts[S_FLD][fn[FTAG]][S_FDEF]        # Use symtab field definition
        fx = f[FTAG] - 1
        fopts = ts[S_FLD][fx + 1][S_FOPT]
        sv = val[fx] if len(val) > fx else None
        if sv is not None:
            if 'atfield' in fopts:
                choice_type = val[int(fopts['atfield']) - 1]
                if 'max' in fopts and fopts['max'] != 1:
                    cftype = codec.symtab[fn[FTYPE]][S_FLD][choice_type][S_FDEF][FTYPE]
                    codec.symtab[f[FTYPE]][S_TOPT]['rtype'] = cftype    # Patch dynamic ArrayOf with fixed type
                    av = codec.decode(f[FTYPE], sv)
                else:
                    d = codec.decode(f[FTYPE], {choice_type: sv})        # TODO: fix str/int handling of choice
                    av = d[next(iter(d))]
            else:
                av = codec.decode(f[FTYPE], sv)
            aval.append(av)
        else:
            aval.append(None)
            if 'min' not in fopts or fopts['min'] > 0:
                _bad_value(ts, val, f)
    while aval and aval[-1] is None:    # Strip non-populated trailing optional values
        aval.pop()
    return aval


def _encode_array(ts, aval, codec):
    _check_type(ts, aval, list)
    sval = list()
    extra = len(aval) > len(ts[S_FLD])
    if extra:
        _extra_value(ts, aval, extra)
    for fn in ts[S_TDEF][FIELDS]:
        f = ts[S_FLD][fn[FTAG]][S_FDEF]       # Use symtab field definition
        fx = f[FTAG] - 1
        fopts = ts[S_FLD][fx + 1][S_FOPT]
        av = aval[fx] if len(aval) > fx else None
        if av is not None:
            if 'atfield' in fopts:
                choice_type = aval[int(fopts['atfield']) - 1]
                if 'max' in fopts and fopts['max'] != 1:
                    cftype = codec.symtab[fn[FTYPE]][S_FLD][choice_type][S_FDEF][FTYPE]
                    codec.symtab[f[FTYPE]][S_TOPT]['rtype'] = cftype    # Patch dynamic ArrayOf with fixed type
                    sv = codec.encode(f[FTYPE], av)
                else:
                    e = codec.encode(f[FTYPE], {choice_type: av})
                    sv = e[next(iter(e))]
            else:
                sv = codec.encode(f[FTYPE], av)
            sval.append(sv)
        else:
            sval.append(None)
            if 'min' not in fopts or fopts['min'] > 0:
                _bad_value(ts, aval, f)
    while sval and sval[-1] is None:    # Strip non-populated trailing optional values
        sval.pop()
    if 'cvt' in ts[S_TOPT]:
        sval = _format(ts, sval, FMT_B2S)    # Convert multipart value to string
    return sval


def _decode_null(ts, val, codec):
    _check_type(ts, val, type(''))
    if val:
        _bad_value(ts, val)
    return val


def _encode_null(ts, val, codec):
    _check_type(ts, val, type(''))
    if val:
        _bad_value(ts, val)
    return val


def _decode_string(ts, val, codec):
    _check_type(ts, val, type(''))
    _check_size(ts, val)
    return _format(ts, val, FMT_CHECK)


def _encode_string(ts, val, codec):
    _check_type(ts, val, type(''))
    _check_size(ts, val)
    return _format(ts, val, FMT_CHECK)


enctab = {  # decode, encode, min encoded type
    'Binary': (_decode_binary, _encode_binary, str),
    'Boolean': (_decode_boolean, _encode_boolean, bool),
    'Integer': (_decode_integer, _encode_integer, int),
    'Number': (_decode_number, _encode_number, float),
    'Null': (_decode_null, _encode_null, str),
    'String': (_decode_string, _encode_string, str),
    'ArrayOf': (_decode_array_of, _encode_array_of, list),
    'Array': (_decode_array, _encode_array, list),
    'Choice': (_decode_choice, _encode_choice, dict),
    'Enumerated': (_decode_enumerated, _encode_enumerated, int),
    'Map': (_decode_maprec, _encode_maprec, dict),
    'MapOf': (None, None, None),
    'Record': (None, None, None),   # Dynamic values
}

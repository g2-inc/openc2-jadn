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
from ..jadn_defs import *
from ..jadn_utils import topts_s2d, fopts_s2d
from .codec_format import get_format_function
from .codec_format import FMT_NAME, FMT_CHECK, FMT_B2S, FMT_S2B

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
        assert set(enctab) == set(PRIMITIVE_TYPES + STRUCTURE_TYPES)
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
            raise ValueError('datatype "%s" is not defined' % (datatype))
        return ts[S_CODEC][C_DEC](ts, sval, self)     # Dispatch to type-specific decoder

    def encode(self, datatype, aval):       # Encode API value into serialized value
        try:
            ts = self.symtab[datatype]
        except KeyError:
            raise ValueError('datatype "%s" is not defined' % (datatype))
        return ts[S_CODEC][C_ENC](ts, aval, self)     # Dispatch to type-specific encoder

    def set_mode(self, verbose_rec=False, verbose_str=False):
        def _add_dtype(fs, newfs):          # Create datatype needed by a field
            dname = '$' + str(len(self.arrays))
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
        self.symtab.update({t: [['', t], enctab[t], enctab[t][C_ETYPE], get_format_function('', t), []] for t in PRIMITIVE_TYPES})


def _bad_index(ts, k, val):
    td = ts[S_TDEF]
    raise ValueError('%s(%s): array index %d out of bounds (%d, %d)' % (td[TNAME], td[TTYPE], k, len(ts[S_FLD]), len(val)))


def _bad_choice(ts, val):
    td = ts[S_TDEF]
    raise ValueError('%s: choice must have one value: %s' % (td[TNAME], val))


def _bad_value(ts, val, fld=None):
    td = ts[S_TDEF]
    if fld is not None:
        raise ValueError('%s(%s): missing required field "%s": %s' % (td[TNAME], td[TTYPE], fld[FNAME], val))
    else:
        v = next(iter(val)) if type(val) == dict else val
        raise ValueError('%s(%s): bad value: %s' % (td[TNAME], td[TTYPE], v))


def _check_type(ts, val, vtype, fail=False):      # fail forces rejection of boolean vals for number types
    if vtype is not None:
        if fail or not isinstance(val, vtype):
            td = ts[S_TDEF]
            tn = ('%s(%s)' % (td[TNAME], td[TTYPE]) if td else 'Primitive')
            raise TypeError('%s: %s is not %s' % (tn, val, vtype))


def _format(ts, val, fmtop):
    try:
        rval = ts[S_FORMAT][fmtop](val)         # fmtop selects function to check, serialize or deserialize
    except ValueError:
        td = ts[S_TDEF]
        tn = ('%s(%s)' % (td[TNAME], td[TTYPE]) if td[TNAME] else td[TTYPE])
        val = b2a_hex(val).decode() if isinstance(val, bytes) else val
        raise ValueError('%s: %s is not a valid %s' % (tn, val, ts[S_FORMAT][FMT_NAME]))
    except NameError:
        td = ts[S_TDEF]
        tn = ('%s(%s)' % (td[TNAME], td[TTYPE]) if td[TNAME] else td[TTYPE])
        raise ValueError('%s: %s is not defined' % (tn, ts[S_FORMAT][FMT_NAME]))
    except AttributeError:
        td = ts[S_TDEF]
        tn = ('%s(%s)' % (td[TNAME], td[TTYPE]) if td[TNAME] else td[TTYPE])
        val = b2a_hex(val).decode() if isinstance(val, bytes) else val
        raise ValueError('%s: %s is not supported: %s' % (tn, val, ts[S_FORMAT][FMT_NAME]))
    return rval


def _check_range(ts, val):
    op = ts[S_TOPT]
    tn = ts[S_TDEF][TNAME]
    if 'min' in op and val < op['min']:
        raise ValueError('%s: %s < minimum %s' % (tn, len(val), op['min']))
    if 'max' in op and val > op['max']:
        raise ValueError('%s: %s > maximum %s' % (tn, len(val), op['max']))


def _check_size(ts, val):
    op = ts[S_TOPT]
    tn = ts[S_TDEF][TNAME]
    if 'min' in op and len(val) < op['min']:
        raise ValueError('%s: length %s < minimum %s' % (tn, len(val), op['min']))
    if 'max' in op and len(val) > op['max']:
        raise ValueError('%s: length %s > maximum %s' % (tn, len(val), op['max']))


def _extra_value(ts, val, fld):
    td = ts[S_TDEF]
    raise ValueError('%s(%s): unexpected field: %s not in %s:' % (td[TNAME], td[TTYPE], val, fld))


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
        raise ValueError('%s: %r is not a valid %s' % (td[TTYPE], val, td[TNAME]))


def _encode_enumerated(ts, val, codec):
    _check_type(ts, val, type(next(iter(ts[S_EMAP]))))
    if val in ts[S_EMAP]:
        return ts[S_EMAP][val]
    else:
        td = ts[S_TDEF]
        raise ValueError('%s: %r is not a valid %s' % (td[TTYPE], val, td[TNAME]))


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


def _decode_maprec(ts, val, codec):
    _check_type(ts, val, ts[S_CODEC][C_ETYPE])
    apival = dict()
    fx = FNAME if ts[S_VSTR] else FTAG  # Verbose or minified identifier strings
    fnames = [k for k in ts[S_FLD]]
    for f in ts[S_TDEF][FIELDS]:
        fs = ts[S_FLD][f[fx]]           # Symtab entry for field
        fd = fs[S_FDEF]                 # JADN field definition from symtab
        fopts = fs[S_FOPT]              # Field options dict
        if type(val) == dict:
            fn = next(iter(set(val) & set(fs[S_FNAMES])), None) if fd[FNAME] == '<' else f[fx]
            fv = val[fn] if fn in val else None
        else:
            fn = fd[FTAG] - 1
            fv = val[fn] if len(val) > fn else None
        if fv is not None:
            if fd[FNAME] == '<':
                if type(val) == dict:
                    apival.update(codec.decode(fd[FTYPE], {fn: fv}))
                    fnames.append(fn)
                else:
                    apival.update(codec.decode(fd[FTYPE], fv))
            elif 'atfield' in fopts:  # Type of this field is specified by contents of another field
                ctf = fopts['atfield']
                choice_type = val[ctf] if isinstance(val, dict) else val[ts[S_EMAP][ctf] - 1]
                av = codec.decode(fd[FTYPE], {choice_type: fv})
                apival[fd[FNAME]] = next(iter(av.values()))
            else:
                apival[fd[FNAME]] = codec.decode(fd[FTYPE], fv)
        else:
            if 'min' not in fopts or fopts['min'] > 0:
                _bad_value(ts, val, fd)
    extra = set(val) - set(fnames) if type(val) == dict else len(val) > len(ts[S_FLD])
    if extra:
        _extra_value(ts, val, extra)
    return apival


def _encode_maprec(ts, val, codec):
    _check_type(ts, val, dict)
    encval = ts[S_CODEC][C_ETYPE]()
    assert type(encval) in (list, dict)
    fx = FNAME if ts[S_VSTR] else FTAG  # Verbose or minified identifier strings
    fnames = [f[S_FDEF][FNAME] for f in ts[S_FLD].values()]
    for f in ts[S_TDEF][FIELDS]:
        fs = ts[S_FLD][f[fx]]           # Symtab entry for field
        fd = fs[S_FDEF]                 # JADN field definition from symtab
        fname = fd[FNAME]               # Field name
        fopts = fs[S_FOPT]              # Field options dict
        if fd[FNAME] == '<':            # Pull Choice value up to this level
            fname = next(iter(set(val) & set(fs[S_FNAMES])), None)
            fnames.append(fname)
            fv = codec.encode(fd[FTYPE], {fname: val[fname]}) if fname in val else None
        elif 'atfield' in fopts:        # Type of this field is specified by contents of another field
            choice_type = val[fopts['atfield']]
            e = codec.encode(fd[FTYPE], {choice_type: val[fname]})
            fv = next(iter(e.values()))
        else:
            fv = codec.encode(fd[FTYPE], val[fname]) if fname in val else None
        if fv is None and ('min' not in fopts or fopts['min'] > 0):     # Missing required field
            _bad_value(ts, val, fd)
        if type(encval) == list:        # Concise Record
            encval.append(fv)
        elif fv is not None:            # Map or Verbose Record
            if fd[FNAME] == '<':
                encval.update(fv)
            else:
                encval[fd[fx]] = fv

    if set(val) - set(fnames):
        _extra_value(ts, val, fnames)
    if type(encval) == list:
        while encval and encval[-1] is None:    # Strip non-populated trailing optional values
            encval.pop()
    return encval


def _decode_array(ts, aval, codec):          # Ordered list of types, returned as a list
    if 'cvt' in ts[S_TOPT]:
        _check_type(ts, aval, type(''))
        val = _format(ts, aval, FMT_S2B)    # Convert string to multipart value (array)
    else:
        val = aval
    _check_type(ts, val, list)
    apival = list()
    extra = len(val) > len(ts[S_FLD])
    if extra:
        _extra_value(ts, val, extra)        # TODO: write sensible display of excess values
    for fn in ts[S_TDEF][FIELDS]:
        f = ts[S_FLD][fn[FTAG]][S_FDEF]        # Use symtab field definition
        fx = f[FTAG] - 1
        fopts = ts[S_FLD][fx + 1][S_FOPT]
        av = val[fx] if len(val) > fx else None
        if av is not None:
            if 'atfield' in fopts:
                choice_type = val[int(fopts['atfield']) - 1]
                d = codec.decode(f[FTYPE], {choice_type: av})        # TODO: fix str/int handling of choice
                dv = d[next(iter(d))]
            else:
                dv = codec.decode(f[FTYPE], av)
            apival.append(dv)
        else:
            apival.append(None)
            if 'min' not in fopts or fopts['min'] > 0:
                _bad_value(ts, val, f)
    while apival and apival[-1] is None:    # Strip non-populated trailing optional values
        apival.pop()
    return apival


def _encode_array(ts, val, codec):
    _check_type(ts, val, list)
    encval = list()
    extra = len(val) > len(ts[S_FLD])
    if extra:
        _extra_value(ts, val, extra)
    for fn in ts[S_TDEF][FIELDS]:
        f = ts[S_FLD][fn[FTAG]][S_FDEF]       # Use symtab field definition
        fx = f[FTAG] - 1
        fopts = ts[S_FLD][fx + 1][S_FOPT]
        av = val[fx] if len(val) > fx else None
        if av is not None:
            if 'atfield' in fopts:
                choice_type = val[int(fopts['atfield']) - 1]
                e = codec.encode(f[FTYPE], {choice_type: av})
                ev = e[next(iter(e))]
            else:
                ev = codec.encode(f[FTYPE], av)
            encval.append(ev)
        else:
            encval.append(None)
            if 'min' not in fopts or fopts['min'] > 0:
                _bad_value(ts, val, f)
    while encval and encval[-1] is None:    # Strip non-populated trailing optional values
        encval.pop()
    if 'cvt' in ts[S_TOPT]:
        encval = _format(ts, encval, FMT_B2S)    # Convert multipart value to string
    return encval


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
    'Record': (None, None, None),   # Dynamic values
}

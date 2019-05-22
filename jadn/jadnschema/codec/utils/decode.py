"""
Codec Decoding functions
"""
import numbers

from . import general

from ..config import *

from ..codec_format import (
    FMT_CHECK,
    FMT_S2B
)

from ...jadn_defs import (
    # Type Indexes
    TypeName,
    BaseType,
    Fields,
    # Field Indexes
    FieldName,
    FieldType,
    FieldID
)


def binary(ts, val, codec):  # Decode ASCII string to bytes
    general.check_type(ts, val, type(''))
    bval =general.format(ts, val, FMT_S2B)  # Convert to bytes
    general.check_size(ts, bval)
    return general.format(ts, bval, FMT_CHECK)  # Check bytes value


def boolean(ts, val, codec):
    general.check_type(ts, val, bool)
    return val


def integer(ts, val, codec):
    general.check_type(ts, val, numbers.Integral, isinstance(val, bool))
    general.check_range(ts, val)
    return general.format(ts, val, FMT_CHECK)


def number(ts, val, codec):
    general.check_type(ts, val, numbers.Real, isinstance(val, bool))
    general.check_range(ts, val)
    return general.format(ts, val, FMT_CHECK)


def null(ts, val, codec):
    general.check_type(ts, val, type(''))
    if val:
        general.bad_value(ts, val)
    return val


def string(ts, val, codec):
    general.check_type(ts, val, type(''))
    general.check_size(ts, val)
    return general.format(ts, val, FMT_CHECK)


def enumerated(ts, val, codec):
    general.check_type(ts, val, type(next(iter(ts[S_DMAP]))))
    if val in ts[S_DMAP]:
        return ts[S_DMAP][val]
    else:
        td = ts[S_TDEF]
        raise ValueError('%s: %r is not a valid %s' % (td[BaseType], val, td[TypeName]))


def choice(ts, val, codec):  # Map Choice:  val == {key: value}
    general.check_type(ts, val, dict)
    if len(val) != 1:
       general.bad_choice(ts, val)
    k, v = next(iter(val.items()))
    k = general.check_key(ts, k)
    if k not in ts[S_DMAP]:
        general.bad_value(ts, val)
    f = ts[S_FLD][k][S_FDEF]
    k = ts[S_DMAP][k]
    return {k: codec.decode(f[FieldType], v)}


def maprec(ts, sval, codec):
    general.check_type(ts, sval, ts[S_CODEC][C_ETYPE])
    val = sval
    if ts[S_CODEC][C_ETYPE] == dict:
        val = {general.check_key(ts, k): v for k, v in sval.items()}
    aval = dict()
    fx = FieldName if ts[S_VSTR] else FieldID  # Verbose or minified identifier strings
    fnames = [k for k in ts[S_FLD]]
    for f in ts[S_TDEF][Fields]:
        fs = ts[S_FLD][f[fx]]  # Symtab entry for field
        fd = fs[S_FDEF]  # JADN field definition from symtab
        fopts = fs[S_FOPT]  # Field options dict
        if type(val) == dict:
            fn = next(iter(set(val) & set(fs[S_FNAMES])), None) if fd[FieldName] == '<' else f[fx]
            sv = val[fn] if fn in val else None
        else:
            fn = fd[FieldID] - 1
            sv = val[fn] if len(val) > fn else None
        if sv is not None:
            if fd[FieldName] == '<':
                if type(val) == dict:
                    aval.update(codec.decode(fd[FieldType], {fn: sv}))
                    fnames.append(fn)
                else:
                    aval.update(codec.decode(fd[FieldType], sv))
            elif 'tfield' in fopts:  # Type of this field is specified by contents of another field
                ctf = fopts['tfield']
                choice_type = val[ctf] if isinstance(val, dict) else val[ts[S_EMAP][ctf] - 1]
                av = codec.decode(fd[FieldType], {choice_type: sv})
                aval[fd[FieldName]] = next(iter(av.values()))
            else:
                aval[fd[FieldName]] = codec.decode(fd[FieldType], sv)
        else:
            if 'minc' not in fopts or fopts['minc'] > 0:
                general.bad_value(ts, val, fd)
    extra = set(val) - set(fnames) if type(val) == dict else len(val) > len(ts[S_FLD])
    if extra:
        general.extra_value(ts, val, extra)
    return aval


def array(ts, sval, codec):  # Ordered list of types, returned as a list
    if 'sopt' in ts[S_TOPT]:
        general.check_type(ts, sval, type(''))
        val =general.format(ts, sval, FMT_S2B)  # Convert string to multipart value (array)
    else:
        val = sval
    general.check_type(ts, val, list)
    aval = list()
    extra = len(val) > len(ts[S_FLD])
    if extra:
        general.extra_value(ts, val, extra)  # TODO: write sensible display of excess values
    for fn in ts[S_TDEF][Fields]:
        f = ts[S_FLD][fn[FieldID]][S_FDEF]  # Use symtab field definition
        fx = f[FieldID] - 1
        fopts = ts[S_FLD][fx + 1][S_FOPT]
        sv = val[fx] if len(val) > fx else None
        if sv is not None:
            if 'tfield' in fopts:
                choice_type = val[int(fopts['tfield']) - 1]
                if 'maxc' in fopts and fopts['maxc'] != 1:
                    cftype = codec.symtab[fn[FieldType]][S_FLD][choice_type][S_FDEF][FieldType]
                    codec.symtab[f[FieldType]][S_TOPT]['vtype'] = cftype  # Patch dynamic ArrayOf with fixed type
                    av = codec.decode(f[FieldType], sv)
                else:
                    d = codec.decode(f[FieldType], {choice_type: sv})  # TODO: fix str/int handling of choice
                    av = d[next(iter(d))]
            else:
                av = codec.decode(f[FieldType], sv)
            aval.append(av)
        else:
            aval.append(None)
            if 'minc' not in fopts or fopts['minc'] > 0:
                general.bad_value(ts, val, f)
    while aval and aval[-1] is None:  # Strip non-populated trailing optional values
        aval.pop()
    return aval


def array_of(ts, val, codec):
    general.check_type(ts, val, list)
    general.check_size(ts, val)
    return [codec.decode(ts[S_TOPT]['vtype'], v) for v in val]


def map_of(ts, val, codec):
    general.check_type(ts, val, map)
    general.check_size(ts, val)
    return [codec.decode(ts[S_TOPT]['vtype'], v) for v in val]

"""
Codec Encoding functions
"""
import numbers

from . import general

from ..constants import (
    C_ETYPE,
    S_CODEC,
    S_EMAP,
    S_FDEF,
    S_FLD,
    S_FNAMES,
    S_FOPT,
    S_TDEF,
    S_TOPT,
    S_VSTR
)

from ..codec_format import (
    FMT_B2S,
    FMT_CHECK
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


def binary(ts, val, codec):         # Encode bytes to string
    general.check_type(ts, val, bytes)
    general.check_size(ts, val)
    val = general.format(ts, val, FMT_CHECK)       # Check bytes value
    return general.format(ts, val, FMT_B2S)        # Convert to string


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
    general.check_type(ts, val, type(next(iter(ts[S_EMAP]))))
    if val in ts[S_EMAP]:
        return ts[S_EMAP][val]
    else:
        td = ts[S_TDEF]
        raise ValueError('%s: %r is not a valid %s' % (td[BaseType], val, td[TypeName]))


def choice(ts, val, codec):
    general.check_type(ts, val, dict)
    if len(val) != 1:
        general.bad_choice(ts, val)
    k, v = next(iter(val.items()))
    if k not in ts[S_EMAP]:
        general.bad_value(ts, val)
    k = ts[S_EMAP][k]
    f = ts[S_FLD][k][S_FDEF]
    return {k: codec.encode(f[FieldType], v)}


def maprec(ts, aval, codec):
    general.check_type(ts, aval, dict)
    sval = ts[S_CODEC][C_ETYPE]()
    assert type(sval) in (list, dict)
    fx = FieldName if ts[S_VSTR] else FieldID  # Verbose or minified identifier strings
    fnames = [f[S_FDEF][FieldName] for f in ts[S_FLD].values()]
    for f in ts[S_TDEF][Fields]:
        fs = ts[S_FLD][f[fx]]           # Symtab entry for field
        fd = fs[S_FDEF]                 # JADN field definition from symtab
        fname = fd[FieldName]               # Field name
        fopts = fs[S_FOPT]              # Field options dict
        if fd[FieldName] == '<':            # Pull Choice value up to this level
            fname = next(iter(set(aval) & set(fs[S_FNAMES])), None)
            fnames.append(fname)
            sv = codec.encode(fd[FieldType], {fname: aval[fname]}) if fname in aval else None
        elif 'tfield' in fopts:        # Type of this field is specified by contents of another field
            choice_type = aval[fopts['tfield']]
            e = codec.encode(fd[FieldType], {choice_type: aval[fname]})
            sv = next(iter(e.values()))
        else:
            sv = codec.encode(fd[FieldType], aval[fname]) if fname in aval else None
        if sv is None and ('minc' not in fopts or fopts['minc'] > 0):     # Missing required field
            general.bad_value(ts, aval, fd)
        if type(sval) == list:        # Concise Record
            sval.append(sv)
        elif sv is not None:            # Map or Verbose Record
            if fd[FieldName] == '<':
                sval.update(sv)
            else:
                sval[fd[fx]] = sv

    if set(aval) - set(fnames):
        general.extra_value(ts, aval, fnames)
    if type(sval) == list:
        while sval and sval[-1] is None:    # Strip non-populated trailing optional values
            sval.pop()
    return sval


def array(ts, aval, codec):
    general.check_type(ts, aval, list)
    sval = list()
    extra = len(aval) > len(ts[S_FLD])
    if extra:
        general.extra_value(ts, aval, extra)
    for fn in ts[S_TDEF][Fields]:
        f = ts[S_FLD][fn[FieldID]][S_FDEF]       # Use symtab field definition
        fx = f[FieldID] - 1
        fopts = ts[S_FLD][fx + 1][S_FOPT]
        av = aval[fx] if len(aval) > fx else None
        if av is not None:
            if 'tfield' in fopts:
                choice_type = aval[int(fopts['tfield']) - 1]
                if 'maxc' in fopts and fopts['maxc'] != 1:
                    cftype = codec.symtab[fn[FieldType]][S_FLD][choice_type][S_FDEF][FieldType]
                    codec.symtab[f[FieldType]][S_TOPT]['vtype'] = cftype    # Patch dynamic ArrayOf with fixed type
                    sv = codec.encode(f[FieldType], av)
                else:
                    e = codec.encode(f[FieldType], {choice_type: av})
                    sv = e[next(iter(e))]
            else:
                sv = codec.encode(f[FieldType], av)
            sval.append(sv)
        else:
            sval.append(None)
            if 'minc' not in fopts or fopts['minc'] > 0:
               general.bad_value(ts, aval, f)
    while sval and sval[-1] is None:    # Strip non-populated trailing optional values
        sval.pop()

    # TODO: Validat this
    if 'sopt' in ts[S_TOPT] or 'format' in ts[S_TOPT]:
        sval = general.format(ts, sval, FMT_B2S)    # Convert multipart value to string
    return sval


def array_of(ts, val, codec):
    general.check_type(ts, val, list)
    general.check_size(ts, val)
    return [codec.encode(ts[S_TOPT]['vtype'], v) for v in val]


def map_of(ts, val, codec):
    general.check_type(ts, val, map)
    general.check_size(ts, val)
    return [codec.encode(ts[S_TOPT]['vtype'], v) for v in val]

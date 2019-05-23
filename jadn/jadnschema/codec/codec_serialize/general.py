"""
Codec General Utilities
"""

from binascii import b2a_hex

from ..constants import (
    S_DMAP,
    S_FLD,
    S_FORMAT,
    S_TDEF,
    S_TOPT
)

from ..codec_format import FMT_NAME

from ...jadn_defs import (
    # Type Indexes
    TypeName,
    BaseType,
    # Field Indexes
    FieldName,
)


def bad_index(ts, k, val):
    td = ts[S_TDEF]
    raise ValueError(f"{td[TypeName]}({td[BaseType]}): array index {k} out of bounds ({len(ts[S_FLD])}, {len(val)})")


def bad_choice(ts, val):
    td = ts[S_TDEF]
    raise ValueError(f"{td[TypeName]}: choice must have one value: {val}")


def bad_value(ts, val, fld=None):
    td = ts[S_TDEF]
    if fld is not None:
        raise ValueError(f"{td[TypeName]}({td[BaseType]}): missing required field \"{fld[FieldName]}\": {val}")
    else:
        v = next(iter(val)) if type(val) == dict else val
        raise ValueError(f"{td[TypeName]}({td[BaseType]}): bad value: {v}")


def check_type(ts, val, vtype, fail=False):      # fail forces rejection of boolean vals for number types
    if vtype is not None:
        if fail or not isinstance(val, vtype):
            td = ts[S_TDEF]
            tn = f"{td[TypeName]}({td[BaseType]})" if td else 'Primitive'
            raise TypeError(f"{tn}: {val} is not {vtype}")


def format(ts, val, fmtop):
    try:
        rval = ts[S_FORMAT][fmtop](val)         # fmtop selects function to check, serialize or deserialize

    except ValueError:
        td = ts[S_TDEF]
        tn = f"{td[TypeName]}({td[BaseType]})" if td[TypeName] else td[BaseType]
        val = b2a_hex(val).decode() if isinstance(val, bytes) else val
        raise ValueError(f"{tn}: {val} is not a valid {ts[S_FORMAT][FMT_NAME]}")

    except NameError:
        td = ts[S_TDEF]
        tn = f"{td[TypeName]}({td[BaseType]})" if td[TypeName] else td[BaseType]
        raise ValueError(f"{tn}: {ts[S_FORMAT][FMT_NAME]} is not defined")

    except AttributeError:
        td = ts[S_TDEF]
        tn = f"{td[TypeName]}({td[BaseType]})" if td[TypeName] else td[BaseType]
        val = b2a_hex(val).decode() if isinstance(val, bytes) else val
        raise ValueError(f"{tn}: {val} is not supported: {ts[S_FORMAT][FMT_NAME]}")

    return rval


def check_key(ts, val):
    try:
        return int(val) if isinstance(next(iter(ts[S_DMAP])), int) else val
    except ValueError:
        raise ValueError(f"{ts[S_TDEF][TypeName]}: {val} is not a valid field ID")


def check_range(ts, val):
    op = ts[S_TOPT]
    tn = ts[S_TDEF][TypeName]
    if 'minv' in op and val < op['minv']:
        raise ValueError(f"{tn}: {len(val)} < minimum {op['min']}")

    if 'maxv' in op and val > op['maxv']:
        raise ValueError(f"{tn}: {len(val)} > maximum {op['max']}")


def check_size(ts, val):
    op = ts[S_TOPT]
    tn = ts[S_TDEF][TypeName]
    if 'minv' in op and len(val) < op['minv']:
        raise ValueError(f"{tn}: {len(val)} < minimum {op['minv']}")

    if 'maxv' in op and len(val) > op['maxv']:
        raise ValueError(f"{tn}: {len(val)} > maximum {op['maxv']}")


def extra_value(ts, val, fld):
    td = ts[S_TDEF]
    raise ValueError(f"{td[TypeName]}({td[BaseType]}): unexpected field: {val} not in {fld}:")

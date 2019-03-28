"""
Support functions for JADN codec
Convert dict between nested and flat
Convert typedef options between dict and strings
"""
from functools import reduce
from typing import Any, List, Tuple, Union

from . import jadn_defs


# Dict conversion utilities
def _dmerge(x: dict, y: dict) -> dict:
    k, v = next(iter(y.items()))
    if k in x:
        _dmerge(x[k], v)
    else:
        x[k] = v
    return x


def hdict(keys: str, value: dict, sep: str = ".") -> dict:
    """
    Convert a hierarchical-key value pair to a nested dict
    """
    return reduce(lambda v, k: {k: v}, reversed(keys.split(sep)), value)


def fluff(src: dict, sep: str = ".") -> dict:
    """
    Convert a flat dict with hierarchical keys to a nested dict
    :param src: flat dict - e.g., {"a.b.c": 1, "a.b.d": 2}
    :param sep: separator character for keys
    :return: nested dict - e.g., {"a": {"b": {"c": 1, "d": 2}}}
    """
    return reduce(lambda x, y: _dmerge(x, y), [hdict(k, v, sep) for k, v in src.items()], {})


def flatten(cmd: Any, path: str = "", fc: dict = None, sep: str = ".") -> dict:
    """
    Convert a nested dict to a flat dict with hierarchical keys
    """
    if fc is None:
        fc = {}
    fcmd = fc.copy()
    if isinstance(cmd, dict):
        for k, v in cmd.items():
            k = k.split(":")[1] if ":" in k else k
            fcmd = flatten(v, sep.join((path, k)) if path else k, fcmd)
    elif isinstance(cmd, list):
        for n, v in enumerate(cmd):
            fcmd.update(flatten(v, sep.join([path, str(n)])))
    else:
        fcmd[path] = cmd
    return fcmd


def dlist(src: dict) -> dict:
    """
    Convert dicts with numeric keys to lists
    :param src: {"a": {"b": {"0":"red", "1":"blue"}, "c": "foo"}}
    :return: {"a": {"b": ["red", "blue"], "c": "foo"}}
    """
    if isinstance(src, dict):
        for k in src:
            src[k] = dlist(src[k])
        if set(src) == set([str(k) for k in range(len(src))]):
            src = [src[str(k)] for k in range(len(src))]
    return src


def topts_s2d(ostr: Union[List[str], Tuple[str]]) -> dict:
    """
    Convert list of type definition option strings to options dictionary
    :param ostr: list type options
    :return: key/value type options
    """
    if isinstance(ostr, (list, tuple)):
        # assert len(set(OPTIONS_S2D.TYPE).difference(set(TYPE_D2S.keys()))) == 0
        opts = {}
        for o in ostr:
            try:
                k = jadn_defs.TYPE_OPTIONS[ord(o[0])]
                opts[k] = jadn_defs.OPTIONS_S2D.TYPE[k](o[1:])
            except KeyError:
                raise ValueError(f"Unknown type option: {o}")
        return opts
    else:
        raise TypeError(f"Options given are not list/tuple, given {type(ostr)}")


def topts_d2s(opts: dict) -> List[str]:
    """
    Convert options dictionary to list of option strings
    :param opts: key/value type options
    :return: list field options
    """
    if isinstance(opts, dict):
        ostr = []
        for k, v in opts.items():
            assert k in jadn_defs.OPTIONS_D2S.TYPE, f"Unknown field option '{k}'"
            ostr.append(jadn_defs.OPTIONS_D2S.TYPE[k](v))
        return ostr
    else:
        raise TypeError(f"Options given are not a dict, given {type(opts)}")


def fopts_s2d(ostr: List[str]) -> dict:
    """
    Convert list of field definition option strings to options dictionary
    :param ostr: list field options
    :return: key/value field options
    """
    if isinstance(ostr, (list, tuple)):
        # assert len(set(OPTIONS_S2D.FIELD).difference(set(FIELD_D2S.keys()))) == 0
        opts = {}
        for o in ostr:
            try:
                k = jadn_defs.FIELD_OPTIONS[ord(o[0])]
                opts[k] = jadn_defs.OPTIONS_S2D.FIELD[k](o[1:])
            except KeyError:
                raise ValueError(f"Unknown type option: {o}")
        return opts
    else:
        raise TypeError(f"Options given are not list/tuple, given {type(ostr)}")


def fopts_d2s(opts: dict) -> List[str]:
    """
    Convert options dictionary to list of option strings
    :param opts: key/value field options
    :return: list field options
    """
    if isinstance(opts, dict):
        ostr = []
        for k, v in opts.items():
            assert k in jadn_defs.OPTIONS_D2S.FIELD, f"Unknown field option '{k}'"
            ostr.append(jadn_defs.OPTIONS_D2S.FIELD[k](v))
        return ostr
    else:
        raise TypeError(f"Options given are not a dict, given {type(opts)}")


def basetype(tt: str) -> str:                   # Return base type of derived subtypes
    return tt.rsplit('.')[0]        # Strip off subtype (e.g., .ID)


def multiplicity(minimum: int, maximum: int) -> str:
    if minimum == 1 and maximum == 1:
        return '1'
    return f"{minimum}..{'n' if maximum == 0 else maximum}"

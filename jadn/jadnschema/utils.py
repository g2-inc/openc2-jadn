import base64
import sys

from typing import Any, Type, Union


# Util Classes
class FrozenDict(dict):
    def __init__(self, *args, **kwargs) -> None:
        self._hash = None
        super(FrozenDict, self).__init__(*args, **kwargs)

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash(tuple(sorted(self.items())))  # iteritems() on py2
        return self._hash

    def __getattr__(self, item: str) -> Any:
        return self.get(item, None)

    def __getitem__(self, item: str, default: Any = None) -> Any:
        return self.get(item, default)

    def _immutable(self, *args, **kwargs) -> TypeError:
        raise TypeError('cannot change object - object is immutable')

    __setitem__ = _immutable
    __delitem__ = _immutable
    pop = _immutable
    popitem = _immutable
    clear = _immutable
    update = _immutable
    setdefault = _immutable


# Util Functions
def default_encoding(itm: Any) -> Any:
    """
    Encode the given object/type to the default of the system
    :param itm: object/type to convert to the system default
    :return: system default converted object/type
    """
    tmp = type(itm)()
    if hasattr(tmp, '__iter__') and not isinstance(tmp, (str, int, float)):
        for k in itm:
            ks = toStr(k)
            if isinstance(itm, dict):
                tmp[ks] = default_encoding(itm[k])
            elif isinstance(itm, list):
                tmp.append(default_encoding(k))
            else:
                print(f"Not prepared type: {type(itm[k])}-{itm[k]}")
    elif isinstance(itm, (complex, int, float, object)):
        tmp = itm
    else:
        tmp = toStr(itm)
    return tmp


def isBase64(sb: Union[str, bytes]) -> bool:
    """
    Determine if a given string is valid as base64
    :param sb: string to validate as base64
    :return: bool if base64
    """
    try:
        if isinstance(sb, str):
            # If there's any unicode here, an exception will be thrown and the function will return false
            sb_bytes = bytes(sb, 'ascii')
        elif isinstance(sb, bytes):
            sb_bytes = sb
        else:
            raise ValueError("Argument must be string or bytes")
        return base64.b64encode(base64.b64decode(sb_bytes)) == sb_bytes
    except Exception:
        return False


def toFrozen(d: dict) -> FrozenDict:
    """
    Convert the given dict to a FrozenDict
    :param d: dict to convert
    :return: converted dict as a FrozenDict
    """
    for k in d:
        v = d[k]
        if isinstance(v, dict):
            v = toFrozen(v)
        if isinstance(v, list):
            v = tuple(v)
        d[k] = v

    return FrozenDict(d)


def toStr(s: Any) -> str:
    """
    Convert a given type to a default string
    :param s: item to convert to a string
    :return: converted string
    """
    return s.decode(sys.getdefaultencoding(), 'backslashreplace') if hasattr(s, 'decode') else str(s)


def safe_cast(val: Any, to_type: Type, default: Any = None) -> Any:
    """
    Cast the given value to the goven type safely without an exception being thrown
    :param val: value to cast
    :param to_type: type to cast as
    :param default: default value if casting fails
    :return: casted value or given default/None
    """
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default

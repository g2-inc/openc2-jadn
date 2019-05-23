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
    if isinstance(itm, dict):
        return {toStr(k): default_encoding(v) for k, v in itm}

    elif isinstance(itm, list):
        return [default_encoding(i) for i in itm]

    elif isinstance(itm, tuple):
        tmp = tuple(default_encoding(i) for i in itm)

    elif isinstance(itm, (complex, int, float, object)):
        return itm
    else:
        return toStr(itm)
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


def toFrozen(itm: Union[dict, list, str]) -> Union[FrozenDict, str, tuple]:
    """
    Convert the given item to a frozen format
    :param itm: item to freeze
    :return: converted item as a frozen format
    """
    if isinstance(itm, dict):
        return FrozenDict({k: toFrozen(v) for k, v in itm.items()})
    if isinstance(itm, list):
        return tuple(toFrozen(i) for i in itm)

    return itm


def toThawed(itm: Union[dict, FrozenDict, tuple]) -> Union[dict, list, str]:
    """
    Convert the given item to a thawed format
    :param itm: item to thaw
    :return: converted item as a thawed format
    """
    if isinstance(itm, (dict, FrozenDict)):
        return FrozenDict({k: toThawed(v) for k, v in itm.items()})
    if isinstance(itm, tuple):
        return list(toThawed(i) for i in itm)

    return itm


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
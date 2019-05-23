from . import (
    encode,
    decode
)

from ...utils import FrozenDict


enctab = FrozenDict(  # decode, encode, min encoded type
    # Primitives
    Binary=(decode.binary, encode.binary, str),
    Boolean=(decode.boolean, encode.boolean, bool),
    Integer=(decode.integer, encode.integer, int),
    Null=(decode.null, encode.null, str),
    Number=(decode.number, encode.number, float),
    String=(decode.string, encode.string, str),
    # Structures
    Array=(decode.array, encode.array, list),
    ArrayOf=(decode.array_of, encode.array_of, list),
    Choice=(decode.choice, encode.choice, dict),
    Enumerated=(decode.enumerated, encode.enumerated, int),
    Map=(decode.maprec, encode.maprec, dict),
    MapOf=(decode.map_of, encode.map_of, dict),
    Record=(None, None, None),   # Dynamic values
)

__all__ = [
    "enctab"
]

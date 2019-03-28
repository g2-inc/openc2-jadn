"""
 JADN Definitions

A JSON Abstract Data Notation (JADN) file contains a list of datatype definitions.  Each type definition
has a specified format - a list of four or five columns depending on whether the type is primitive or
structure: (name, base type, type options, type description [, fields]).

For the enumerated type each field definition is a list of three items: (tag, name, description).

For other structure types (array, choice, map, record) each field definition is a list of five items:
(tag, name, type, field options, field description).
"""

from __future__ import unicode_literals

from . import utils

# JADN Datatype Definition columns
TNAME = 0       # Datatype name
TTYPE = 1       # Base type - built-in or defined
TOPTS = 2       # Type options
TDESC = 3       # Type description
FIELDS = 4      # List of fields

# JADN Field Definition columns
FTAG = 0        # Element ID
FNAME = 1       # Element name
EDESC = 2       # Enumerated value description
FTYPE = 2       # Datatype of field
FOPTS = 3       # Field options
FDESC = 4       # Field Description

META_ORDER = ('title', 'module', 'description', 'imports', 'exports', 'patch')

# TODO: Convert to use COLUMN_KEY instead of above key/index
COLUMN_KEYS = utils.FrozenDict(
    # Structures
    Structure=('name', 'type', 'opts', 'desc', 'fields'),
    # Field Definitions
    Enum_Def=('id', 'value', 'desc'),
    Gen_Def=('id', 'name', 'type', 'opts', 'desc')
)

# JADN built-in datatypes
JADN_TYPES = utils.FrozenDict(
    PRIMITIVES=(
        'Binary',
        'Boolean',
        'Integer',
        'Number',
        'Null',
        'String'
    ),
    STRUCTURES=(
        'Array',
        'ArrayOf',      # Special case: instance is a structure but type definition has no fields
        'Choice',
        'Enumerated',
        'Map',
        'MapOf',        # (key type, value type)
        'Record'
    )
)


def is_primitive(vtype):
    return vtype in JADN_TYPES.PRIMITIVES


def is_structure(vtype):
    return vtype in JADN_TYPES.STRUCTURES


def is_builtin(vtype):
    return vtype in JADN_TYPES.PRIMITIVES + JADN_TYPES.STRUCTURES


def column_index(col_type: str, col_name: str) -> int:
    if col_type not in COLUMN_KEYS:
        raise KeyError(f"{col_type} is not a valid column type")

    columns = COLUMN_KEYS[col_type]
    if col_name not in columns:
        raise KeyError(f"{col_name} is not a valid column for {col_type}")

    return columns.index(col_name)


# Option Tags/Keys
#   JADN Type Options (TOPTS) and Field Options (FOPTS) contain a list of strings, each of which is an option.
#   The first character of an option string is the type ID; the remaining characters are the value.
#   The option string is converted into a Name: Value pair before use.
#   The tables list the unicode codepoint of the ID and the corresponding Name.

# TODO: Merge options into field and type dicts?
TYPE_OPTIONS = utils.FrozenDict({        # ID, value type, description
    0x3d: 'compact',    # '=', boolean, Enumerated type and Choice/Map/Record keys are ID not Name
    0x2e: 'cvt',        # '.', string, String conversion and validation function for Binary derived types
    0x40: 'format',     # '@', string, name of validation function, e.g., date-time, email, ipaddr, ...
    0x5b: 'min',        # '[', integer, minimum string length, integer value, array length, property count
    0x5d: 'max',        # ']', integer, maximum string length, integer value, array length, property count
    0x2a: 'rtype',      # '*', string, Enumerated value from referenced type or ArrayOf element type
    0x2b: 'ktype',      # '+', string, Key type for MapOf
    0x24: 'pattern',    # '$', string, regular expression that a string type must match
})

TYPE_OPTIONS_INVERT = utils.FrozenDict(zip(TYPE_OPTIONS.values(), TYPE_OPTIONS.keys()))

FIELD_OPTIONS = utils.FrozenDict({
    0x5b: 'min',        # '[', integer, minimum cardinality of field, default = 1, 0 = field is optional
    0x5d: 'max',        # ']', integer, maximum cardinality of field, default = 1, 0 = inherited max, not 1 = array
    0x25: 'enum',       # '%', boolean, enumeration derived from field type
    0x26: 'atfield',    # '&', string, name of a field that specifies the type of this field
    0x2a: 'rtype',      # '*', string, Enumerated value from referenced type
    0x2f: 'etype',      # '/', string, serializer-specific encoding type, e.g., u8, s16, hex, base64
    0x21: 'default',    # '!', string, default value for this field (coerced to field type)
})

FIELD_OPTIONS_INVERT = utils.FrozenDict(zip(FIELD_OPTIONS.values(), FIELD_OPTIONS.keys()))

SUPPORTED_TYPE_OPTIONS = utils.FrozenDict(
    Binary=('min', 'max', 'format', 'cvt'),
    Boolean=(),
    Integer=('min', 'max', 'format'),
    Number=('min', 'max', 'format'),
    Null=(),
    String=('min', 'max', 'pattern', 'format'),
    Array=('min', 'max', 'cvt'),
    ArrayOf=('min', 'max', 'rtype'),
    Choice=('compact', ),
    Enumerated=('compact', 'rtype'),
    Map=('compact', 'min', 'max'),
    MapOf=('min', 'max', 'ktype', 'rtype'),
    Record=('min', 'max'),
)

SUPPORTED_FIELD_OPTIONS = utils.FrozenDict(
    Binary=('min', 'max'),
    Boolean=('min', 'max'),
    Integer=('min', 'max'),
    Number=('min', 'max'),
    Null=(),
    String=('min', 'max', 'pattern', 'format'),
    Array=('min', 'max', 'etype', 'atfield'),
    ArrayOf=('min', 'max', 'rtype'),
    Choice=('min', 'max', 'etype'),
    Enumerated=('rtype', ),
    Map=('min', 'max', 'etype'),
    Record=('min', 'max', 'etype', 'atfield'),
)

# Option Conversions
OPTIONS_S2D = utils.FrozenDict(
    TYPE=utils.FrozenDict(
        compact=lambda x: True,
        cvt=lambda x: x,
        format=lambda x: x,
        min=lambda x: utils.safe_cast(x, int, 1),
        max=lambda x: utils.safe_cast(x, int, 1),
        ktype=lambda x: x,
        pattern=lambda x: x,
        rtype=lambda x: x
    ),
    FIELD=utils.FrozenDict(
        atfield=lambda x: x,
        default=lambda x: x,
        enum=lambda x: True,
        etype=lambda x: x,
        min=lambda x: utils.safe_cast(x, int, 1),
        max=lambda x: utils.safe_cast(x, int, 1),
        rtype=lambda x: x
    )
)

OPTIONS_D2S = utils.FrozenDict(
    TYPE=utils.FrozenDict(
        compact=lambda x: chr(TYPE_OPTIONS_INVERT.compact),
        cvt=lambda x: f"{chr(TYPE_OPTIONS_INVERT.cvt)}{x}",
        format=lambda x: f"{chr(TYPE_OPTIONS_INVERT.format)}{x}",
        min=lambda x: f"{chr(TYPE_OPTIONS_INVERT.min)}{utils.safe_cast(x, int, 1)}",
        max=lambda x: f"{chr(TYPE_OPTIONS_INVERT.max)}{utils.safe_cast(x, int, 1)}",
        ktype=lambda x: f"{chr(TYPE_OPTIONS_INVERT.ktype)}{x}",
        rtype=lambda x: f"{chr(TYPE_OPTIONS_INVERT.rtype)}{x}",
        pattern=lambda x: f"{chr(TYPE_OPTIONS_INVERT.pattern)}{x}"
    ),
    FIELD=utils.FrozenDict(
        atfield=lambda x: f"{chr(FIELD_OPTIONS_INVERT.atfield)}{x}",
        default=lambda x: f"{chr(FIELD_OPTIONS_INVERT.default)}{x}",
        enum=lambda x: chr(TYPE_OPTIONS_INVERT.enum),
        etype=lambda x: f"{chr(FIELD_OPTIONS_INVERT.etype)}{x}",
        min=lambda x: f"{chr(FIELD_OPTIONS_INVERT.min)}{utils.safe_cast(x, int, 1)}",
        max=lambda x: f"{chr(FIELD_OPTIONS_INVERT.max)}{utils.safe_cast(x, int, 1)}",
        rtype=lambda x: f"{chr(FIELD_OPTIONS_INVERT.rtype)}{x}"
    )
)

# TODO: Combine into single format dict
FORMAT = utils.FrozenDict(
    CHECK=utils.FrozenDict({            # Semantic validation functions
        'email': 'String',      # email address, RFC 5322 Section 3.4.1
        'hostname': 'String',   # host name, RFC 1123 Section 2.1
        'ip-addr': 'Binary',    # length must be 4 octets (IPv4) or 16 octets (IPv6)
        'mac-addr': 'Binary',   # length must be 6 octets (EUI-48) or 8 octets (EUI-64)
        'uri': 'String',        # RFC 3986 Appendix A
    }),
    CONVERT=utils.FrozenDict({          # Binary-String and Array-String conversion functions
        'b': 'Binary',          # Base64url - RFC 4648 Section 5 (default)
        'x': 'Binary',          # Hex - RFC 4648 Section 8
        'ipv4-addr': 'Binary',  # IPv4 text representation - draft-main-ipaddr-text-rep-02 Section 3
        'ipv6-addr': 'Binary',  # IPv6 text representation - RFC 5952 Section 4
        'ipv4-net': 'Array',    # IPv4 Network Address CIDR string - RFC 4632 Section 3.1
        'ipv6-net': 'Array',    # IPv6 Network Address CIDR string - RFC 4291 Section 2.3
    })
)

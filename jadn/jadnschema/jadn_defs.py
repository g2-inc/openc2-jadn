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
TypeName = 0        # Datatype name
BaseType = 1        # Base type - built-in or defined
TypeOptions = 2     # Type options
TypeDesc = 3        # Type description
Fields = 4          # List of fields

# JADN Field Definition columns
FieldID = 0         # Element ID
FieldName = 1       # Element name
EnumDesc = 2        # Enumerated value description
FieldType = 2       # Datatype of field
FieldOptions = 3    # Field options
FieldDesc = 4       # Field Description

META_ORDER = ('title', 'module', 'description', 'imports', 'exports', 'patch')

# TODO: Convert to use COLUMN_KEY instead of above key/index
COLUMN_KEYS = utils.FrozenDict(
    # Structures
    Structure=(
        'name',     # 0 - TNAME - Datatype name
        'type',     # 1 - TTYPE - Base type - built-in or defined
        'opts',     # 2 - TOPTS - Type options
        'desc',     # 3 - TDESC - Type description
        'fields'    # 4 - FIELDS - List of fields
    ),
    # Field Definitions
    Enum_Def=(
        'id',       # 0 - FTAG - Element ID
        'value',    # 1 - FNAME - Element name
        'desc'      # 2 - EDESC - Enumerated value description
    ),
    Gen_Def=(
        'id',       # 0 - FTAG - Element ID
        'name',     # 1 - FNAME - Element name
        'type',     # 2 - FTYPE - Datatype of field
        'opts',     # 3 - FOPTS - Field options
        'desc'      # 4 - FDESC - Field Description
    )
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


def is_builtin(vtype: str) -> bool:
    """
    Determine if the given type is a JADN builtin type
    :param vtype: Type
    :return: is builtin type
    """
    return vtype in JADN_TYPES.PRIMITIVES + JADN_TYPES.STRUCTURES


def is_primitive(vtype: str) -> bool:
    """
    Determine if the given type is a JADN builtin primitive
    :param vtype: Type
    :return: is builtin primitive
    """
    return vtype in JADN_TYPES.PRIMITIVES


def is_structure(vtype: str) -> bool:
    """
    Determine if the given type is a JADN builtin structure
    :param vtype: Type
    :return: is builtin structure
    """
    return vtype in JADN_TYPES.STRUCTURES


def is_compound(vtype: str) -> bool:
    """
    Determine if the given type is a JADN builtin compound (has defined fields)
    :param vtype: Type
    :return: is builtin compound
    """
    return vtype in ('Array', 'Choice', 'Map', 'Record')


def column_index(col_type: str, col_name: str) -> int:
    """
    Get the index of hte column given the type and column name
    :param col_type: type of builtin - (Structure, Gen_Def, Enum_Def)
    :param col_name: name of column
    :return: index number of the column
    """
    if col_type not in COLUMN_KEYS:
        raise KeyError(f"{col_type} is not a valid column type")

    columns = COLUMN_KEYS[col_type]
    if col_name not in columns:
        raise KeyError(f"{col_name} is not a valid column for {col_type}")

    return columns.index(col_name)


# Option Tags/Keys
#   JADN TypeOptions and FieldOptions contain a list of strings, each of which is an option.
#   The first character of an option string is the type ID; the remaining characters are the value.
#   The option string is converted into a Name: Value pair before use.
#   The tables list the unicode codepoint of the ID and the corresponding Name.

# Type Config
TYPE_CONFIG = dict(
    OPTIONS={               # ID, value type, description
        0x3d: 'id',         # '=', none, Enumerated type and Choice/Map/Record keys are ID not Name
        0x2a: 'vtype',      # '*', string, Value type for ArrayOf and MapOf
        0x2b: 'ktype',      # '+', string, Key type for MapOf
        0x24: 'enum',       # '$', string, enumeration derived from the referenced Array/Choice/Map/Record type
        0x2f: 'format',     # '/', string, semantic validation keyword, may affect serialization
        0x25: 'pattern',    # '%', string, regular expression that a string must match
        0x7b: 'minv',       # '{', integer, minimum byte or text string length, numeric value, element count
        0x7d: 'maxv',       # '}', integer, maximum byte or text string length, numeric value, element count
        0x21: 'default',    # '!', string, default value for an instance of this type
    },
    SUPPORTED_OPTIONS=dict(
        # Primitives
        Binary=('minv', 'maxv', 'format'),
        Boolean=(),
        Integer=('minv', 'maxv', 'format'),
        Number=('minv', 'maxv', 'format'),
        Null=(),
        String=('minv', 'maxv', 'pattern', 'format'),
        # Structures
        Array=('format', ),
        ArrayOf=('minv', 'maxv', 'vtype'),
        Choice=('id',),
        Enumerated=('id', 'enum'),
        Map=('id', 'minv', 'maxv'),
        MapOf=('minv', 'maxv', 'ktype', 'rtype'),
        Record=(),
    ),
    S2D=dict(  # Option Conversions - String -> Dict
        id=lambda x: True,
        vtype=lambda x: x,
        ktype=lambda x: x,
        enum=lambda x: x,
        format=lambda x: x,
        pattern=lambda x: x,
        minv=lambda x: utils.safe_cast(x, int, 1),
        maxv=lambda x: utils.safe_cast(x, int, 1),
        default=lambda x: x,
    )
)

TYPE_CONFIG['OPTIONS_INVERT'] = utils.FrozenDict({v: chr(k) for k, v in TYPE_CONFIG['OPTIONS'].items()})
TYPE_CONFIG['D2S'] = dict(
    id=lambda x: TYPE_CONFIG['OPTIONS_INVERT'].id,
    vtype=lambda x: f"{TYPE_CONFIG['OPTIONS_INVERT'].vtype}{x}",
    ktype=lambda x: f"{TYPE_CONFIG['OPTIONS_INVERT'].ktype}{x}",
    enum=lambda x: f"{TYPE_CONFIG['OPTIONS_INVERT'].enum}{x}",
    format=lambda x: f"{TYPE_CONFIG['OPTIONS_INVERT'].format}{x}",
    pattern=lambda x: f"{TYPE_CONFIG['OPTIONS_INVERT'].pattern}{x}",
    minv=lambda x: f"{TYPE_CONFIG['OPTIONS_INVERT'].minv}{utils.safe_cast(x, int, 1)}",
    maxv=lambda x: f"{TYPE_CONFIG['OPTIONS_INVERT'].maxv}{utils.safe_cast(x, int, 1)}",
    default=lambda x: f"{TYPE_CONFIG['OPTIONS_INVERT'].default}{x}",
)
TYPE_CONFIG = utils.toFrozen(TYPE_CONFIG)

# Field Config
FIELD_CONFIG = dict(
    OPTIONS={               # ID, value type, description
        # New Options
        0x5b: 'minc',       # '[', integer, minimum cardinality, default = 1, 0 = field is optional
        0x5d: 'maxc',       # ']', integer, maximum cardinality, default = 1, 0 = inherited max, not 1 = array
        0x26: 'tfield',     # '&', string, field that specifies the type of this field
        0x3c: 'flatten',    # '<', integer, use FieldName as namespace prefix for FieldType, depending on serialization
        # Added Options
        0x2b: 'ktype',      # '+', string, Key type for MapOf
        0x2a: 'vtype',      # '*', string, Value type for ArrayOf and MapOf
        0x2f: 'format',     # '/', string, semantic validation keyword, may affect serialization
        0x24: 'enum',       # '$', string, enumeration derived from the referenced Array/Choice/Map/Record type
    },
    SUPPORTED_OPTIONS=dict(
        # Primitives
        Binary=('minc', 'maxc'),
        Boolean=('minc', 'maxc'),
        Integer=('minc', 'maxc'),
        Number=('minc', 'maxc'),
        Null=(),
        String=('minc', 'maxc', 'pattern', 'format'),
        # Structures
        Array=('minc', 'maxc', 'tfield'),
        ArrayOf=('minc', 'maxc'),
        Choice=('minc', 'maxc'),
        Enumerated=('vtype',),
        Map=('minc', 'maxc'),
        MapOf=('minv', 'maxv', 'ktype', 'vtype'),
        Record=('minc', 'maxc', 'tfield'),
    ),
    S2D=dict(  # Option Conversions - String -> Dict
        minc=lambda x: utils.safe_cast(x, int, 1),
        maxc=lambda x: utils.safe_cast(x, int, 1),
        tfield=lambda x: x,
        flatten=lambda x: x,
        # Added Options
        ktype=lambda x: x,
        vtype=lambda x: x,
        format=lambda x: x,
        enum=lambda x: x,
    )
)
FIELD_CONFIG['OPTIONS_INVERT'] = utils.FrozenDict({v: chr(k) for k, v in FIELD_CONFIG['OPTIONS'].items()})
FIELD_CONFIG['D2S'] = dict(
    minc=lambda x: f"{FIELD_CONFIG['OPTIONS_INVERT'].minc}{utils.safe_cast(x, int, 1)}",
    maxc=lambda x: f"{FIELD_CONFIG['OPTIONS_INVERT'].maxc}{utils.safe_cast(x, int, 1)}",
    tfield=lambda x: f"{FIELD_CONFIG['OPTIONS_INVERT'].tfield}{x}",
    flatten=lambda x: f"{FIELD_CONFIG['OPTIONS_INVERT'].flatten}{x}",
    # Added Options
    ktype=lambda x: f"{FIELD_CONFIG['OPTIONS_INVERT'].ktype}{x}",
    vtype=lambda x: f"{FIELD_CONFIG['OPTIONS_INVERT'].vtype}{x}",
    format=lambda x: f"{FIELD_CONFIG['OPTIONS_INVERT'].format}{x}",
    enum=lambda x: f"{FIELD_CONFIG['OPTIONS_INVERT'].enum}{x}",

)
FIELD_CONFIG = utils.toFrozen(FIELD_CONFIG)

# TODO: Find if this is needed
OPTION_ID = {**TYPE_CONFIG['OPTIONS_INVERT']}
OPTION_ID.update(FIELD_CONFIG['OPTIONS_INVERT'])
OPTION_ID = utils.toFrozen(OPTION_ID)

FORMAT = utils.FrozenDict(
    CHECK=utils.FrozenDict({        # Semantic validation functions
        'email': 'String',          # email address, RFC 5322 Section 3.4.1
        'eui': 'Binary',            # IEEE Extended Unique Identifier, 48 bits or 64 bits
        'hostname': 'String',       # host name, RFC 1123 Section 2.1
        'ipv4-addr': 'Binary',      # IPv4 address as specified in RFC 791 Section 3.1
        'ipv4-net': 'Array',        # Binary IPv4 address and Integer prefix length, RFC 4632 Section 3.1
        'ipv6-addr': 'Binary',      # IPv6 address as specified in RFC 8200 Section 3
        'ipv6-net': 'Array',        # Binary IPv6 address and Integer prefix length, RFC 4291 Section 2.3
        'mac-addr': 'Binary',       # length must be 6 octets (EUI-48) or 8 octets (EUI-64)
        'uri': 'String',            # RFC 3986 Appendix A
    }),
    SERIALIZE=utils.FrozenDict({    # Format options that affect serialization
        'b': 'Binary',              # Base64url - RFC 4648 Section 5 (default text representation of Binary type)
        'eui': 'Binary',            # IEEE Extended Unique Identifier, 48 bits or 64 bits
        'f16': 'Number',            # IEEE 754 Half-Precision Float
        'f32': 'Number',            # IEEE 754 Single-Precision Float
        'ipv4-addr': 'Binary',      # IPv4 "dotted-quad" text representation, RFC 2673 Section 3.2
        'ipv4-net': 'Array',        # IPv4 Network Address CIDR string, RFC 4632 Section 3.1
        'ipv6-addr': 'Binary',      # IPv6 text representation, RFC 4291 Section 2.2
        'ipv6-net': 'Array',        # IPv6 Network Address CIDR string, RFC 4291 Section 2.3
        'x': 'Binary',              # Hex - RFC 4648 Section 8
    })
)

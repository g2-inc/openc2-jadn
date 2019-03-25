from .utils import FrozenDict

# Message Formats for OpenC2
MessageFormats = FrozenDict(
    CBOR='cbor',
    JSON='json',
    XML='xml',
    # Proto='proto',
    YAML='yaml'
)

# Schema Formats for OpenC2
SchemaFormats = FrozenDict(
    CDDL='cddl',
    HTML='html',
    JADN='jadn',
    JAS='jas',
    MARKDOWN='md',
    PROTOBUF='proto',
    RELAX='relax',
    THRIFT='thrift'
)

# Conversion Comment Level
CommentLevels = FrozenDict(
    ALL='all',
    NONE='none'
)

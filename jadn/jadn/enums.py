from .utils import FrozenDict

# Message Formats for OpenC2
OpenC2MessageFormats = FrozenDict(
    CBOR='cbor',
    JSON='json',
    PROTO='proto',
    XML='xml',
)

# Schema Formats for OpenC2
OpenC2SchemaFormats = FrozenDict(
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
import json
import os

from jadnschema.enums import CommentLevels
from jadnschema.convert import (
    cddl_dump,
    cddl_load,
    html_dump,
    md_dump,
    proto_dump,
    proto_load,
    relax_dump,
    relax_load,
    thrift_dump,
    thrift_load,
    jas_dump,
    jas_load,
    json_dump,
    json_load
)
# from libs.schema import relax2jadn_dump, proto2jadn_dump, cddl2jadn_dump, thrift2jadn_dump

schema = 'oc2ls-csdpr02'
base_schema = 'schema/{}.jadn'.format(schema)
test_dir = 'schema_gen_test'

if not os.path.isdir(test_dir):
    os.makedirs(test_dir)

schema_json = json.loads(open(base_schema, 'rb').read())

# TODO: Add CommentLevels, requires dump.py rewrite
jas_dump(schema_json, os.path.join(test_dir, schema + '.jas'))
jas_load(open(os.path.join(test_dir, schema + '.jas'), 'rb').read(), os.path.join(test_dir, schema + '.jas.jadn'))

proto_dump(schema_json, os.path.join(test_dir, schema + '.all.proto'), comm=CommentLevels.ALL)
proto_dump(schema_json, os.path.join(test_dir, schema + '.none.proto'), comm=CommentLevels.NONE)
proto_load(open(os.path.join(test_dir, schema + '.all.proto'), 'rb').read(), os.path.join(test_dir, schema + '.proto.jadn'))

json_dump(schema_json, os.path.join(test_dir, schema + '.all.json'), comm=CommentLevels.ALL)
json_dump(schema_json, os.path.join(test_dir, schema + '.none.json'), comm=CommentLevels.NONE)
json_load(open(os.path.join(test_dir, schema + '.all.json'), 'rb').read(), os.path.join(test_dir, schema + '.all.jadn'))

cddl_dump(schema_json, os.path.join(test_dir, schema + '.all.cddl'), comm=CommentLevels.ALL)
cddl_dump(schema_json, os.path.join(test_dir, schema + '.none.cddl'), comm=CommentLevels.NONE)
cddl_load(open(os.path.join(test_dir, schema + '.all.cddl'), 'rb').read(), os.path.join(test_dir, schema + '.cddl.jadn'))

relax_dump(schema_json, os.path.join(test_dir, schema + '.all.rng'), comm=CommentLevels.ALL)
relax_dump(schema_json, os.path.join(test_dir, schema + '.none.rng'), comm=CommentLevels.NONE)
relax_load(open(os.path.join(test_dir, schema + '.all.rng'), 'rb').read(), os.path.join(test_dir, schema + '.rng.jadn'))

thrift_dump(schema_json, os.path.join(test_dir, schema + '.all.thrift'), comm=CommentLevels.ALL)
thrift_dump(schema_json, os.path.join(test_dir, schema + '.none.thrift'), comm=CommentLevels.NONE)
thrift_load(open(os.path.join(test_dir, schema + '.all.thrift'), 'rb').read(), os.path.join(test_dir, schema + '.thrift.jadn'))

md_dump(schema_json, os.path.join(test_dir, schema + '.md'))

html_dump(schema_json, os.path.join(test_dir, schema + '.html'))

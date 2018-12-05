import json
import os

from libs.enums import CommentLevels
from libs.convert import cddl_dump, html_dump, md_dump, proto_dump, relax_dump, thrift_dump
from libs.schema import relax2jadn_dump, proto2jadn_dump, cddl2jadn_dump, thrift2jadn_dump

schema = 'oc2ls-csdpr01'
base_schema = 'schema/{}.jadn'.format(schema)
test_dir = 'schema_gen_test'

if not os.path.isdir(test_dir):
    os.makedirs(test_dir)

schema_json = json.loads(open(base_schema, 'rb').read())

proto_dump(schema_json, os.path.join(test_dir, schema + '.all.proto'), comm=CommentLevels.ALL)
proto_dump(schema_json, os.path.join(test_dir, schema + '.none.proto'), comm=CommentLevels.NONE)
proto2jadn_dump(open(os.path.join(test_dir, schema + '.all.proto'), 'rb').read(), os.path.join(test_dir, schema + '.proto.jadn'))

cddl_dump(schema_json, os.path.join(test_dir, schema + '.all.cddl'), comm=CommentLevels.ALL)
cddl_dump(schema_json, os.path.join(test_dir, schema + '.none.cddl'), comm=CommentLevels.NONE)
cddl2jadn_dump(open(os.path.join(test_dir, schema + '.all.cddl'), 'rb').read(), os.path.join(test_dir, schema + '.cddl.jadn'))

relax_dump(schema_json, os.path.join(test_dir, schema + '.all.rng'), comm=CommentLevels.ALL)
relax_dump(schema_json, os.path.join(test_dir, schema + '.none.rng'), comm=CommentLevels.NONE)
relax2jadn_dump(open(os.path.join(test_dir, schema + '.all.rng'), 'rb').read(), os.path.join(test_dir, schema + '.rng.jadn'))

thrift_dump(schema_json, os.path.join(test_dir, schema + '.all.thrift'), comm=CommentLevels.ALL)
thrift_dump(schema_json, os.path.join(test_dir, schema + '.none.thrift'), comm=CommentLevels.NONE)
thrift2jadn_dump(open(os.path.join(test_dir, schema + '.all.thrift'), 'rb').read(), os.path.join(test_dir, schema + '.thrift.jadn'))

md_dump(schema_json, os.path.join(test_dir, schema + '.md'))

html_dump(schema_json, os.path.join(test_dir, schema + '.html'))

import json
import os

from libs.convert import cddl_dump, html_dump, md_dump, proto_dump, relax_dump, thrift_dump
from libs.schema import relax2jadn_dump, proto2jadn_dump, cddl2jadn_dump, thrift2jadn_dump

schema = 'openc2_wd08_functional'
base_schema = 'schema/{}.jadn'.format(schema)
test_dir = 'schema_gen_test'

if not os.path.isdir(test_dir):
    os.makedirs(test_dir)

schema_json = json.loads(open(base_schema, 'rb').read())

proto_dump(schema_json, os.path.join(test_dir, schema + '.proto'))
proto2jadn_dump(open(os.path.join(test_dir, schema + '.proto'), 'rb').read(), os.path.join(test_dir, schema + '.proto.jadn'))

# cddl_dump(schema_json, os.path.join(test_dir, schema + '.cddl'))
# cddl2jadn_dump(open(os.path.join(test_dir, schema + '.cddl'), 'rb').read(), os.path.join(test_dir, schema + '.cddl.jadn'))

relax_dump(schema_json, os.path.join(test_dir, schema + '.rng'))
relax2jadn_dump(open(os.path.join(test_dir, schema + '.rng'), 'rb').read(), os.path.join(test_dir, schema + '.rng.jadn'))

thrift_dump(schema_json, os.path.join(test_dir, schema + '.thrift'))
thrift2jadn_dump(open(os.path.join(test_dir, schema + '.thrift'), 'rb').read(), os.path.join(test_dir, schema + '.thrift.jadn'))

md_dump(schema_json, os.path.join(test_dir, schema + '.md'))

html_dump(schema_json, os.path.join(test_dir, schema + '.html'))

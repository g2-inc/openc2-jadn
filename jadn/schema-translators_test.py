import json
import os

from jadn.enums import CommentLevels
from jadn.convert import (
    json_dump,
    json_dumps
)
# from libs.schema import relax2jadn_dump, proto2jadn_dump, cddl2jadn_dump, thrift2jadn_dump

schema = 'oc2ls-csdpr02'
base_schema = 'schema/{}.jadn'.format(schema)
test_dir = 'schema_gen_test'

if not os.path.isdir(test_dir):
    os.makedirs(test_dir)

schema_json = json.loads(open(base_schema, 'rb').read())

# TODO: Add CommentLevels, requires dump.py rewrite
json_dump(schema_json, os.path.join(test_dir, schema + '.all.json'), comm=CommentLevels.ALL)
json_dump(schema_json, os.path.join(test_dir, schema + '.none.json'), comm=CommentLevels.NONE)

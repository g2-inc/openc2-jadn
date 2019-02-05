import json
import os
import re

from jadn.enums import CommentLevels
from jadn.convert import (
    json_dump,
    json_load
)
# from jadn.schema import relax2jadn_dump, proto2jadn_dump, cddl2jadn_dump, thrift2jadn_dump


schema = 'oc2ls-csdpr02_reorg'
base_schema = 'schema/{}.jadn'.format(schema)
test_dir = 'schema_gen_test'

if not os.path.isdir(test_dir):
    os.makedirs(test_dir)


def escape_replace(match):
    orig = match.string
    match_str = match.group()
    if orig[match.start()-1] == '\\' or orig[match.end()] == '\\':
        return match_str
    else:
        return f'{match_str}\\'


with open(base_schema, 'rb') as jadn_file:
    jadn = str(jadn_file.read(), 'utf-8')
    jadn = re.sub(r'\\', escape_replace, jadn)

    schema_json = json.loads(jadn)

'''
with open(base_schema, 'w+') as jadn_file:
    from jadn.utils import jadn_format
    jadn_file.write(jadn_format(schema_json))
'''


# TODO: Add CommentLevels, requires dump.py rewrite
print('Convert to JSON Schema - All Comments')
json_dump(schema_json, os.path.join(test_dir, schema + '.all.json'), comm=CommentLevels.ALL)

# print('\nConvert to JSON Schema - No Comments')
# json_dump(schema_json, os.path.join(test_dir, schema + '.none.json'), comm=CommentLevels.NONE)

# print('\nConvert to JADN Schema from JSON Schema - All Comments')
# json_load(open(os.path.join(test_dir, schema + '.all.json'), 'rb').read(), os.path.join(test_dir, schema + '.all.json.jadn'))

# print('\nConvert to JADN Schema from JSON Schema - No Comments')
# json_load(open(os.path.join(test_dir, schema + '.none.json'), 'rb').read(), os.path.join(test_dir, schema + '.none.json.jadn'))

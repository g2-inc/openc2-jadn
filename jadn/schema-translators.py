import glob
import json
import os
import pprint
import sys
import xmltodict

from lxml import etree

convert = True

if convert:
    from libs.convert import base_dump, cddl_dump, proto_dump, relax_dump, thrift_dump

    schema = 'schema/openc2-wd06_functional.jadn'
    test_dir = 'schema_gen_test'
    if not os.path.isdir(test_dir):
        os.makedirs(test_dir)

    with open(schema, 'rb') as r:
        schema_json = json.loads(r.read())

    proto_dump(schema_json, os.path.join(test_dir, 'openc2-wd06.proto'))

    cddl_dump(schema_json, os.path.join(test_dir, 'openc2-wd06.cddl'))

    relax_dump(schema_json, os.path.join(test_dir, 'openc2-wd06.rng'))

    thrift_dump(schema_json, os.path.join(test_dir, 'openc2-wd06.thrift'))

    base_dump(schema_json, os.path.join(test_dir, 'openc2-wd06.md'), form='markdown')

    base_dump(schema_json, os.path.join(test_dir, 'openc2-wd06.html'), form='html')

else:
    if sys.version_info.major >= 3:
        from io import StringIO
    elif sys.version_info.major >= 2:
        from StringIO import StringIO

    with open('test_openc2-wd06.rng', 'rb') as r:
        relax_schema = StringIO(r.read())
        relaxng = etree.RelaxNG(etree.parse(relax_schema))

    for f in glob.glob('message/*.xml'):
        print(f)
        with open(f, 'rb') as r:
            doc = etree.parse(StringIO(r.read()))

            try:
                print('Validating: {}'.format(f))
                relaxng.assertValid(doc)
                print('Valid Message')
                pprint.pprint(json.loads(json.dumps(xmltodict.parse(etree.tostring(doc)))))
            except Exception as e:
                print('Error: {}'.format(e))
        print('')

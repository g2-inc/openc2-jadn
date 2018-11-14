# This Python file uses the following encoding: utf-8
from __future__ import unicode_literals

import os
import unittest

from libs.codec.codec import Codec
from libs.codec.jadn import jadn_load, jadn_analyze


class Language(unittest.TestCase):

    def setUp(self):
        fn = os.path.join('schema', 'openc2-wd09_merged.jadn')
        schema = jadn_load(fn)
        sa = jadn_analyze(schema)
        if sa['undefined']:
            print('Warning - undefined:', sa['undefined'])
        self.tc = Codec(schema, verbose_rec=True, verbose_str=True)

    mredirect = {'action': 'redirect', 'target': {'url': 'http://evil.com'}, 'args': {''}}

    mq1 = {'action': 'query', 'target': {'features': ['versions']}}
    mq2 = {'action': 'query', 'target': {'features': ['profiles']}}

    def test_query_oc2(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.mq1), self.mq1)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.mq1), self.mq1)
        self.assertEqual(self.tc.encode('OpenC2-Command', self.mq2), self.mq2)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.mq2), self.mq2)
#        with self.assertRaises(TypeError):
#            self.tc.encode('OpenC2-Command', self.mq_bad1)
#        with self.assertRaises(TypeError):
#            self.tc.decode('OpenC2-Command', self.mq_bad1)

    mr1 = {'status': 200}
    mr2 = {'status': 200,
           'status_text': 'The request has succeeded',
           'versions': ['foo']
        }

    def test_response_oc2(self):
        self.assertEqual(self.tc.encode('OpenC2-Response', self.mr1), self.mr1)
        self.assertEqual(self.tc.decode('OpenC2-Response', self.mr1), self.mr1)
        self.assertEqual(self.tc.encode('OpenC2-Response', self.mr2), self.mr2)
        self.assertEqual(self.tc.decode('OpenC2-Response', self.mr2), self.mr2)

    mex2c = {
        'action': 'query',
        'target': {
            'properties': ['battery_percentage']
        }
    }

    mex2r = {
        'kvps': [['battery_percentage', '0.577216']]
    }

    def test_properties_cmd(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.mex2c), self.mex2c)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.mex2c), self.mex2c)

    def test_properties_rsp(self):
        self.assertEqual(self.tc.encode('OpenC2-Response', self.mex2r), self.mex2r)
        self.assertEqual(self.tc.decode('OpenC2-Response', self.mex2r), self.mex2r)

    mex3c = {
        'action': 'query',
        'target': {
            'features': ['versions', 'profiles']
        }
    }

    mex3r = {
        "status_text": 'ACME Corp Stateless Packet Filter Appliance',
        'versions': ['1.0'],
        'profiles': [
            'oasis-open.org/openc2/v1.0/ap-slpf'
        ]
    }

    def test_features_cmd(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.mex3c), self.mex3c)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.mex3c), self.mex3c)

    def test_features_rsp(self):
        self.assertEqual(self.tc.encode('OpenC2-Response', self.mex3r), self.mex3r)
        self.assertEqual(self.tc.decode('OpenC2-Response', self.mex3r), self.mex3r)


class SLPF(unittest.TestCase):

    def setUp(self):
        fn = os.path.join('schema', 'openc2-wd09-slpf_merged.jadn')
        schema = jadn_load(fn)
        sa = jadn_analyze(schema)
        if sa['undefined']:
            print('Warning - undefined:', sa['undefined'])
        self.tc = Codec(schema, verbose_rec=True, verbose_str=True)

    mdeny1c = {
      'action': 'deny',
      'target': {
        'ip_connection': {
          'protocol': 'tcp',
          'src_addr': b'\x01\x02\x03\x04',
          'src_port': 10996,
          'dst_addr': b'\xc6\x02\x03\x04',
          'dst_port': 80
        }
      },
      'args': {
        'start_time': 1534775460000,
        'duration': 500,
        'response_requested': 'ack',
        'slpf': {
          'drop_process': 'none'
        }
      },
      'actuator': {
        'slpf': {
          'asset_id': '30'
        }
      }
    }

    mdeny1c_s = {
      'action': 'deny',
      'target': {
        'ip_connection': {
          'protocol': 'tcp',
          'src_addr': 'AQIDBA',
          'src_port': 10996,
          'dst_addr': 'xgIDBA',
          'dst_port': 80
        }
      },
      'args': {
        'start_time': 1534775460000,
        'duration': 500,
        'response_requested': 'ack',
        'slpf': {
          'drop_process': 'none'
        }
      },
      'actuator': {
        'slpf': {
          'asset_id': '30'
        }
      }
    }

    mdeny1r = {
      'status': 200
    }

    mdeny2c = {
      'action': 'deny',
      'target': {
        'ip_connection': {
          'protocol': 'tcp',
          'src_port': 21
        }
      },
      'args': {
        'slpf': {
          'drop_process': 'false_ack'
        }
      },
      'actuator': {
        'slpf': {}
      }
    }

    mdeny2r1 = {'status':200}
    mdeny2r2 = {
      'status': 400,
      'status_text': 'Validation Error: Target: ip_conection'
    }
    mdeny2r3 = {
      'status': 501
    }

    mdeny3c = {
      'action': 'deny',
      'target': {
        'ip_addr': b'\x01\x02\x03\x04'
      },
      'args': {
        'response_requested': 'none',
        'slpf': {
          'direction': 'ingress'
        }
      },
      'actuator': {
        'slpf': {
          'named_group': 'perimeter'
        }
      }
    }

    mdeny3c_s = {
      'action': 'deny',
      'target': {
        'ip_addr': 'AQIDBA'
      },
      'args': {
        'response_requested': 'none',
        'slpf': {
          'direction': 'ingress'
        }
      },
      'actuator': {
        'slpf': {
          'named_group': 'perimeter'
        }
      }
    }

    mdeny4c = {
      'action': 'allow',
      'target': {
        'ip_connection': {
          'protocol': 'tcp',
          'dst_addr': b'\xc6\x33\x64\x11',
          'src_port': 21
        }
      },
      'actuator': {
        'slpf': {}
      }
    }


    mdeny4c_s = {
      'action': 'allow',
      'target': {
        'ip_connection': {
          'protocol': 'tcp',
          'dst_addr': 'xjNkEQ',
          'src_port': 21
        }
      },
      'actuator': {
        'slpf': {}
      }
    }


    mdeny4r = {
      'status': 200,
      'slpf': {
        'rule_number': 1234
      }
    }

    mdelete1c = {
      'action': 'delete',
      'target': {
        'slpf': {
          'rule_number': 1234
        }
      },
      'args': {
        'response_requested': 'complete'
      },
      'actuator': {
        'slpf': {}
      }
    }

    mupdate1c = {
      'action': 'update',
      'target': {
        'file': {
          'path': '\\\\someshared-drive\\somedirectory\\configurations',
          'name': 'firewallconfiguration.txt'
        }
      },
      'actuator': {
        'slpf': {
          'named_group': 'network'
        }
      }
    }

    mupdate1r1 = {'status':200}
    mupdate1r2 = {
      'status': 501,
      'status_text': 'Update-File Not Implemented'
    }
    mupdate1r3 = {
      'status': 500,
      'status_text': 'Server error, Cannot access file'
    }

    mquery1c = {
      'action': 'query',
      'target': {
        'features': []
      }
    }

    mquery1r = {'status':200}

    mquery2c = {
      'action': 'query',
      'target': {
        'features': ['versions']
      }
    }

    mquery2r = {
      'status': 200,
      'versions': ['1.3']
    }

    mquery3c = {
      'action': 'query',
      'target': {
        'features': ['versions', 'profiles']
      }
    }

    mquery3r = {
      'status': 200,
      'versions': ['1.3'],
      'profiles': [
        'oasis-open.org/openc2/v1.0/ap-slpf',
        'example.com/openc2/products/iot-toaster'
      ]
    }

    mquery4c = {
      'action': 'query',
      'target': {
        'features': ['pairs']
      }
    }

    mquery4r = {
        'status': 200,
        'schema': {
            'meta': {
                'module': 'oasis-open.org/openc2/v1.0/openc2-lang',
                'patch': 'wd08-slpf-VendorX',
                'title': 'OpenC2 Language Objects',
                'description': 'OpenC2 Language supported by Vendor X SLPF.',
                'exports': ['OpenC2-Command', 'OpenC2-Response']
            },
            'types': [
                ['OpenC2-Command', 'Record', [], '', [
                    [1, 'action', 'Action', [], ''],
                    [2, 'target', 'Target', [], ''],
                    [3, 'actuator', 'Actuator', ['[0'], ''],
                    [4, 'args', 'Args', ['[0'], ''],
                    [5, 'id', 'Command-ID', ['[0'], '']]
                 ],
                ['Action', 'Enumerated', [], '', [
                    [3, 'query', ''],
                    [6, 'deny', ''],
                    [8, 'allow', ''],
                    [16, 'update', ''],
                    [20, 'delete', '']]
                 ],
                ['Target', 'Choice', [], '', [
                    [10, 'file', 'File', [], ''],
                    [11, 'ip_addr', 'IP-Addr', [], ''],
                    [15, 'ip_connection', 'IP-Connection', [], ''],
                    [16, 'openc2', 'OpenC2', [], ''],
                    [1024, 'slpf', 'slpf:Target', [], '']]
                 ],
                ['Actuator', 'Choice', [], '', [
                    [1024, 'slpf', 'slpf:Specifiers', [], '']]
                 ],
                ['Args', 'Map', [], '', [
                    [1, 'start_time', 'Date-Time', ['[0'], ''],
                    [2, 'stop_time', 'Date-Time', ['[0'], ''],
                    [3, 'duration', 'Duration', ['[0'], ''],
                    [4, 'response_requested', 'Response-Type', ['[0'], ''],
                    [1024, 'slpf', 'slpf:Args', ['[0'], '']]
                 ],
                ['OpenC2-Response', 'Record', [], '', [
                    [1, 'status', 'Status-Code', [], ''],
                    [2, 'status_text', 'String', ['[0'], ''],
                    [3, '*', 'Results', ['[0'], ''],
                    [4, 'id', 'Command-ID', ['[0'], ''],
                    [5, 'id_ref', 'Command-ID', ['[0'], ''],
                    [6, 'actuator_id', 'String', ['[0'], '']]
                 ],
                ['Status-Code', 'Enumerated', ['='], '', [
                    [102, 'Processing', ''],
                    [200, 'OK', ''],
                    [301, 'Moved Permanently', ''],
                    [400, 'Bad Request', ''],
                    [401, 'Unauthorized', ''],
                    [403, 'Forbidden', ''],
                    [500, 'Server Error', ''],
                    [501, 'Not Implemented', '']]
                 ],
                ['File', 'Map', [], '', [
                    [1, 'name', 'String', ['[0'], ''],
                    [2, 'path', 'String', ['[0'], ''],
                    [3, 'hashes', 'Hashes', ['[0'], '']]
                 ],
                ['IP-Addr', 'Binary', [], ''],
                ['IP-Connection', 'Record', [], '', [
                    [1, 'src_addr', 'IP-Addr', ['[0'], ''],
                    [2, 'src_port', 'Port', ['[0'], ''],
                    [3, 'dst_addr', 'IP-Addr', ['[0'], ''],
                    [4, 'dst_port', 'Port', ['[0'], ''],
                    [5, 'protocol', 'L4-Protocol', ['[0'], '']]
                 ],
                ['OpenC2', 'ArrayOf', ['*Query-Item', '[0', ']3'], ''],
                ['Command-ID', 'String', [], ''],
                ['Date-Time', 'Integer', [], ''],
                ['Duration', 'Integer', [], ''],
                ['Hashes', 'Map', [], '', [
                    [1, 'md5', 'Binary', ['[0'], ''],
                    [4, 'sha1', 'Binary', ['[0'], ''],
                    [6, 'sha256', 'Binary', ['[0'], '']]
                 ],
                ['L4-Protocol', 'Enumerated', [], '', [
                    [1, 'icmp', ''],
                    [6, 'tcp', ''],
                    [17, 'udp', ''],
                    [132, 'sctp', '']]
                 ],
                ['Port', 'String', ['@port'], ''],
                ['Query-Item', 'Enumerated', [], '', [
                    [1, 'versions', ''],
                    [2, 'profiles', ''],
                    [3, 'schema', ''],
                    [4, 'pairs', '']]
                 ],
                ['Response-Type', 'Enumerated', [], '', [
                    [0, 'none', ''],
                    [1, 'ack', ''],
                    [2, 'status', ''],
                    [3, 'complete', '']]
                 ],
                ['Version', 'String', [], ''],
                ['Results', 'Map', [], '', [
                    [4, 'versions', 'Version', ['[0', ']0'], ''],
                    [5, 'profiles', 'jadn:Uname', ['[0', ']0'], ''],
                    [6, 'schema', 'jadn:Schema', ['[0', ']0'], ''],
                    [7, 'pairs', 'ActionTargets', ['[0', ']0'], ''],
                    [1024, 'slpf', 'slpf:Results', ['[0', ']0'], '']]
                 ],
                ['ActionTargets', 'Array', [], '', [
                    [1, 'action', 'Action', [], ''],
                    [2, 'targets', 'Target.*', [']0'], '']]
                 ],

                ['slpf:Target', 'Choice', [], '', [
                    [1, 'rule_number', 'slpf:Rule-ID', [], '']]
                 ],
                ['slpf:Args', 'Map', [], '', [
                    [1, 'drop_process', 'slpf:Drop-Process', ['[0'], ''],
                    [2, 'running', 'Boolean', ['[0'], ''],
                    [3, 'direction', 'slpf:Direction', ['[0'], ''],
                    [4, 'insert_rule', 'slpf:Rule-ID', ['[0'], '']]
                 ],
                ['slpf:Drop-Process', 'Enumerated', [], '', [
                    [1, 'none', ''],
                    [2, 'reject', ''],
                    [3, 'false_ack', '']]
                 ],
                ['slpf:Direction', 'Enumerated', [], '', [
                    [1, 'ingress', ''],
                    [2, 'egress', '']]
                 ],
                ['slpf:Rule-ID', 'Integer', [], ''],
                ['slpf:Specifiers', 'Map', [], '', [
                    [1, 'hostname', 'String', ['[0'], ''],
                    [2, 'named_group', 'String', ['[0'], ''],
                    [3, 'asset_id', 'String', ['[0'], ''],
                    [4, 'asset_tuple', 'String', ['[0', ']10'], '']]
                 ],
                ['slpf:Results', 'Map', [], '', [
                    [1, 'rule_number', 'slpf:Rule-ID', ['[0'], '']]
                 ],

                ['jadn:Schema', 'Record', [], '', [
                    [1, 'meta', 'jadn:Meta', [], ''],
                    [2, 'types', 'jadn:Type', [']0'], '']]
                 ],
                ['jadn:Meta', 'Map', [], '', [
                    [1, 'module', 'jadn:Uname', [], ''],
                    [2, 'patch', 'String', ['[0'], ''],
                    [3, 'title', 'String', ['[0'], ''],
                    [4, 'description', 'String', ['[0'], ''],
                    [5, 'imports', 'jadn:Import', ['[0', ']0'], ''],
                    [6, 'exports', 'jadn:Identifier', ['[0', ']0'], ''],
                    [7, 'bounds', 'jadn:Bounds', ['[0'], '']]
                 ],
                ['jadn:Import', 'Array', [], '', [
                    [1, 'nsid', 'jadn:Nsid', [], ''],
                    [2, 'uname', 'jadn:Uname', [], '']]
                 ],
                ['jadn:Bounds', 'Array', [], '', [
                    [1, 'max_msg', 'Integer', [], ''],
                    [2, 'max_str', 'Integer', [], ''],
                    [3, 'max_bin', 'Integer', [], ''],
                    [4, 'max_fields', 'Integer', [], '']]
                 ],
                ['jadn:Type', 'Array', [], '', [
                    [1, 'tname', 'jadn:Identifier', [], ''],
                    [2, 'btype', 'jadn:JADN-Type', ['*'], ''],
                    [3, 'opts', 'jadn:Option', [']0'], ''],
                    [4, 'desc', 'String', [], ''],
                    [5, 'fields', 'jadn:JADN-Type', ['&btype', ']0'], '']]
                 ],
                ['jadn:JADN-Type', 'Choice', ['='], '', [
                    [1, 'Binary', 'Null', [], ''],
                    [2, 'Boolean', 'Null', [], ''],
                    [3, 'Integer', 'Null', [], ''],
                    [4, 'Number', 'Null', [], ''],
                    [5, 'Null', 'Null', [], ''],
                    [6, 'String', 'Null', [], ''],
                    [7, 'Array', 'jadn:FullField', [']0'], ''],
                    [8, 'ArrayOf', 'Null', [], ''],
                    [9, 'Choice', 'jadn:FullField', [']0'], ''],
                    [10, 'Enumerated', 'jadn:EnumField', [']0'], ''],
                    [11, 'Map', 'jadn:FullField', [']0'], ''],
                    [12, 'Record', 'jadn:FullField', [']0'], '']]
                 ],
                ['jadn:EnumField', 'Array', [], '', [
                    [1, '', 'Integer', [], ''],
                    [2, '', 'String', [], ''],
                    [3, '', 'String', [], '']]
                 ],
                ['jadn:FullField', 'Array', [], '', [
                    [1, '', 'Integer', [], ''],
                    [2, '', 'jadn:Identifier', [], ''],
                    [3, '', 'jadn:Identifier', [], ''],
                    [4, '', 'jadn:Options', [], ''],
                    [5, '', 'String', [], '']]
                 ],
                ['jadn:Identifier', 'String', ['$^[a-zA-Z][\\w-]*$', '[1', ']32'], ''],
                ['jadn:Nsid', 'String', ['$^[a-zA-Z][\\w-]*$', '[1', ']8'], ''],
                ['jadn:Uname', 'String', ['[1', ']100'], ''],
                ['jadn:Options', 'ArrayOf', ['*jadn:Option', '[0', ']0'], ''],
                ['jadn:Option', 'String', ['[1', ']100'], '']
            ]
        }
    }

    def test_deny1c(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.mdeny1c), self.mdeny1c_s)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.mdeny1c_s), self.mdeny1c)

    def test_deny1r(self):
        self.assertEqual(self.tc.encode('OpenC2-Response', self.mdeny1r), self.mdeny1r)
        self.assertEqual(self.tc.decode('OpenC2-Response', self.mdeny1r), self.mdeny1r)

    def test_deny2c(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.mdeny2c), self.mdeny2c)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.mdeny2c), self.mdeny2c)

    def test_deny2r(self):
        self.assertEqual(self.tc.encode('OpenC2-Response', self.mdeny2r1), self.mdeny2r1)
        self.assertEqual(self.tc.decode('OpenC2-Response', self.mdeny2r1), self.mdeny2r1)
        self.assertEqual(self.tc.encode('OpenC2-Response', self.mdeny2r2), self.mdeny2r2)
        self.assertEqual(self.tc.decode('OpenC2-Response', self.mdeny2r2), self.mdeny2r2)
        self.assertEqual(self.tc.encode('OpenC2-Response', self.mdeny2r3), self.mdeny2r3)
        self.assertEqual(self.tc.decode('OpenC2-Response', self.mdeny2r3), self.mdeny2r3)

    def test_deny3c(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.mdeny3c), self.mdeny3c_s)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.mdeny3c_s), self.mdeny3c)

    def test_deny4c(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.mdeny4c), self.mdeny4c_s)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.mdeny4c_s), self.mdeny4c)

    def test_deny4r(self):
        self.assertEqual(self.tc.encode('OpenC2-Response', self.mdeny4r), self.mdeny4r)
        self.assertEqual(self.tc.decode('OpenC2-Response', self.mdeny4r), self.mdeny4r)

    def test_delete1c(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.mdelete1c), self.mdelete1c)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.mdelete1c), self.mdelete1c)

    def test_update1c(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.mupdate1c), self.mupdate1c)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.mupdate1c), self.mupdate1c)

    def test_update1r(self):
        self.assertEqual(self.tc.encode('OpenC2-Response', self.mupdate1r1), self.mupdate1r1)
        self.assertEqual(self.tc.decode('OpenC2-Response', self.mupdate1r1), self.mupdate1r1)
        self.assertEqual(self.tc.encode('OpenC2-Response', self.mupdate1r2), self.mupdate1r2)
        self.assertEqual(self.tc.decode('OpenC2-Response', self.mupdate1r2), self.mupdate1r2)
        self.assertEqual(self.tc.encode('OpenC2-Response', self.mupdate1r3), self.mupdate1r3)
        self.assertEqual(self.tc.decode('OpenC2-Response', self.mupdate1r3), self.mupdate1r3)

    def test_query1c(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.mquery1c), self.mquery1c)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.mquery1c), self.mquery1c)

    def test_query1r(self):
        self.assertEqual(self.tc.encode('OpenC2-Response', self.mquery1r), self.mquery1r)
        self.assertEqual(self.tc.decode('OpenC2-Response', self.mquery1r), self.mquery1r)

    def test_query2c(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.mquery2c), self.mquery2c)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.mquery2c), self.mquery2c)

    def test_query2r(self):
        self.assertEqual(self.tc.encode('OpenC2-Response', self.mquery2r), self.mquery2r)
        self.assertEqual(self.tc.decode('OpenC2-Response', self.mquery2r), self.mquery2r)

    def test_query3c(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.mquery3c), self.mquery3c)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.mquery3c), self.mquery3c)

    def test_query3r(self):
        self.assertEqual(self.tc.encode('OpenC2-Response', self.mquery3r), self.mquery3r)
        self.assertEqual(self.tc.decode('OpenC2-Response', self.mquery3r), self.mquery3r)

    def test_query4c(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.mquery4c), self.mquery4c)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.mquery4c), self.mquery4c)

    def test_query4r(self):
        self.assertEqual(self.tc.encode('OpenC2-Response', self.mquery4r), self.mquery4r)
        self.assertEqual(self.tc.decode('OpenC2-Response', self.mquery4r), self.mquery4r)

if __name__ == '__main__':
    unittest.main()

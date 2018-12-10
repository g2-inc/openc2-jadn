# This Python file uses the following encoding: utf-8
from __future__ import unicode_literals

import os
import unittest

from libs.codec.codec import Codec
from libs.codec.jadn import jadn_load, jadn_analyze

# These unit tests include features that are not currently used in the OpenC2 Language Specification or
# any actuator profile.  They demonstrate that potential features work and show how to use them, to
# provide concrete illustration of alternative proposals.


class Experimental_IP(unittest.TestCase):

    def setUp(self):
        fn = os.path.join('schema', 'oc2ls-exp_merged.jadn')        # Load experimental OpenC2 schema
        schema = jadn_load(fn)
        sa = jadn_analyze(schema)
        if sa['undefined']:
            print('Warning - undefined:', sa['undefined'])
        self.tc = Codec(schema, verbose_rec=True, verbose_str=True)

    ipv4_addr_b64_api = {           # API IPv4 address target.  All API values are identical except for target name.
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_b64': b'\xc0\xa8\x00\xfe'}}}

    ipv4_addr_b64_api_bad1 = {      # Bad API IPv4 address target - too short
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_s': b'\xc0\xa8\x00'}}}

    ipv4_addr_b64_api_bad2 = {      # Bad API IPv4 address target - too long
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_s': b'\xc0\xa8\x00\xfe\x02'}}}

    ipv4_addr_b64_ser = {           # IPv4 address target serialized in Base64url format
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_b64': 'wKgA_g'}}}

    ipv4_addr_hex_api = {           # API IPv4 address target.  All API values are identical except for target name.
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_x': b'\xc0\xa8\x00\xfe'}}}

    ipv4_addr_hex_ser = {           # IPv4 address target serialized in hex format
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_x': 'C0A800FE'}}}

    ipv4_addr_hex_ser_bad1 = {      # Bad IPv4 address target - too short
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_x': 'C0A800'}}}

    ipv4_addr_hex_ser_bad2 = {      # Bad IPv4 address target - too long
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_x': 'C0A800FE02'}}}

    ipv4_addr_hex_ser_bad3 = {      # Bad IPv4 address target - punctuation
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_x': 'C0A8:00FE'}}}

    ipv4_addr_hex_ser_bad4 = {      # Bad IPv4 address target - lower case
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_x': 'C0a800fe'}}}

    ipv4_addr_hex_ser_bad5 = {      # Bad IPv4 address target - spaces
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_x': 'C0 A8 00 FE'}}}

    ipv4_addr_str_api = {           # API IPv4 address target.  All API values are identical except for target name.
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_s': b'\xc0\xa8\x00\xfe'}}}

    ipv4_addr_str_ser = {           # IPv4 address target serialized in type-specific string (dotted decimal) format
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_s': '192.168.0.254'}}}

    ipv4_addr_str_ser_bad1 = {      # Bad IPv4 address target - too long
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_s': '192.168.0.254.2'}}}

    ipv4_addr_str_ser_bad2 = {      # Bad IPv4 address target - leading zero
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_s': '192.168.0.054'}}}

    ipv4_addr_str_ser_bad3 = {      # Bad IPv4 address target - wrong punctuation
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_s': '192:168:0:54'}}}

    ipv4_addr_str_ser_bad4 = {      # Bad IPv4 address target - non-decimal
      'action': 'deny',
      'target': {'exp': {'ipv4_addr_s': '192.168.0.5a'}}}


    def test_ipv4_b64(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.ipv4_addr_b64_api), self.ipv4_addr_b64_ser)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.ipv4_addr_b64_ser), self.ipv4_addr_b64_api)
        with self.assertRaises(ValueError):
            self.tc.encode('OpenC2-Command', self.ipv4_addr_b64_api_bad1)
        with self.assertRaises(ValueError):
            self.tc.encode('OpenC2-Command', self.ipv4_addr_b64_api_bad2)

    def test_ipv4_hex(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.ipv4_addr_hex_api), self.ipv4_addr_hex_ser)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.ipv4_addr_hex_ser), self.ipv4_addr_hex_api)
        with self.assertRaises(ValueError):
            self.tc.decode('OpenC2-Command', self.ipv4_addr_hex_ser_bad1)
        with self.assertRaises(ValueError):
            self.tc.decode('OpenC2-Command', self.ipv4_addr_hex_ser_bad2)
        with self.assertRaises(ValueError):
            self.tc.decode('OpenC2-Command', self.ipv4_addr_hex_ser_bad3)
        with self.assertRaises(ValueError):
            self.tc.decode('OpenC2-Command', self.ipv4_addr_hex_ser_bad4)
        with self.assertRaises(ValueError):
            self.tc.decode('OpenC2-Command', self.ipv4_addr_hex_ser_bad5)

    def test_ipv4_str(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.ipv4_addr_str_api), self.ipv4_addr_str_ser)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.ipv4_addr_str_ser), self.ipv4_addr_str_api)
        with self.assertRaises(ValueError):
            self.tc.decode('OpenC2-Command', self.ipv4_addr_str_ser_bad1)
#        with self.assertRaises(ValueError):    # https://tools.ietf.org/html/draft-main-ipaddr-text-rep-02#section-3
#            self.tc.decode('OpenC2-Command', self.ipv4_addr_str_ser_bad2)      # leading zeroes are not used
        with self.assertRaises(ValueError):
            self.tc.decode('OpenC2-Command', self.ipv4_addr_str_ser_bad3)
        with self.assertRaises(ValueError):
            self.tc.decode('OpenC2-Command', self.ipv4_addr_str_ser_bad4)

    ipv6_addr_b64_api = {           # API IPv6 address target.  All API values are identical except for target name.
      'action': 'deny',
      'target': {'exp': {'ipv6_addr_b64': b' \x01\r\xb8\x85\xa3\x08\xd3\x13\x19\x8a.\x03psH'}}}

    ipv6_addr_b64_ser = {           # IPv6 address target serialized in Base64url format
      'action': 'deny',
      'target': {'exp': {'ipv6_addr_b64': 'IAENuIWjCNMTGYouA3BzSA'}}}

    ipv6_addr_hex_api = {           # API IPv6 address target.  All API values are identical except for target name.
      'action': 'deny',
      'target': {'exp': {'ipv6_addr_x': b' \x01\r\xb8\x85\xa3\x08\xd3\x13\x19\x8a.\x03psH'}}}

    ipv6_addr_hex_ser = {           # IPv6 address target serialized in hex format
      'action': 'deny',
      'target': {'exp': {'ipv6_addr_x': '20010DB885A308D313198A2E03707348'}}}

    ipv6_addr_str_api = {           # API IPv6 address target.  All API values are identical except for target name.
      'action': 'deny',
      'target': {'exp': {'ipv6_addr_s': b' \x01\r\xb8\x85\xa3\x08\xd3\x13\x19\x8a.\x03psH'}}}

    ipv6_addr_str_ser = {           # IPv6 address target serialized in type-specific string (dotted decimal) format
      'action': 'deny',
      'target': {'exp': {'ipv6_addr_s': '2001:db8:85a3:8d3:1319:8a2e:370:7348'}}}

    def test_ipv6_b64(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.ipv6_addr_b64_api), self.ipv6_addr_b64_ser)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.ipv6_addr_b64_ser), self.ipv6_addr_b64_api)

    def test_ipv6_hex(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.ipv6_addr_hex_api), self.ipv6_addr_hex_ser)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.ipv6_addr_hex_ser), self.ipv6_addr_hex_api)

    def test_ipv6_str(self):
        self.assertEqual(self.tc.encode('OpenC2-Command', self.ipv6_addr_str_api), self.ipv6_addr_str_ser)
        self.assertEqual(self.tc.decode('OpenC2-Command', self.ipv6_addr_str_ser), self.ipv6_addr_str_api)

if __name__ == '__main__':
    unittest.main()
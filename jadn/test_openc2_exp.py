# This Python file uses the following encoding: utf-8
from __future__ import unicode_literals

import os
import unittest

from jadnschema.codec.codec import Codec
from jadnschema import jadn_load, jadn_analyze

# These unit tests include features that are not currently used in the OpenC2 Language Specification or
# any actuator profile.  They demonstrate that potential features work and show how to use them, to
# provide concrete illustration of alternative proposals.


class Experimental_IPv4_Addr(unittest.TestCase):

    def setUp(self):
        fn = os.path.join('schema', 'exp.jadn')        # Load experimental OpenC2 schema
        schema = jadn_load(fn)
        sa = jadn_analyze(schema)
        if sa['undefined']:
            print('Warning - undefined:', sa['undefined'])
        self.tc = Codec(schema, verbose_rec=True, verbose_str=True)

    ipv4_addr_b64_api = {           # API IPv4 address.  All API values are identical except for name.
        'ipv4_addr_b64': b'\xc0\xa8\x00\xfe'}

    ipv4_addr_b64_ser = {           # IPv4 address serialized in Base64url format
        'ipv4_addr_b64': 'wKgA_g'}

    ipv4_addr_hex_api = {           # API IPv4 address.  All API values are identical except for name.
        'ipv4_addr_x': b'\xc0\xa8\x00\xfe'}

    ipv4_addr_hex_ser = {           # IPv4 address serialized in hex format
        'ipv4_addr_x': 'C0A800FE'}

    ipv4_addr_str_api = {           # API IPv4 address.  All API values are identical except for name.
        'ipv4_addr_s': b'\xc0\xa8\x00\xfe'}

    ipv4_addr_str_ser = {           # IPv4 address serialized in type-specific string (dotted decimal) format
        'ipv4_addr_s': '192.168.0.254'}

    ipv4_addr_b64_api_bad1 = {  # Bad API IPv4 address - too short
        'ipv4_addr_s': b'\xc0\xa8\x00'}

    ipv4_addr_b64_api_bad2 = {  # Bad API IPv4 address - too long
        'ipv4_addr_s': b'\xc0\xa8\x00\xfe\x02'}

    ipv4_addr_hex_ser_bad1 = {      # Bad IPv4 address - too short
        'ipv4_addr_x': 'C0A800'}

    ipv4_addr_hex_ser_bad2 = {      # Bad IPv4 address - too long
        'ipv4_addr_x': 'C0A800FE02'}

    ipv4_addr_hex_ser_bad3 = {      # Bad IPv4 address - punctuation
        'ipv4_addr_x': 'C0A8:00FE'}

    ipv4_addr_hex_ser_bad4 = {      # Bad IPv4 address - lower case
        'ipv4_addr_x': 'C0a800fe'}

    ipv4_addr_hex_ser_bad5 = {      # Bad IPv4 address - spaces
        'ipv4_addr_x': 'C0 A8 00 FE'}

    ipv4_addr_str_ser_bad1 = {      # Bad IPv4 address - too long
        'ipv4_addr_s': '192.168.0.254.2'}

    ipv4_addr_str_ser_bad2 = {      # Bad IPv4 address - leading zero
        'ipv4_addr_s': '192.168.0.054'}

    ipv4_addr_str_ser_bad3 = {      # Bad IPv4 address - wrong punctuation
        'ipv4_addr_s': '192:168:0:54'}

    ipv4_addr_str_ser_bad4 = {      # Bad IPv4 address - non-decimal
        'ipv4_addr_s': '192.168.0.5a'}

    def test_ipv4_b64(self):
        self.assertEqual(self.tc.encode('Target', self.ipv4_addr_b64_api), self.ipv4_addr_b64_ser)
        self.assertEqual(self.tc.decode('Target', self.ipv4_addr_b64_ser), self.ipv4_addr_b64_api)
        with self.assertRaises(ValueError):
            self.tc.encode('Target', self.ipv4_addr_b64_api_bad1)
        with self.assertRaises(ValueError):
            self.tc.encode('Target', self.ipv4_addr_b64_api_bad2)

    def test_ipv4_hex(self):
        self.assertEqual(self.tc.encode('Target', self.ipv4_addr_hex_api), self.ipv4_addr_hex_ser)
        self.assertEqual(self.tc.decode('Target', self.ipv4_addr_hex_ser), self.ipv4_addr_hex_api)
        with self.assertRaises(ValueError):
            self.tc.decode('Target', self.ipv4_addr_hex_ser_bad1)
        with self.assertRaises(ValueError):
            self.tc.decode('Target', self.ipv4_addr_hex_ser_bad2)
        with self.assertRaises(TypeError):
            self.tc.decode('Target', self.ipv4_addr_hex_ser_bad3)
        with self.assertRaises(TypeError):
            self.tc.decode('Target', self.ipv4_addr_hex_ser_bad4)
        with self.assertRaises(TypeError):
            self.tc.decode('Target', self.ipv4_addr_hex_ser_bad5)

    def test_ipv4_str(self):
        self.assertEqual(self.tc.encode('Target', self.ipv4_addr_str_api), self.ipv4_addr_str_ser)
        self.assertEqual(self.tc.decode('Target', self.ipv4_addr_str_ser), self.ipv4_addr_str_api)
        with self.assertRaises(ValueError):
            self.tc.decode('Target', self.ipv4_addr_str_ser_bad1)
#        with self.assertRaises(ValueError):    # https://tools.ietf.org/html/draft-main-ipaddr-text-rep-02#section-3
#            self.tc.decode('Target', self.ipv4_addr_str_ser_bad2)      # leading zeroes are not used
        with self.assertRaises(ValueError):
            self.tc.decode('Target', self.ipv4_addr_str_ser_bad3)
        with self.assertRaises(ValueError):
            self.tc.decode('Target', self.ipv4_addr_str_ser_bad4)


class Experimental_IPv6_Addr(unittest.TestCase):

    def setUp(self):
        fn = os.path.join('schema', 'exp.jadn')  # Load experimental OpenC2 schema
        schema = jadn_load(fn)
        sa = jadn_analyze(schema)
        if sa['undefined']:
            print('Warning - undefined:', sa['undefined'])
        self.tc = Codec(schema, verbose_rec=True, verbose_str=True)

    ipv6_addr_b64_api = {           # API IPv6 address.  All API values are identical except for name.
        'ipv6_addr_b64': b' \x01\r\xb8\x85\xa3\x08\xd3\x13\x19\x8a.\x03psH'}

    ipv6_addr_b64_ser = {           # IPv6 address serialized in Base64url format
        'ipv6_addr_b64': 'IAENuIWjCNMTGYouA3BzSA'}

    ipv6_addr_hex_api = {           # API IPv6 address.  All API values are identical except for name.
        'ipv6_addr_x': b' \x01\r\xb8\x85\xa3\x08\xd3\x13\x19\x8a.\x03psH'}

    ipv6_addr_hex_ser = {           # IPv6 address serialized in hex format
        'ipv6_addr_x': '20010DB885A308D313198A2E03707348'}

    ipv6_addr_str_api = {           # API IPv6 address.  All API values are identical except for name.
        'ipv6_addr_s': b' \x01\r\xb8\x85\xa3\x08\xd3\x13\x19\x8a.\x03psH'}

    ipv6_addr_str_ser = {           # IPv6 address serialized in type-specific string (dotted decimal) format
        'ipv6_addr_s': '2001:db8:85a3:8d3:1319:8a2e:370:7348'}

    ipv6_addr_b64_api_bad1 = {      # Bad API IPv6 address - too short
        'ipv6_addr_s': b' \x01\r\xb8\x85\xa3\x08\xd3\x13\x19\x8a.\x03ps'}

    ipv6_addr_b64_api_bad2 = {      # Bad API IPv6 address - too long
        'ipv6_addr_s': b' \x01\r\xb8\x85\xa3\x08\xd3\x13\x19\x8a.\x03psH\x01'}

    ipv6_addr_hex_ser_bad1 = {      # Bad IPv6 address - too short
        'ipv6_addr_x': '20010DB885A308D313198A2E037073'}

    ipv6_addr_hex_ser_bad2 = {      # Bad IPv6 address - too long
        'ipv6_addr_x': '20010DB885A308D313198A2E0370734801'}

    ipv6_addr_hex_ser_bad3 = {      # Bad IPv6 address - punctuation
        'ipv6_addr_x': '2001:0DB8:85A3:08D3:1319:8A2E:0370:7348'}

    ipv6_addr_hex_ser_bad4 = {      # Bad IPv6 address - lower case
        'ipv6_addr_x': '20010db885a308d313198a2e03707348'}

    ipv6_addr_hex_ser_bad5 = {      # Bad IPv6 address - spaces
        'ipv6_addr_x': '2001 0DB8 85A3 08D3 1319 8A2E 0370 7348'}

    ipv6_addr_str_ser_bad1 = {      # Bad IPv6 address - too long
        'ipv6_addr_s': '2001:db8:85a3:8d3:1319:8a2e:370:7348:0123'}

    ipv6_addr_str_ser_bad2 = {      # Bad IPv6 address - leading zero
        'ipv6_addr_s': '2001:0db8:85a3:08d3:1319:8a2e:0370:7348'}

    ipv6_addr_str_ser_bad3 = {      # Bad IPv6 address - wrong punctuation
        'ipv6_addr_s': '2001.db8.85a3.8d3.1319.8a2e.370.7348'}

    def test_ipv6_b64(self):
        self.assertEqual(self.tc.encode('Target', self.ipv6_addr_b64_api), self.ipv6_addr_b64_ser)
        self.assertEqual(self.tc.decode('Target', self.ipv6_addr_b64_ser), self.ipv6_addr_b64_api)
        with self.assertRaises(ValueError):
            self.tc.encode('Target', self.ipv6_addr_b64_api_bad1)
        with self.assertRaises(ValueError):
            self.tc.encode('Target', self.ipv6_addr_b64_api_bad2)

    def test_ipv6_hex(self):
        self.assertEqual(self.tc.encode('Target', self.ipv6_addr_hex_api), self.ipv6_addr_hex_ser)
        self.assertEqual(self.tc.decode('Target', self.ipv6_addr_hex_ser), self.ipv6_addr_hex_api)
        with self.assertRaises(ValueError):
            self.tc.decode('Target', self.ipv6_addr_hex_ser_bad1)
        with self.assertRaises(ValueError):
            self.tc.decode('Target', self.ipv6_addr_hex_ser_bad2)
        with self.assertRaises(TypeError):
            self.tc.decode('Target', self.ipv6_addr_hex_ser_bad3)
        with self.assertRaises(TypeError):
            self.tc.decode('Target', self.ipv6_addr_hex_ser_bad4)
        with self.assertRaises(TypeError):
            self.tc.decode('Target', self.ipv6_addr_hex_ser_bad5)

    def test_ipv6_str(self):
        self.assertEqual(self.tc.encode('Target', self.ipv6_addr_str_api), self.ipv6_addr_str_ser)
        self.assertEqual(self.tc.decode('Target', self.ipv6_addr_str_ser), self.ipv6_addr_str_api)
        with self.assertRaises(ValueError):
            self.tc.decode('Target', self.ipv6_addr_str_ser_bad1)
#        with self.assertRaises(ValueError):    # https://tools.ietf.org/html/draft-main-ipaddr-text-rep-02#section-3
#            self.tc.decode('Target', self.ipv6_addr_str_ser_bad2)      # leading zeroes are not used
        with self.assertRaises(ValueError):
            self.tc.decode('Target', self.ipv6_addr_str_ser_bad3)


class Experimental_IPv4_Net(unittest.TestCase):

    def setUp(self):
        fn = os.path.join('schema', 'exp.jadn')        # Load experimental OpenC2 schema
        schema = jadn_load(fn)
        sa = jadn_analyze(schema)
        if sa['undefined']:
            print('Warning - undefined:', sa['undefined'])
        self.tc = Codec(schema, verbose_rec=True, verbose_str=True)

    ipv4_net_api = {           # API IPv4 net.
        'ipv4_net': [b'\xc0\xa8\x00\xfe', 24]}

    ipv4_net_api_bad1 = {       # Negative
        'ipv4_net': [b'\xc0\xa8\x00\xfe', -3]}

    ipv4_net_api_bad2 = {       # Too large
        'ipv4_net': [b'\xc0\xa8\x00\xfe', 42]}

    ipv4_net_ser = {            # IPv4 net serialized in type-specific string (dotted decimal) format
        'ipv4_net': '192.168.0.254/24'}

    ipv4_net_ser_bad1 = {       # Leading 0
        'ipv4_net': '192.168.0.254/024'}

    ipv4_net_ser_bad2 = {       # Negative
        'ipv4_net': '192.168.0.254/-3'}

    ipv4_net_ser_bad3 = {       # Too large
        'ipv4_net': '192.168.0.254/42'}

    def test_ipv4_net(self):
        self.assertEqual(self.tc.encode('Target', self.ipv4_net_api), self.ipv4_net_ser)
        self.assertEqual(self.tc.decode('Target', self.ipv4_net_ser), self.ipv4_net_api)
        with self.assertRaises(ValueError):
            self.tc.encode('Target', self.ipv4_net_api_bad1)
        with self.assertRaises(ValueError):
            self.tc.encode('Target', self.ipv4_net_api_bad2)
#        with self.assertRaises(ValueError):
#            self.tc.decode('Target', self.ipv4_net_ser_bad1)
        with self.assertRaises(ValueError):
            self.tc.decode('Target', self.ipv4_net_ser_bad2)
        with self.assertRaises(ValueError):
            self.tc.decode('Target', self.ipv4_net_ser_bad3)


class Experimental_IPv6_Net(unittest.TestCase):

    def setUp(self):
        fn = os.path.join('schema', 'exp.jadn')        # Load experimental OpenC2 schema
        schema = jadn_load(fn)
        sa = jadn_analyze(schema)
        if sa['undefined']:
            print('Warning - undefined:', sa['undefined'])
        self.tc = Codec(schema, verbose_rec=True, verbose_str=True)

    ipv6_net_api = {           # API IPv4 net.
        'ipv6_net': [b' \x01\r\xb8\x85\xa3\x08\xd3\x13\x19\x8a.\x03psH', 64]}

    ipv6_net_api_bad1 = {       # Negative
        'ipv6_net': [b' \x01\r\xb8\x85\xa3\x08\xd3\x13\x19\x8a.\x03psH', -3]}

    ipv6_net_api_bad2 = {       # Too large
        'ipv6_net': [b' \x01\r\xb8\x85\xa3\x08\xd3\x13\x19\x8a.\x03psH', 142]}

    ipv6_net_ser = {            # IPv4 net serialized in type-specific string (dotted decimal) format
        'ipv6_net': '2001:db8:85a3:8d3:1319:8a2e:370:7348/64'}

    ipv6_net_ser_bad1 = {       # Leading 0
        'ipv6_net': '2001:db8:85a3:8d3:1319:8a2e:370:7348/064'}

    ipv6_net_ser_bad2 = {       # Negative
        'ipv6_net': '2001:db8:85a3:8d3:1319:8a2e:370:7348/-3'}

    ipv6_net_ser_bad3 = {       # Too large
        'ipv6_net': '2001:db8:85a3:8d3:1319:8a2e:370:7348/142'}

    def test_ipv6_net(self):
        self.assertEqual(self.tc.encode('Target', self.ipv6_net_api), self.ipv6_net_ser)
        self.assertEqual(self.tc.decode('Target', self.ipv6_net_ser), self.ipv6_net_api)
        with self.assertRaises(ValueError):
            self.tc.encode('Target', self.ipv6_net_api_bad1)
        with self.assertRaises(ValueError):
            self.tc.encode('Target', self.ipv6_net_api_bad2)
#        with self.assertRaises(ValueError):
#            self.tc.decode('Target', self.ipv6_net_ser_bad1)
        with self.assertRaises(ValueError):
            self.tc.decode('Target', self.ipv6_net_ser_bad2)
        with self.assertRaises(ValueError):
            self.tc.decode('Target', self.ipv6_net_ser_bad3)


if __name__ == '__main__':
    unittest.main()

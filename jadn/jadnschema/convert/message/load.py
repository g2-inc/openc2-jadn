import base64
import binascii
import collections
import cbor2
import json
import os
import xmltodict


from ...codec.codec_format import s2b_ip_addr
from ... import (
    enums,
    utils
)


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


def jsonWalk(node):
    tmp_node = type(node)()
    for key, item in node.items():
        if isinstance(item, (int, str, float)):
            if key in ['src_addr', 'dst_addr']:
                tmp_ip = item + ((4 - len(item) % 4) % 4) * '='
                if utils.isBase64(tmp_ip):
                    tmp_item = item
                else:
                    tmp_item = base64.b64encode(s2b_ip_addr(item))
            elif item.isdigit():
                tmp_item = int(item)
            else:
                tmp_item = item
        else:
            tmp_item = jsonWalk(item)

        if type(tmp_node) is dict:
            tmp_node[key] = tmp_item
        else:
            tmp_node.append(tmp_item)

    return tmp_node


def essageLoader(msg='', msgType=enums.MessageFormats.JSON):
    def load_json(m):
        """
        :param m: JSON Encoded message
        :type m: str or dict
        :raise SyntaxError: Malformed JSON encoded message
        :raise ValueError: Malformed JSON encoded message
        """
        if os.path.isfile(m):
            try:
                with open(m, 'rb') as f:
                    rtn = json.load(f)
            except (SyntaxError, ValueError) as e:
                raise e

        elif type(m) == str:
            try:
                rtn = json.loads(m)
            except (SyntaxError, ValueError) as e:
                raise e

        elif type(m) == dict:
            rtn = m

        else:
            raise Exception('Cannot load json, improperly formatted')

        return rtn

    def load_cbor(m):
        """
        :param m: CBOR Encoded message
        :type m: hex encoded string (each character is a two digit hex value)
        :raise SyntaxError: Malformed CBOR encoded message
        :raise ValueError: Malformed CBOR encoded message
        :raise cbor2.decoder.CBORDecodeError: Malformed CBOR encoded message
        """
        if os.path.isfile(m):
            try:
                with open(m, 'rb') as f:
                    rtn = cbor2.load(f)
            except (SyntaxError, ValueError, cbor2.decoder.CBORDecodeError) as e:
                raise e

        elif type(m) in [str, bytes]:

            try:
                rtn = cbor2.load(StringIO(m))
                if rtn is not dict:
                    rtn = cbor2.loads(binascii.unhexlify(m))
            except (SyntaxError, ValueError, cbor2.decoder.CBORDecodeError) as e1:
                try:
                    rtn = cbor2.loads(binascii.unhexlify(m))
                except (SyntaxError, ValueError, cbor2.decoder.CBORDecodeError) as e2:
                    raise e2
        else:
            raise Exception('Cannot load cbor, improperly formatted')

        return utils.default_encode(rtn)

    def load_protobuf(m):
        """
        :param m: ProtoBuf Encoded message
        :type m: str
        """
        if os.path.isfile(m):
            with open(m, 'rb') as f:
                pass
                # TODO: Convert ProtoBuf data to dict
                # rtn = f.read()
                rtn = {}
        elif type(m) == str:
            rtn = {}

        else:
            raise Exception('Cannot load protobuf, improperly formatted')

        return rtn

    def load_xml(m):
        """
        :parammg: XML Encoded message
        :type m: str
        """

        def _xml_to_dict(xml):
            tmp = {}

            for t in xml:
                if type(xml[t]) == collections.OrderedDict:
                    tmp[t] = _xml_to_dict(xml[t])
                else:
                    tmp[t[1:] if t.startswith("@") else t] = xml[t]

            return tmp

        if os.path.isfile(m):
            with open(m, 'rb') as f:
                return _xml_to_dict(xmltodict.parse(f.read()))['message']

        elif type(m) == str:
            return _xml_to_dict(xmltodict.parse(m))['message']

        else:
            raise Exception('Cannot load xml, improperly formatted')

    load = {
        'json': load_json,
        'cbor': load_cbor,
        'proto': load_protobuf,
        'xml': load_xml
    }
    if msgType in enums.MessageFormats.values():
        tmp = load.get(msgType, load['json'])(msg)
        # tmp = Utils.defaultDecode(Utils.defaultEncode(jsonWalk(tmp)))
        # print(tmp)
        return tmp
    else:
        raise ValueError("Message Type is not a Valid Message Format")

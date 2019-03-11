import json
import re

from datetime import datetime

from bs4 import BeautifulSoup, Comment

from jadn.utils import jadn_format, toStr
from jadn.jadn_defs import is_structure
from jadn.jadn_utils import fopts_d2s, topts_d2s, fopts_s2d, topts_s2d


class Relax2Jadn(object):
    def __init__(self, relax):
        if type(relax) in [str, bytes]:
            relax = toStr(relax).replace('\n', '')
            relax = re.sub(r'>\s*?<', '><', relax)
            self.schema = BeautifulSoup(relax, 'html.parser')

        else:
            raise TypeError('Relax-NG improperly formatted')

        self._fieldMap = {
            'base64Binary': 'Binary',
            'boolean': 'Boolean',
            'integer': 'Integer',
            'float': 'Number',
            '': 'Null',
            'string': 'String'
        }

    def jadn_dump(self):
        jadn = {
            'meta': self.makeMeta(),
            'types': self.makeTypes()
        }

        return jadn_format(jadn, indent=2)

    def makeMeta(self):
        meta = {}

        for m in self.schema .find_all(string=lambda text: isinstance(text, Comment)):
            m = re.sub(r'(^\s|\s$)', '', m)
            if m.startswith('meta:'):
                m = re.sub('meta:\s?', '', m)
                k, v = m.split(' - ')

                try:
                    v = json.loads(v)
                except Exception as e:
                    v = re.sub(r'(^\s?|\s?$)', '', v)
                meta[k] = v

        return meta

    def makeTypes(self):
        types = []

        for t in self.schema.find_all('define'):
            tmp_type = [t['name']]
            children = list(t.children)
            if isinstance(children[0], Comment):
                com, opts = self._loadCommentDefs(children[0].string)

                tmp_type.append(opts['type'] if 'type' in opts else 'String')

                if 'options' in opts:
                    options = opts['options'] if type(opts['options']) is dict else {}
                    tmp_type.append(topts_d2s(options))
                else:
                    tmp_type.append([])

                tmp_type.append(topts_d2s(opts['options']) if 'options' in opts else [])

                tmp_type.append(com)
                children = children[1:]

            if children[0].name == 'data':
                tmp_type.insert(1, self._fieldType(children[0]['type']))

            else:
                c = self._children(children)
                tmp_type.append(c)

            types.append(tmp_type)

        return types

    def formatStr(self, s):
        """
        Formats the string for use in schema
        :param s: string to format
        :type s: str
        :return: formatted string
        :rtype str
        """
        if s == '*':
            return 'unknown'
        else:
            return re.sub(r'[\- ]', '_', s)

    def _children(self, childList):
        tmp_defs = []
        tmp_count = 1
        for child in childList:
            # print(child)
            if child.name == 'interleave':
                # print('Interleave')
                c = self._children(list(child.children))
                tmp_defs.extend(c)

            elif child.name == 'optional':
                # print('Optional')
                c = self._children(list(child.children))
                tmp_defs.extend(c)

            elif child.name == 'choice':
                # print('Optional')
                c = self._children(list(child.children))
                tmp_defs.extend(c)

            elif child.name == 'element':
                tmp_def = [child['name']]
                comment = child.find_all(string=lambda text: isinstance(text, Comment))
                ref_data = child.findAll(['ref', 'data', 'text'])

                if len(comment) == 1 and len(ref_data) == 1:
                    com, opts = self._loadCommentDefs(comment[0].string)
                    ref_data = ref_data[0]

                    if 'field' in opts:
                        tmp_def.insert(0, opts['field'])

                    fieldType = ref_data['type'] if ref_data.name == 'data' else (ref_data['name'] if ref_data.name == 'ref' else 'string')

                    if 'type' in opts:
                        fieldTypeTmp = self.formatStr(opts['type'])
                        fieldType = fieldType if fieldTypeTmp == fieldType else fieldTypeTmp

                    tmp_def.append(self._fieldType(fieldType))

                    if 'options' in opts:
                        options = opts['options'] if type(opts['options']) is dict else {}
                        tmp_def.append(topts_d2s(options) if is_structure(opts['type']) else fopts_d2s(options))
                    else:
                        tmp_def.append([])

                    tmp_def.append(com)

                else:
                    print(child.name)
                    print('Comment: {}'.format(comment))
                    print('Options: {}'.format(ref_data))
                    print('Issues with schema formatting')

                # print('Append Element')
                tmp_defs.append(tmp_def)

            elif child.name == 'value':
                def_name = child.parent.parent['name']
                tmp_def = []
                comment = child.find_all(string=lambda text: isinstance(text, Comment))
                if len(comment) == 1:
                    com, opts = self._loadCommentDefs(comment[0].string)

                    if 'field' in opts:
                        tmp_def.append(opts['field'])

                    else:
                        tmp_def.append(tmp_count)

                    val = child.text.strip()
                    if re.match(r'^Unknown_{}_'.format(def_name), val):
                        val = ''

                    tmp_def.append(val)
                    tmp_def.append(com)

                else:
                    tmp_def.append([tmp_count, child.text.strip(), ''])

                tmp_defs.append(tmp_def)

            else:
                print('Unknown tag function: {}'.format(child.name))

        tmp_count += 1

        return tmp_defs

    def _fieldType(self, f):
        """
        Determines the field type for the schema
        :param f: current type
        :return: type mapped to the schema
        :rtype str
        """
        rtn = self._fieldMap.get(f, f)

        return rtn

    def _loadCommentDefs(self, comStr):
        com = re.sub(r'(^\s?|\s?$)', '', comStr)
        com = re.sub(r'\s?#jadn_opts:\s*?\{.*?\}+', '', com)
        opts = re.sub(r'.*?#jadn_opts:\s*?(?P<opts>\{.*?\}+)', '\g<opts>', comStr)

        try:
            opts = json.loads(opts)
            opts['type'] = opts['type'] if 'type' in opts else 'String'
        except Exception as e:
            # print('Err: {}'.format(opts))
            opts = {}

        return com, opts


def relax_loads(relax):
    """
    Produce jadn schema from relax schema
    :arg relax: JADN Schema to convert
    :type relax: str
    :return: jadn schema
    :rtype str
    """
    return Relax2Jadn(relax).jadn_dump()


def relax_load(relax, fname, source=""):
    with open(fname, "w") as f:
        if source:
            f.write("-- Generated from {}, {}\n".format(source, datetime.ctime(datetime.now())))
        f.write(relax_loads(relax))

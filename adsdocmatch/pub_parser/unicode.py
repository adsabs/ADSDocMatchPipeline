from builtins import chr
from builtins import object
import os
import re
from collections import UserDict


class UnicodeError(Exception):
    """
    Error in the UnicodeHandler.
    """
    pass


class UnicodeChar(object):
    def __init__(self, fields):
        """

        :param fields:
        """
        self.code = int(fields[0].strip())
        self.entity = fields[1].strip()
        self.ascii = fields[2].strip()
        self.latex = fields[3].strip()
        if len(fields) > 4:
            self.type = fields[4].strip()
        else:
            self.type = ''


class UnicodeHandler(UserDict):
    """
    Loads a table of Unicode Data from a file.

    Each line of the file consists in 4 or 5 fields.
    Field description:
    1/ Unicode code
    2/ Entity name
    3/ Ascii representation
    4/ Latex representation
    5/ Type (optional) can be P=ponctuation, S=space, L=lowercase-letter, U=uppercase-letter

    Some day we may want to scrap this approach in favor of using the python
    namedentities module (although that will lack the TeX representation)

    """

    re_entity = re.compile(r'&([a-zA-Z0-9]{2,}?);')
    re_numentity = re.compile(r'&#(?P<number>\d+);')
    re_hexnumentity = re.compile('&#x(?P<hexnum>[0-9a-fA-F]+);')

    # Courtesy of Chase Seibert.
    # http://bitkickers.blogspot.com/2011/05/stripping-control-characters-in-python.html
    re_xml_illegal = re.compile(u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])|' + \
                                u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
                                (chr(0xd800), chr(0xdbff), chr(0xdc00), chr(0xdfff), chr(0xd800), chr(0xdbff),
                                 chr(0xdc00), chr(0xdfff), chr(0xd800), chr(0xdbff), chr(0xdc00), chr(0xdfff)))
    re_control_char = re.compile(r"[\x01-\x08\x0B-\x1F\x7F]")
    re_white_space = re.compile(r"\s+")

    XML_PREDEFINED_ENTITIES = ('quot', 'amp', 'apos', 'lt', 'gt')

    def __init__(self):
        """

        :param data_filename:
        """
        self.data_filename = os.path.dirname(__file__) + '/unicode.dat'
        self.str = [None, ] * 65536

        lines = open(self.data_filename).readlines()
        UserDict.__init__(self)
        for line in lines:
            fields = line.split()
            for i, field in enumerate(fields):
                if field.startswith('"') and field.endswith('"'):
                    fields[i] = field[1:-1]
            if len(fields) > 3:
                try:
                    code = int(fields[0].split(':')[0].split(';')[0])
                    entity = fields[1]
                    self[entity] = UnicodeChar(fields)  # keep entity table

                    if len(fields) > 4:  # keep code table
                        if not self.str[code]:
                            self.str[code] = self[entity]
                        else:
                            pass
                except ValueError:
                    pass

    def __unichr(self, value):
        """
        Computes correct wide unicode characters on a narrow platform.
        For more info, see: http://stackoverflow.com/questions/7105874/valueerror-unichr-arg-not-in-range0x10000-narrow-python-build-please-hel

        :param value:
        :return:
        """
        try:
            return chr(value)
        except ValueError:
            ustring = "\\U%08x" % value
            return ustring.decode('unicode-escape')

    def sub_entity(self, match):
        """

        :param match:
        :return:
        """
        ent = match.group(1)
        if ent in list(self.keys()):
            ret = eval("u'\\u%04x'" % self[ent].code)
            return ret
        return None

    def sub_xml_entity(self, match):
        """
        similar to sub_entity, but preserve the built-in XML predifined entities

        :param match:
        :return:
        """
        ent = match.group(1)
        if ent in self.XML_PREDEFINED_ENTITIES:
            return "&" + ent + ";"
        elif ent in list(self.keys()):
            ret = eval("u'\\u%04x'" % self[ent].code)
            return ret
        else:
            raise UnicodeError('Unknown numeric entity: %s' % match.group(0))

    def numeric_entity_to_unicode(self, match):
        """

        :param match:
        :return:
        """
        entity_number = int(match.group('number'))
        try:
            return self.__unichr(entity_number)
        except ValueError:
            raise UnicodeError('Unknown numeric entity: %s' % match.group(0))

    def hexadecimal_entity_to_unicode(self, match):
        """

        :param match:
        :return:
        """
        entity_number = int(match.group('hexnum'), 16)
        try:
            return self.__unichr(entity_number)
        except ValueError:
            raise UnicodeError('Unknown hexadecimal entity: %s' % match.group(0))

    # this function is not used, but keep it for now
    def ent2u(self, the_entity):
        """

        :param the_entity:
        :return:
        """
        the_unicode = self.re_entity.sub(self.sub_entity, the_entity)
        the_unicode = self.re_numentity.sub(self.numeric_entity_to_unicode, the_unicode)
        the_unicode = self.re_hexnumentity.sub(self.hexadecimal_entity_to_unicode, the_unicode)
        return the_unicode

    def ent2xml(self, the_entity):
        """
        translates entities to unicode but keep basic XML entities (such as "&lt;", "&gt;") encoded
        (we use this to properly process fields such as abstracts and title which may contain HTML markup)

        :param the_entity:
        :return:
        """
        the_xml = self.re_entity.sub(self.sub_xml_entity, the_entity)
        the_xml = self.re_numentity.sub(self.numeric_entity_to_unicode, the_xml)
        the_xml = self.re_hexnumentity.sub(self.hexadecimal_entity_to_unicode, the_xml)
        return the_xml

    def remove_control_chars(self, input, strict=False):
        """

        :param input:
        :param strict:
        :return:
        """
        input = self.re_xml_illegal.sub("", input)
        if not strict:
            # map all whitespace to single blank
            input = self.re_white_space.sub(" ", input)
        # now remove control characters
        input = self.re_control_char.sub("", input)
        return input

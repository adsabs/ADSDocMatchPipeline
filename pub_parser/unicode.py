import os
import re
from UserDict import UserDict


class UnicodeError(Exception):
    """
    Error in the UnicodeHandler.
    """
    pass


class UnicodeChar:
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

    re_entity = re.compile('&([a-zA-Z0-9]{2,}?);')
    re_numentity = re.compile('&#(?P<number>\d+);')
    re_hexnumentity = re.compile('&#x(?P<hexnum>[0-9a-fA-F]+);')

    XML_PREDEFINED_ENTITIES = ('quot', 'amp', 'apos', 'lt', 'gt')

    def __init__(self):
        """

        :param data_filename:
        """
        self.data_filename = os.path.dirname(__file__) + '/unicode.dat'
        self.unicode = [None, ] * 65536

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
                        if not self.unicode[code]:
                            self.unicode[code] = self[entity]
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
            return unichr(value)
        except ValueError:
            ustring = "\\U%08x" % value
            return ustring.decode('unicode-escape')

    def sub_entity(self, match):
        """
    
        :param match:
        :return:
        """
        ent = match.group(1)
        if ent in self.keys():
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
        elif ent in self.keys():
            ret = eval("u'\\u%04x'" % self[ent].code)
            return ret
        else:
            raise UnicodeError('Unknown numeric entity: %s' % match.group(0))
    
    
    def numeric_entity_to_unicode(self, match):
    
        entity_number = int(match.group('number'))
        try:
            return self.__unichr(entity_number)
        except ValueError:
            raise UnicodeError('Unknown numeric entity: %s' % match.group(0))
    
    def hexadecimal_entity_to_unicode(self, match):
    
        entity_number = int(match.group('hexnum'), 16)
        try:
            return self.__unichr(entity_number)
        except ValueError:
            raise UnicodeError('Unknown hexadecimal entity: %s' % match.group(0))

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

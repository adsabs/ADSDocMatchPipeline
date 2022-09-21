from builtins import chr
import sys
import re
from adsputils import setup_logging
from pub_parser.unicode import UnicodeHandler

logger = setup_logging('docmatch_log')

FIELDPAT = re.compile(r"([A-Za-z][^:]*):\s*(.*)")
MAX_ABSTRACT_FIELD_LINES = 50000
# Fields containing entity-encoded content but without ad-hoc handlers
ENCODED_ABSTRACT_FIELDS = ['Origin', 'Abstract Copyright', 'Instruments']
# Fieldes containing HTML encoded content
HTML_ENCODED_ABSTRACT_FIELDS = ['Journal', 'Authors']

class MetadataError(Exception):
    """
    Error in reading metadata routine.
    """
    pass

def get_illegal_char_regex():
    """
    Returns an re object to find unicode characters illegal in XML
    """
    illegal_unichrs = [ (0x00, 0x08), (0x0B, 0x1F), (0x7F, 0x84), (0x86, 0x9F),
        (0xD800, 0xDFFF), (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF),
        (0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF), (0x3FFFE, 0x3FFFF),
        (0x4FFFE, 0x4FFFF), (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
        (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF), (0x9FFFE, 0x9FFFF),
        (0xAFFFE, 0xAFFFF), (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
        (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF), (0xFFFFE, 0xFFFFF),
        (0x10FFFE, 0x10FFFF) ]
    illegal_ranges = ["%s-%s" % (chr(low), chr(high))
        for (low, high) in illegal_unichrs if low < sys.maxunicode]
    return re.compile(u'[%s]' % u''.join(illegal_ranges))
ILLEGALCHARSREGEX = get_illegal_char_regex()

UNICODE_HANDLER = UnicodeHandler()

def as_needed(article):
    """
    return only needed fields

    :param article:
    :return:
    """
    field_mappings = [
        ("Authors", "authors"),
        ("Title", "title"),
        ("Abstract", "abstract"),
        ("Publication Date", "pubdate"),
        ("Bibliographic Code", "bibcode"),
    ]
    return_record = {}
    for src_key, dest_key in field_mappings:
        value = article.get(src_key, None)
        if value:
            return_record[dest_key] = value
    return return_record

def get_pub_metadata(contents):
    """
    Returns a dictionary generated from the metadata file.

    :param contents:
    :return:
    """
    article = {}
    article[u'Bibliographic Code'] = ''
    current_field = ''
    current_value = ''
    fields_found_in_file = []
    num_lines = 0

    if (isinstance(contents, bytes)):
        contents = contents.decode('utf-8')

    #I check if in the file there are invalid unicode characters
    if ILLEGALCHARSREGEX.search(contents):
        # strip illegal stuff but keep newlines
        contents = UNICODE_HANDLER.remove_control_chars(contents, strict=True)
        logger.error('Illegal unicode character in metadata file')
    contents = contents.strip().split('\n')

    while contents:
        line = contents.pop(0)
        match = FIELDPAT.match(line)
        if match:
            # see if we have an existing field
            if current_field:
                article[current_field] = current_value
            current_field = match.group(1)
            current_value = match.group(2).strip()
            fields_found_in_file.append(current_field)
            num_lines = 1
        elif line == '                               Abstract':
            # Beginning of the abstract.
            fields_found_in_file.append('Abstract')
            article[current_field] = current_value
            break
        elif line.strip():
            # Same field as previous line. Append to the value.
            current_value = current_value + ' ' + line.strip()
            num_lines += 1

        if num_lines > MAX_ABSTRACT_FIELD_LINES:
            raise MetadataError('Number of lines for field %s too large (%d).'%(current_field, num_lines))

    # Now let's get the abstract. The abstract can contain multiple
    # paragraphs so we need to make sure that we keep this information.
    abstract = ''.join([l.strip() and l.strip() + ' ' or '<P />' for l in contents])
    article[u'Abstract'] = abstract.strip().replace(' \n', '\n')

    # if the bibcode is not in the field that I have retrieved then there is a huge problem with the file
    if 'Bibliographic Code' not in fields_found_in_file:
        raise MetadataError('No bibcode field found')

    if len(article['Bibliographic Code']) != 19:
        raise MetadataError('Invalid bibcode')

    if 'Authors' not in fields_found_in_file and 'Review Author' in fields_found_in_file:
        article['Authors'] = article['Review Author']

    # now properly encode data in fields which have XML-encoded entities and which do not
    # have their own specific content management/cleanup routine
    for field in ENCODED_ABSTRACT_FIELDS:
        if field in article:
            article[field] = UNICODE_HANDLER.ent2u(article[field])
    for field in HTML_ENCODED_ABSTRACT_FIELDS:
        if field in article:
            article[field] = UNICODE_HANDLER.ent2xml(article[field])

    switch_date = article['Publication Date'].split('/')
    article['Publication Date'] = switch_date[1] + '/' + switch_date[0]

    return as_needed(article)


import re

COLLABORATION_PAT = re.compile(r"(?P<collaboration>[(\[]*[A-Za-z\s\-\/]+\s[Cc]ollaboration[s]?\s*[A-Z\.]*[\s.,)\]]+)")
COMMA_BEFORE_AND = re.compile(r"(,)?(\s+and)", re.IGNORECASE)
def get_collaborators(ref_string):
    """
    collabrators are listed at the beginning of the author list,
    return the length, if there are any collaborators listed

    :param ref_string:
    :return:
    """
    match = COLLABORATION_PAT.findall(COMMA_BEFORE_AND.sub(r',\2', ref_string))
    if len(match) > 0:
        collaboration = match[-1]
        return ref_string.find(collaboration), len(collaboration)

    return 0, 0

def get_length_matched_authors(ref_string, matches):
    """
    make sure the author was matched from the beginning of the reference

    :param ref_string:
    :param matched:
    :return:
    """
    matched_str = ', '.join([' '.join(list(filter(None, author))).strip() for author in matches])
    count = 0
    for sub, full in zip(matched_str, ref_string):
        if sub != full:
            break
        count += 1
    return count

# all author lists coming in need to be case-folded
# replaced van(?: der) with van|van der
SINGLE_NAME_RE = "(?:(?:d|de|de la|De|des|Des|in '[a-z]|van|van der|van den|van de|von|Mc|[A-Z]')[' ]?)?[A-Z][a-z]['A-Za-z]*"
LAST_NAME_PAT = re.compile(r"%s(?:[- ]%s)*" % (SINGLE_NAME_RE, SINGLE_NAME_RE))

ETAL = r"(([\s,]*and)?[\s,]*[Ee][Tt][.\s]*[Aa][Ll][.\s]+)?"
LAST_NAME_SUFFIX = r"([,\s]*[Jj][Rr][.,\s]+)?"

# This pattern should match author names with initials behind the last name
TRAILING_INIT_PAT = re.compile(r"(?P<last>%s%s)\s*,?\s+"
                               r"(?P<first>(?:[A-Z]\.[\s-]*)+)" % (LAST_NAME_PAT.pattern, LAST_NAME_SUFFIX))
# This pattern should match author names with initals in front of the last name
LEADING_INIT_PAT = re.compile(r"(?P<first>(?:[A-Z]\.[\s-]*)+) "
                              r"(?P<last>%s%s)\s*,?" % (LAST_NAME_PAT.pattern, LAST_NAME_SUFFIX))

# This pattern should match author names with first/middle name behind the last name
TRAILING_FULL_PAT = re.compile(r"(?P<last>%s%s)\s*,?\s+"
                               r"(?P<first>(?:[A-Z][A-Za-z]+\s*)(?:[A-Z][.\s])*)" % (LAST_NAME_PAT.pattern, LAST_NAME_SUFFIX))
# This pattern should match author names with first/middle name in front of the last name
LEADING_FULL_PAT = re.compile(r"(?P<first>(?:[A-Z][A-Za-z]+\s*)(?:[A-Z][.\s])*) "
                              r"(?P<last>%s%s)\s*,?" % (LAST_NAME_PAT.pattern, LAST_NAME_SUFFIX))

def get_author_pattern(ref_string):
    """
    returns a pattern matching authors in ref_string.

    The problem here is that initials may be leading or trailing.
    The function looks for patterns pointing on one or the other direction;
    if unsure, an Undecidable exception is raised.

    :param ref_string:
    :return:
    """
    # if there is a collaboration included in the list of authors
    # remove that to be able to decide if the author list is trailing or ending
    collaborators_idx, collaborators_len = get_collaborators(ref_string)

    patterns = [TRAILING_INIT_PAT, LEADING_INIT_PAT, TRAILING_FULL_PAT, LEADING_FULL_PAT]
    lengths = [0] * len(patterns)

    # if collaborator is listed before authors
    if collaborators_idx != 0:
        for i, pattern in enumerate(patterns):
            # lengths[i] = len(pattern.findall(ref_string[collaborators_len:]))
            lengths[i] = get_length_matched_authors(ref_string[collaborators_len:], pattern.findall(ref_string[collaborators_len:]))
    else:
        for i, pattern in enumerate(patterns):
            # lengths[i] = len(pattern.findall(ref_string))
            lengths[i] = get_length_matched_authors(ref_string, pattern.findall(ref_string))

    indices_max = [index for index, value in enumerate(lengths) if value == max(lengths)]
    if len(indices_max) != 1:
        indices_match = [index for index, value in enumerate(lengths) if value > 0]

        # if there were multiple max and one min, pick the min
        if len(indices_match) - len(indices_max) == 1:
            return patterns[min(indices_match)]

        # see which two or more patterns recognized this reference, turn the indices_max to on/off, convert to binary,
        # and then decimal, note that 1, 2, 4, and 8 do not get there
        on_off_value = int(''.join(['1' if i in indices_max else '0' for i in list(range(4))]),2)

        # all off, all on, or contradiction (ie, TRAILING on from one set of INIT or FULL with LEADING on from the other)
        if on_off_value in [0, 6, 9, 12, 15]:
            return None

        # 0011 pick fourth pattern
        # this happens when there is no init and last-first is not distinguishable with first-last,
        # so pick last-first
        if on_off_value == 3:
            return patterns[2]
        # 0101 and 0111 pick second pattern
        if on_off_value in [5, 7]:
            return patterns[1]
        # 1010 and 1011 pick first pattern
        if on_off_value in [10, 11]:
            return patterns[0]
        # 1101 pick fourth pattern
        if on_off_value == 13:
            return patterns[3]
        # 1110 pick third pattern
        if on_off_value == 14:
            return patterns[2]

    return patterns[indices_max[0]]

AND_HOOK = re.compile(r"((?:[A-Z][.\s])?%s%s[,\s]+|%s%s[,\s]+(?:[A-Z][.\s])?)+(\b[Aa]nd|\s&)\s((?:[A-Z][.\s])?%s%s|%s%s(?:[A-Z][.\s])?)"
                      %(LAST_NAME_PAT.pattern, LAST_NAME_SUFFIX, LAST_NAME_PAT.pattern, LAST_NAME_SUFFIX,
                        LAST_NAME_PAT.pattern, LAST_NAME_SUFFIX, LAST_NAME_PAT.pattern, LAST_NAME_SUFFIX))
def get_authors_last_attempt(ref_string):
    """
    last attempt to identify author(s)

    :param ref_string:
    :return:
    """
    # if there is an and, used that as an anchor
    match = AND_HOOK.match(ref_string)
    if match:
        return match.group(0).strip()
    # grab first author's lastname and include etal
    match = LAST_NAME_PAT.findall(ref_string)
    if match:
        return '; '.join(match)
    return None

REMOVE_AND = re.compile(r"(,?\s+and\s+)", re.IGNORECASE)
def normalize_author_list(author_string):
    """
    tries to bring author_string in the form AuthorLast1; AuthorLast2

    If the function cannot make sense of author_string, it returns it unchanged.

    :param author_string:
    :return:
    """
    author_string = REMOVE_AND.sub(',', author_string)
    pattern = get_author_pattern(author_string)
    if pattern:
        return "; ".join("%s, %s" % (match.group("last"), match.group("first")[0])
                         for match in pattern.finditer(author_string)).strip()

    authors = get_authors_last_attempt(author_string)
    if authors:
        return authors
    return author_string

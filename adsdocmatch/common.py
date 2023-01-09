"""
The module contains methods that are called from both match_to_pub and match_to_arxiv modules.

"""

import os
from adsputils import setup_logging

logger = setup_logging('docmatch_log_common')

def get_filenames(filename):
    """
    read input file and return list of arXiv metadata full filenames

    :param filename:
    :return:
    """
    filenames = []
    try:
        with open(filename, 'r') as fp:
            for filename in fp.readlines():
                filenames.append(filename.rstrip('\r\n'))
    except Exception as e:
        logger.error('Unable to open/read input file', e)
    return filenames

def format_results(results, separator):
    """

    :param results:
    :param separator:
    :return:
    """
    if results.get('matched_bibcode', None):
        match = separator.join([str(results.get(field, '')) for field in ['source_bibcode', 'matched_bibcode', 'label', 'confidence', 'score', 'comment']])
        if len(results.get('inspection', [])) > 1:
            return match, results['inspection']
        # single match
        return match, None
    # when error, return status_code
    return '%s status_code=%s'%(results.get('comment', ''), results.get('status_code', '')), None

def write_for_inspection_hits(result_filename, a_match, inspection_hits):
    """
    for inspection list, also include matches, first write the match, and then if there are inspection_hits wrote those

    :param result_filename:
    :param a_match:
    :param inspection_hits:
    :return:
    """
    csv_file = result_filename + '.csv'
    if os.path.exists(csv_file):
        fp = open(csv_file, 'a')
    else:
        fp = open(csv_file, 'w')
        # new file, write header line
        fp.write('source bibcode (link),verified bibcode,matched bibcode (link),label,confidence,matched scores,comment\n')

    hyperlink_format = '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/%s/abstract"",""%s"")"'
    double_quote = '"%s"'

    # include match only if inpsection_hits is empty
    # otherwise write inspection_hits
    if not inspection_hits and a_match:
        a_match_parts = a_match.split('\t')
        if len(a_match_parts) == 6:
            source_bibcode = a_match_parts[0]
            matched_bibcode = a_match_parts[1]
            fp.write('%s,,%s,%s,%s,%s,%s\n' % (
                hyperlink_format % (source_bibcode, source_bibcode),
                hyperlink_format % (matched_bibcode, matched_bibcode),
                a_match_parts[2],
                a_match_parts[3],
                double_quote % a_match_parts[4],
                double_quote % a_match_parts[5],
            ))
        else:
            # it is an error write it out
            fp.write("%s\n"%a_match)
    elif inspection_hits:
        for item in inspection_hits:
            source_bibcode = item['source_bibcode']
            matched_bibcode = item['matched_bibcode']
            # source bibcode, empty column reserved for curators adding verified bibcode, and the score
            fp.write('%s,,%s,%s,%s,%s,%s\n' % (
                hyperlink_format % (source_bibcode, source_bibcode),
                hyperlink_format % (matched_bibcode, matched_bibcode),
                item['label'],
                item['confidence'],
                double_quote % item['scores'],
                double_quote % item['comment'],
            ))
    fp.close()
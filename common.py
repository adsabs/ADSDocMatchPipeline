"""
The module contains methods that are called from both match_to_pub and match_to_arxiv modules.

"""

import os
from adsputils import setup_logging

logger = setup_logging('docmatch_log')

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
        match = separator.join([str(results.get(field, '')) for field in ['source_bibcode', 'matched_bibcode', 'confidence', 'score', 'comment']])
        if results.get('inspection', None):
            # found low confidence match or multiple matches
            for_inspection = [results.get('source_bibcode'), results.get('confidence'),
                              results['inspection'].get('bibcodes'), results['inspection'].get('scores'),
                              results['inspection'].get('comment')]
            return match, for_inspection
        # single match
        return match, None
    # when error, return status_code
    return '%s status_code=%s'%(results.get('comment', ''), results.get('status_code', '')), None

def write_for_inspection_hits(result_filename, inspection_hits):
    """

    :param result_filename:
    :param inspection_hits:
    :return:
    """
    csv_file = result_filename + '.csv'
    if os.path.exists(csv_file):
        fp = open(csv_file, 'a')
    else:
        fp = open(csv_file, 'w')
        # new file, write header line
        fp.write('source bibcode (link),verified bibcode,confidence,matched bibcode (link),matched scores,matched bibcode (link),matched scores,comment\n')

    hyperlink_format = '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/%s/abstract"",""%s"")",'
    score_format = '"%s",'
    # source bibcode, empty column reserved for curators adding verified bibcode, and the score
    csv_line = hyperlink_format%(inspection_hits[0], inspection_hits[0]) + ',' + score_format%(inspection_hits[1])
    for bibcode, score in zip(inspection_hits[2], inspection_hits[3]):
        csv_line += hyperlink_format%(bibcode,bibcode) + score_format%(score)
    comment = (', ,' if len(inspection_hits[2]) == 1 else '') + '"%s"'%inspection_hits[4]
    csv_line += comment
    fp.write('%s\n'%(csv_line))
    fp.close()
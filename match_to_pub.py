import sys, os
import argparse
from adsputils import setup_logging
from pyingest.parsers.arxiv import ArxivParser
from from_oracle import get_matches
from common import get_filenames, format_results, write_for_inspection_hits
import re

logger = setup_logging('docmatch_log')

MUST_MATCH = ['Astrophysics', 'Physics']
DOCTYPE_THESIS = ['phdthesis', 'mastersthesis']

ARXIV_PARSER = ArxivParser()

re_admin_notes = re.compile(r'arXiv admin note: (.*)$')
def add_metadata_comment(results, comments):
    """

    :param results:
    :param comments:
    :return:
    """
    match = re_admin_notes.search(comments)
    if match:
        admin_notes = match.group(1)
        results['comment'] = ('%s %s'%(results.get('comment', ''), admin_notes)).strip()
        for inspection in results.get('inspection', []):
            inspection['comment'] = ('%s %s'%(inspection.get('comment', ''), admin_notes)).strip()
    return results

re_doi = re.compile(r'doi:\s*(10\.\d{4,9}/\S+\w)', re.IGNORECASE)
re_thesis = re.compile(r'(thesis)', re.IGNORECASE)
def match_to_pub(filename):
    """
    read and parse arXiv metadata file
    return list of bibcodes and scores for the matches in decreasing order

    :param filename:
    :return:
    """
    try:
        with open(filename, 'rb') as arxiv_fp:
            metadata = ARXIV_PARSER.parse(arxiv_fp)
            comments = ' '.join(metadata.get('comments', []))
            # extract doi out of comments if there are any
            match = re_doi.search(comments)
            if match:
                metadata['doi'] = match.group(1)
            else:
                doi = metadata.get('properties', {}).get('DOI', None)
                if doi:
                    metadata['doi'] = doi.replace('doi:', '')
            match = re_thesis.search(comments)
            if match:
                match_doctype = DOCTYPE_THESIS
            else:
                match_doctype = None
            mustmatch = any(category in metadata.get('keywords', '') for category in MUST_MATCH)
            return add_metadata_comment(get_matches(metadata, 'eprint', mustmatch, match_doctype), comments)
    except Exception as e:
        logger.error('Exception: %s'%e)
        return

def single_match_to_pub(arXiv_filename):
    """
    when user submits a single arxiv metadata file for matching

    :param arxiv_filename:
    :return:
    """
    results = match_to_pub(arXiv_filename)
    if results:
        return format_results(results, '\t')
    return None,None

def single_match_output(arXiv_filename):
    """

    :param arXiv_filename:
    :return:
    """
    a_match, for_inspection = single_match_to_pub(arXiv_filename)
    print('Match? -->', a_match)
    if for_inspection:
        print('Needs inspection -->', for_inspection)


def batch_match_to_pub(filename, result_filename):
    """

    :param filename:
    :param result_filename:
    :return:
    """
    filenames = get_filenames(filename)
    if len(filenames) > 0:
        if result_filename:
            # output file
            with open(result_filename, 'w') as fp:
                # one file at a time, parse and score, and then write the result to the file
                for arXiv_filename in filenames:
                    a_match, for_inspection = single_match_to_pub(arXiv_filename)
                    fp.write('%s\n'%a_match)
                    write_for_inspection_hits(result_filename, a_match, for_inspection)
        else:
            for arXiv_filename in filenames:
                single_match_output(arXiv_filename)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Match arXiv with Publisher')
    parser.add_argument('-i', '--input', help='the path to an input file containing list of arXiv metadata files for processing.')
    parser.add_argument('-s', '--single', help='the path to a single metadata file for processing.')
    parser.add_argument('-o', '--output', help='the output file name to write the result, else the result shall be written to console.')
    args = parser.parse_args()
    if args.input:
        batch_match_to_pub(filename=args.input, result_filename=args.output)
    elif args.single:
        single_match_output(arXiv_filename=args.single)
    # test mode
    else:
        arXiv_path = os.environ.get('ARXIV_DOCMATCHING_PATH')

        matched, _ = single_match_to_pub(arXiv_filename='%s%s'%(arXiv_path,'1701/00200'))
        matched = matched.split('\t')
        assert(matched[0] == '2017arXiv170100200T')
        assert(matched[1] == '...................')
        assert(matched[2] == 'Not Match')
        assert(matched[3] == '0')
        assert(matched[4] == '')
        assert(matched[5] == 'No matches with Abstract, trying Title. No document was found in solr matching the request.')

        matched, _ = single_match_to_pub(arXiv_filename='%s%s'%(arXiv_path,'1801/01021'))
        matched = matched.split('\t')
        assert(matched[0] == '2018arXiv180101021F')
        assert(matched[1] == '2018ApJS..236...24F')
        assert(matched[2] == 'Match')
        assert(matched[3] == '1.98266')
        assert(matched[4] == "{'abstract': 0.98, 'title': 0.98, 'author': 1, 'year': 1, 'doi': 1.0}")
        assert(matched[5] == '')

        matched, _ = single_match_to_pub(arXiv_filename='%s%s'%(arXiv_path,'0708/1752'))
        matched = matched.split('\t')
        assert(matched[0] == '2007arXiv0708.1752V')
        assert(matched[1] == '2007A&A...474..653V')
        assert(matched[2] == 'Match')
        assert(matched[3] == '1.984395')
        assert(matched[4] == "{'abstract': 1.0, 'title': 1.0, 'author': 1, 'year': 1, 'doi': 1.0}")
        assert(matched[5] == '')

        print('all tests pass')

    sys.exit(0)

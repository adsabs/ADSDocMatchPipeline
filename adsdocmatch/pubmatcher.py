import sys, os
import argparse
from adsputils import setup_logging
from pyingest.parsers.arxiv import ArxivParser
from .from_oracle import get_matches
from .common import get_filenames, format_results, write_for_inspection_hits
import re
import time

logger = setup_logging('docmatch_log_match_to_pub')

MUST_MATCH = ['Astrophysics', 'Physics']
DOCTYPE_THESIS = ['phdthesis', 'mastersthesis']

re_doi = re.compile(r'doi:\s*(10\.\d{4,9}/\S+\w)', re.IGNORECASE)
re_doctype_thesis = re.compile(r'\b(thesis)\b', re.IGNORECASE)
re_doctype_errata = re.compile(r'(^errat(a|um))\b', re.IGNORECASE)
re_doctype_bookreview = re.compile(r'\bbook[s|\s|\-]*review[s|ed]*', re.IGNORECASE)
re_admin_notes = re.compile(r'arXiv admin note: (.*)$')


class PubMatcher(object):

    def __init__(self):
        self.parser = ArxivParser()
        pass


    def _add_metadata_comment(self, results, comments):
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

    def _match_to_pub(self, filename):
        """
        read and parse arXiv metadata file
        return list of bibcodes and scores for the matches in decreasing order
        :param filename:
        :return:
        """
        try:
            with open(filename, 'rb') as arxiv_fp:
                metadata = self.parser.parse(arxiv_fp)
                comments = ' '.join(metadata.get('comments', []))
                # extract doi out of comments if there are any
                match = re_doi.search(comments)
                if match:
                    metadata['doi'] = match.group(1)
                else:
                    doi = metadata.get('properties', {}).get('DOI', None)
                    if doi:
                        metadata['doi'] = doi.replace('doi:', '')
                match_doctype = None
                title = metadata.get('title')
                # check title for erratum
                match = re_doctype_errata.search(title)
                if match:
                    match_doctype = ['erratum']
                else:
                    match = re_doctype_bookreview.search(title)
                    if match:
                        match_doctype = ['bookreview']
                    else:
                        # check both comments and title for thesis
                        match = re_doctype_thesis.search("%s %s"%(comments, title))
                        if match:
                            match_doctype = ['phdthesis', 'mastersthesis']
                mustmatch = any(category in metadata.get('keywords', '') for category in MUST_MATCH)
                return self._add_metadata_comment(get_matches(metadata, 'eprint', mustmatch, match_doctype), comments)
        except Exception as e:
            logger.error('Exception: %s'%e)
            return

    def _single_match_to_pub(self, arXiv_filename):
        """
        when user submits a single arxiv metadata file for matching
        :param arxiv_filename:
        :return:
        """
        results = self._match_to_pub(arXiv_filename)
        if results:
            return format_results(results, '\t')
        return None,None
    
    def single_match_output(self, arXiv_filename):
        """
        :param arXiv_filename:
        :return:
        """
        a_match, for_inspection = self._single_match_to_pub(arXiv_filename)
        print('Match? -->', a_match)
        if for_inspection:
            print('Needs inspection -->', for_inspection)
    
    
    def batch_match_to_pub(self, filename, result_filename):
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
                        a_match, for_inspection = self._single_match_to_pub(arXiv_filename)
                        fp.write('%s\n'%a_match)
                        write_for_inspection_hits(result_filename, a_match, for_inspection)
                        # wait a second before the next attempt
                        time.sleep(1)
            else:
                for arXiv_filename in filenames:
                    single_match_output(arXiv_filename)
    
    
    def do_tests(self):
        arXiv_path = os.environ.get('ARXIV_DOCMATCHING_PATH')

        matched, _ = self._single_match_to_pub(arXiv_filename='%s%s'%(arXiv_path,'1701/00200'))
        matched = matched.split('\t')
        assert(matched[0] == '2017arXiv170100200T')
        assert(matched[1] == '...................')
        assert(matched[2] == 'Not Match')
        assert(matched[3] == '0')
        assert(matched[4] == '')
        assert(matched[5] == 'No matches with Abstract, trying Title. No document was found in solr matching the request.')

        matched, _ = self._single_match_to_pub(arXiv_filename='%s%s'%(arXiv_path,'1801/01021'))
        matched = matched.split('\t')
        assert(matched[0] == '2018arXiv180101021F')
        assert(matched[1] == '2018ApJS..236...24F')
        assert(matched[2] == 'Match')
        assert(matched[3] == '0.9957643')
        # assert(matched[4] == "{'abstract': 0.98, 'title': 0.98, 'author': 1, 'year': 1, 'doi': 1.0}")
        assert(matched[5] == '')

        matched, _ = self._single_match_to_pub(arXiv_filename='%s%s'%(arXiv_path,'0708/1752'))
        matched = matched.split('\t')
        assert(matched[0] == '2007arXiv0708.1752V')
        assert(matched[1] == '2007A&A...474..653V')
        assert(matched[2] == 'Match')
        assert(matched[3] == '0.9961402')
        # assert(matched[4] == "{'abstract': 1.0, 'title': 1.0, 'author': 1, 'year': 1, 'doi': 1.0}")
        assert(matched[5] == '')

        print('all tests pass')


def get_args():
    try:
        parser = argparse.ArgumentParser(description='Match arXiv with Publisher')
        parser.add_argument('-i', '--input', help='the path to an input file containing list of arXiv metadata files for processing.')
        parser.add_argument('-s', '--single', help='the path to a single metadata file for processing.')
        parser.add_argument('-o', '--output', help='the output file name to write the result, else the result shall be written to console.')
        args = parser.parse_args()
        return args
    except Exception as err:
        logger.error("Unable to get command line arguments: %s" % err)


def main():
    args = get_args()
    matcher = PubMatcher()
    if args.input:
        matcher.batch_match_to_pub(filename=args.input,
                                   result_filename=args.output)
    elif args.single:
        matcher.single_match_output(arXiv_filename=args.single)
    else:
        # test mode
        matcher.do_tests()

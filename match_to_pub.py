import sys, os
import argparse
from pyingest.parsers.arxiv import ArxivParser
from from_oracle import get_matches
import re

MUST_MATCH = ['Astrophysics', 'Physics']
DOCTYPE_THESIS = ['phdthesis', 'mastersthesis']

ARXIV_PARSER = ArxivParser()

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
        print('Unable to open/read input file', e)
    return filenames

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
        with open(filename, 'r') as arxiv_fp:
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
            return get_matches(metadata, 'eprint', mustmatch, match_doctype)
    except:
        return None

def join_hybrid_elements(hybrid_list, separator):
    """

    :param hybrid_list:
    :param separator:
    :return:
    """
    return separator.join(str(x) for x in hybrid_list)

def single_match_to_pub(arXiv_filename):
    """
    when user submits a single arxiv metadata file for matching

    :param arxiv_filename:
    :return:
    """
    return join_hybrid_elements(match_to_pub(arXiv_filename), '\t')

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
                    fp.write('%s\r\n'%single_match_to_pub(arXiv_filename))
        else:
            for arXiv_filename in filenames:
                print(single_match_to_pub(arXiv_filename))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Match arXiv with Publisher')
    parser.add_argument('-i', '--input', help='the path to an input file containing list of arXiv metadata files for processing.')
    parser.add_argument('-s', '--single', help='the path to a single metadata file for processing.')
    parser.add_argument('-o', '--output', help='the output file name to write the result, else the result shall be written to console.')
    args = parser.parse_args()
    if args.input:
        batch_match_to_pub(filename=args.input, result_filename=args.output)
    elif args.single:
        print single_match_to_pub(arXiv_filename=args.single)
    # test mode
    else:
        assert(single_match_to_pub(arXiv_filename=eval(os.environ.get('PUB_DOCMATCHING_TEST'))[0]) ==
               "2020arXiv200914323K\t...................\t0\tNo result from solr with Abstract, trying Title. No document was found in solr matching the request.")
        assert(single_match_to_pub(arXiv_filename=eval(os.environ.get('PUB_DOCMATCHING_TEST'))[1]) ==
               "2018arXiv180101021F\t2018ApJS..236...24F\t1\t{u'title': 0.98, u'abstract': 0.97, u'year': 1, u'author': 1.0}	No result from solr with DOI.")
        print 'both tests pass'
    sys.exit(0)

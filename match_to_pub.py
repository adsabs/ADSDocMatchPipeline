import os, sys
import argparse
from pyingest.parsers.arxiv import ArxivParser
from from_oracle import get_matches
import time

def read_metadata(filename):
    """
    read arxiv metadata file and return a dict
    containing authors, title, abstract, and bibcode

    :param filename:
    :return:
    """
    arXiv_metadata = []
    try:
        with open(filename, 'rU') as fp:
            parser = ArxivParser()
            for arXiv_filename in fp.readlines():
                with open(arXiv_filename[:-1], 'rU') as arxiv_fp:
                    arXiv_metadata.append(parser.parse(arxiv_fp))
    except Exception as e:
        print('Unable to open/read input file', e)
    return arXiv_metadata

def batch_match_to_pub(filename, result_filename):
    """

    :param filename:
    :param result_filename:
    :return:
    """
    start_time = time.time()
    arXiv_metadata = read_metadata(filename)
    if result_filename:
        with open(result_filename, 'w') as fp:
            for arXiv in arXiv_metadata:
                fp.write('%s\r\n'%str(get_matches(arXiv, 'eprint')))
    else:
        for arXiv in arXiv_metadata:
            print(get_matches(arXiv, 'eprint'))
    end_time = time.time()
    print('duration:', (end_time-start_time)*1000, 'ms')

def single_match_to_pub(arxiv_filename):
    """

    :param arxiv_filename:
    :return:
    """
    with open(arxiv_filename, 'rU') as arxiv_fp:
        print(get_matches(ArxivParser().parse(arxiv_fp), 'eprint'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Match arXiv with Publisher')
    parser.add_argument('-i', '--input', help='the path to an input file containing list of arXiv metadata files for processing.')
    parser.add_argument('-s', '--single', help='the path to a single metadata file for processing.')
    parser.add_argument('-o', '--output', help='the output file name to write the result, else the result shall be written to console.')
    args = parser.parse_args()
    if args.input:
        batch_match_to_pub(filename=args.input, result_filename=args.output)
    elif args.single:
        single_match_to_pub(arxiv_filename=args.single)
    sys.exit(0)

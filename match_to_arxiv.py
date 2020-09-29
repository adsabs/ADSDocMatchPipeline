import sys
import argparse
from pub_parser import get_pub_metadata
from from_oracle import get_matches
import time

def read_metadata(filename):
    """
    read pub metadata file and return a dict
    containing authors, title, abstract, and bibcode

    :param filename:
    :return:
    """
    pub_metadata = []
    try:
        with open(filename, 'rU') as fp:
            for pub_filename in fp:
                with open(pub_filename.rstrip('\r\n'), 'rU') as pub_fp:
                    print 'reading and parsing', pub_filename.rstrip('\r\n')
                    pub_metadata.append(get_pub_metadata(pub_fp.read()))
    except Exception as e:
        print('Unable to open/read input file', e)
    return pub_metadata

def batch_match_to_arXiv(filename, result_filename):
    """

    :param filename:
    :param result_filename:
    :return:
    """
    start_time = time.time()
    pub_metadata = read_metadata(filename)
    if result_filename:
        with open(result_filename, 'w') as fp:
            for pub in pub_metadata:
                fp.write('%s\r\n' % str(get_matches(pub, 'article')))
    else:
        for pub in pub_metadata:
           print(get_matches(pub, 'article'))
    end_time = time.time()
    print('duration:', (end_time - start_time) * 1000, 'ms')

def signle_match_to_arXiv(pub_filename):
    """

    :param pub_filename:
    :return:
    """
    with open(pub_filename, 'rU') as pub_fp:
        print(get_matches(get_pub_metadata(pub_fp.read()), 'article'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Match Publisher with arXiv')
    parser.add_argument('-i', '--input', help='the path to an input file containing list of arXiv metadata files for processing.')
    parser.add_argument('-s', '--single', help='the path to a single metadata file for processing.')
    parser.add_argument('-o', '--output', help='the output file name to write the result, else the result shall be written to console.')
    args = parser.parse_args()
    if args.input:
        batch_match_to_arXiv(filename=args.input, result_filename=args.output)
    elif args.single:
        signle_match_to_arXiv(pub_filename=args.single)
    sys.exit(0)


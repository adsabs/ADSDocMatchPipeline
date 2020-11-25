import sys, os
import argparse
from pub_parser import get_pub_metadata
from from_oracle import get_matches

def get_filenames(filename):
    """
    read input file and return list of pub metadata full filenames

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

def match_to_arXiv(filename):
    """
    read and parse arXiv metadata file
    return list of bibcodes and scores for the matches in decreasing order

    :param filename:
    :return:
    """
    try:
        with open(filename, 'r') as pub_fp:
            return get_matches(get_pub_metadata(pub_fp.read()), 'article')
    except:
        return None

def join_hybrid_elements(hybrid_list, separator):
    """

    :param hybrid_list:
    :param separator:
    :return:
    """
    return separator.join(str(x) for x in hybrid_list)

def single_match_to_arXiv(pub_filename):
    """
    when user submits a single pub metadata file for matching

    :param pub_filename:
    :return:
    """
    return join_hybrid_elements(match_to_arXiv(pub_filename), '\t')

def batch_match_to_arXiv(filename, result_filename):
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
                    fp.write('%s\r\n'%single_match_to_arXiv(arXiv_filename))
        else:
            for arXiv_filename in filenames:
                print(single_match_to_arXiv(arXiv_filename))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Match Publisher with arXiv')
    parser.add_argument('-i', '--input', help='the path to an input file containing list of arXiv metadata files for processing.')
    parser.add_argument('-s', '--single', help='the path to a single metadata file for processing.')
    parser.add_argument('-o', '--output', help='the output file name to write the result, else the result shall be written to console.')
    args = parser.parse_args()
    if args.input:
        batch_match_to_arXiv(filename=args.input, result_filename=args.output)
    elif args.single:
        print single_match_to_arXiv(pub_filename=args.single)
    # test mode
    else:
        pub_path = os.environ.get('PUB_DOCMATCHING_PATH')

        matched = single_match_to_arXiv(pub_filename='%s%s'%(pub_path,'K47/K47-02665.abs')).split('\t')
        assert(matched[0] == '2018ApJS..236...24F')
        assert(matched[1] == '...................')
        assert(matched[2] == '0')
        assert(matched[3] == 'No result from solr with Abstract, trying Title. No document was found in solr matching the request.')

        matched = single_match_to_arXiv(pub_filename='%s%s'%(pub_path,'J05/J05-12407.abs')).split('\t')
        assert(matched[0] == '2005JASIS..56...36K')
        assert(matched[1] == '...................')
        assert(matched[2] == '0')
        assert(matched[3] == 'No matches with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request.')

        print 'both tests pass'

    sys.exit(0)

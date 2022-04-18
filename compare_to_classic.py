import sys
import argparse
import csv


def read_classic_results(classic):
    """

    :param classic:
    :return:
    """
    results = {}
    with open(classic, 'r') as fp:
        for line in fp.readlines():
            columns = line[:-1].split('\t')
            results[columns[0]] = columns[1]
    return results

def read_nowadays_results(nowadays):
    """

    :param nowadays:
    :return:
    """
    results = []
    with open(nowadays, 'r') as fp:
        for line in fp.readlines():
             results.append(line[:-1].split('\t'))
    return results

def read_nowadays_results_audit(nowadays):
    """

    :param nowadays:
    :return:
    """
    results = []
    with open(nowadays, 'r') as fp:
        for columns in csv.reader(fp, delimiter=','):
            results.append(columns)
    return results


def combine_classic_with_nowadays(classic_results, nowadays_results):
    """

    :param classic_results:
    :param nowadays_results:
    :return:
    """
    combined_results = []
    combined_results.append(['source bibcode (link)','verified bibcode','curator comment', 'classic bibcode (link)','confidence','matched bibcode (link)','matched score','comment'])

    hyperlink_format = '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/%s/abstract"",""%s"")"'
    for nowadays_result in nowadays_results:
        if len(nowadays_result) == 1:
            continue
        source_bibcode_link = hyperlink_format % (nowadays_result[0], nowadays_result[0])
        classic_bibcode = classic_results.get(nowadays_result[0], '')
        classic_bibcode_link = hyperlink_format % (classic_bibcode, classic_bibcode) if classic_bibcode else ''
        matched_bibcode_link = hyperlink_format % (nowadays_result[1], nowadays_result[1]) if not nowadays_result[1].startswith('.') else ''
        score = '"%s"'%nowadays_result[3] if nowadays_result[3] else ''
        comment = '"%s"'%nowadays_result[4] if len(nowadays_result) == 5 else ''
        combined_results.append([source_bibcode_link, '', '', classic_bibcode_link, nowadays_result[2], matched_bibcode_link, score, comment])
    return combined_results

def combine_classic_with_nowadays_audit(classic_results, nowadays_results):
    """

    :param classic_results:
    :param nowadays_results:
    :return:
    """
    combined_results = []
    header = nowadays_results[0]
    combined_results.append(header[0:2]+['curator comment', 'classic bibcode (link)']+header[2:5]+['other matched bibcode (link)','other matched scores']+header[7:])

    hyperlink_format = '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/%s/abstract"",""%s"")"'
    for nowadays_result in nowadays_results[1:]:
        source_bibcode_link = '"%s"'%nowadays_result[0].replace('"','""')
        classic_bibcode = classic_results.get(nowadays_result[0][-21:-2], '')
        classic_bibcode_link = hyperlink_format % (classic_bibcode, classic_bibcode) if classic_bibcode else ''
        matched = []
        for i in range(3,len(nowadays_result)-1,2):
            matched.append('"%s"'%nowadays_result[i].replace('"','""'))
            matched.append('"%s"'%nowadays_result[i+1])
        comment = '"%s"'%nowadays_result[-1]
        combined_results.append([source_bibcode_link,nowadays_result[1],'',classic_bibcode_link,nowadays_result[2]]+matched+[comment])
    return combined_results

def write_output(combined_results, filename):
    """
    
    :param combined_results:
    :param filename:
    :return:
    """
    with open(filename, 'w') as fp:
        for combined_result in combined_results:
            fp.write(','.join(combined_result)+'\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combine results with classic')
    parser.add_argument('-c', '--classic', help='the path to an output results file from classic.')
    parser.add_argument('-n', '--nowadays', help='the path to a output results file from docmatching.')
    parser.add_argument('-a', '--nowadays_audit', help='the path to a output cav results file from docmatching for audit.')
    parser.add_argument('-o', '--output', help='the output file name to write the combined results, else the result shall be written to console.')
    args = parser.parse_args()
    if args.classic and args.nowadays:
        classic_results = read_classic_results(args.classic)
        nowadays_results = read_nowadays_results(args.nowadays)
        if classic_results and nowadays_results:
            combined_results = combine_classic_with_nowadays(classic_results, nowadays_results)
    elif args.classic and args.nowadays_audit:
        classic_results = read_classic_results(args.classic)
        nowadays_results = read_nowadays_results_audit(args.nowadays_audit)
        if classic_results and nowadays_results:
            combined_results = combine_classic_with_nowadays_audit(classic_results, nowadays_results)
    else:
        print('not all input parameters was included, either classic and nowadays or classic and nowadays_audit is needed')
        sys.exit(1)

    if combined_results:
        if args.output:
            write_output(combined_results, args.output)
        else:
            for combined_result in combined_results:
                print('\t'.join(combined_result))
    sys.exit(0)

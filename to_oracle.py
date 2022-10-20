import os, sys
import argparse
import requests
import json
from adsputils import setup_logging

logger = setup_logging('docmatch_log_to_oracle')

def read_lines(filename):
    """

    :param filename:
    :return:
    """
    results = []
    with open(filename, 'r') as fp:
        for line in fp.readlines():
            # ignore anything after the comment sign
            line = line.split('#')[0].strip()
            result = line.split('\t')
            # has to have at least two values of bibcodes
            if len(result) < 2:
                continue
            # if confidence is missing, init
            if len(result) == 2:
                result += [os.environ.get('API_DOCMATCHING_CONFIDENCE_VALUE')]
            results.append(result)
    return results


def format_lines(lines):
    """

    :param lines:
    :return:
    """
    formatted = []
    for line in lines:
        formatted.append({
            "source_bibcode": line[0],
            "matched_bibcode": line[1],
            "confidence": line[2]
        })
    return formatted


def write_lines(filename, results):
    """

    :param filename:
    :param results:
    :return:
    """
    with open(filename, 'a') as fp:
        for result in results:
            fp.write('%s\t%s\t%s\n' % (result[0], result[1], result[2]))


def to_add(lines):
    """

    :param lines:
    :return:
    """
    max_lines_one_call = int(os.environ.get('API_DOCMATCHING_MAX_RECORDS_TO_ORACLE'))
    data = format_lines(lines)
    count = 0
    if len(data) > 0:
        for i in range(0, len(data), max_lines_one_call):
            slice_item = slice(i, i + max_lines_one_call, 1)
            response = requests.put(
                url=os.environ.get('API_DOCMATCHING_ORACLE_SERVICE_URL') + '/add',
                headers={'Content-type': 'application/json', 'Accept': 'text/plain',
                         'Authorization': 'Bearer %s' % os.environ.get('API_DOCMATCHING_TOKEN')},
                data=json.dumps(data[slice_item]),
                timeout=60
            )
            if response.status_code == 200:
                json_text = json.loads(response.text)
                print("%s:%s" % (slice_item, json_text))
                count += max_lines_one_call
            else:
                print('Oracle returned status code %d'%response.status_code)
                return 'Stopped...'
        return 'Added %d to database'%count
    return 'No data!'


def to_delete(lines):
    """

    :param lines:
    :return:
    """
    max_lines_one_call = int(os.environ.get('API_DOCMATCHING_MAX_RECORDS_TO_ORACLE'))
    data = format_lines(lines)
    results = []
    if len(data) > 0:
        for i in range(0, len(data), max_lines_one_call):
            slice_item = slice(i, i + max_lines_one_call, 1)
            response = requests.delete(
                url=os.environ.get('API_DOCMATCHING_ORACLE_SERVICE_URL') + '/delete',
                headers={'Content-type': 'application/json', 'Accept': 'text/plain',
                         'Authorization': 'Bearer %s' % os.environ.get('API_DOCMATCHING_TOKEN')},
                data=json.dumps(data[slice_item]),
                timeout=60
            )
            if response.status_code == 200:
                json_text = json.loads(response.text)
                results.append("%s:%s" % (slice_item, json_text))
            else:
                results.append("%s:%s" % (slice_item, response.text))
        return ';'.join(results)
    return 'No data!'


def query(filename):
    """

    :param filename:
    :return:
    """
    # remove the input file if it exitsted, since the subsequent calls use flag `a`.
    try:
        os.remove(filename)
    except OSError:
        pass

    start = 0
    count = 0
    headers = {'Content-type': 'application/json', 'Accept': 'application/json',
               'Authorization': 'Bearer %s' % os.environ.get('API_DOCMATCHING_TOKEN')}
    url = os.environ.get('API_DOCMATCHING_ORACLE_SERVICE_URL') + '/query'
    while True:
        response = requests.post(url=url, headers=headers, data=json.dumps({'start': start}), timeout=60)
        if response.status_code == 200:
            json_dict = json.loads(response.text)
            params = json_dict['params']
            results = json_dict['results']
            print('[%d, %d]' % (start, start + len(results)))
            count += len(results)
            start += params['rows']
            if not results:
                break
            write_lines(filename, results)
    return 'Got %d records from db.' % count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Send a request to oracle service to add/delete records to/from the database, also send a request to query the database')
    parser.add_argument('-f', '--file', help='the path to a tab delimited input file for add/delete, or output file for query commands.  The input file contains triplets: source bibcode/matched bibcode/confidence, allowing comments in the file which shall be ingnored after the # sign.')
    parser.add_argument('-a', '--action', help='add, del, or query')
    args = parser.parse_args()
    if args.file and args.action:
        if args.action == 'add':
            print(to_add(read_lines(args.file)))
        elif args.action == 'del':
            print(to_delete(read_lines(args.file)))
        elif args.action == 'query':
            print(query(args.file))
        else:
            print('unrecognized action, add, del, or query are accepted only')
            sys.exit(1)
    sys.exit(0)

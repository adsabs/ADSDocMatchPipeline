import os, sys
import argparse
import requests
import json
from adsputils import setup_logging

logger = setup_logging('docmatch_log')

def read_lines(lines):
    """

    :param lines:
    :return:
    """
    results = []
    with open(lines, 'r') as fp:
        for line in fp.readlines():
             results.append(line[:-1].split('\t'))
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

def to_add(lines):
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

            response = requests.put(
                url=os.environ.get('API_DOCMATCHING_ORACLE_SERVICE_URL') + '/update',
                headers={'Content-type': 'application/json', 'Accept': 'text/plain',
                         'Authorization': 'Bearer %s'%os.environ.get('API_DOCMATCHING_TOKEN')},
                data=json.dumps(data[slice_item]),
                timeout=60
            )
            if response.status_code == 200:
                json_text = json.loads(response.text)
                results.append("%s:%s" %(slice_item, json_text))
        return ';'.join(results)
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
                         'Authorization': 'Bearer %s'%os.environ.get('API_DOCMATCHING_TOKEN')},
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send an add or delete records to oracle db')
    parser.add_argument('-f', '--file', help='the path to a tab delimited input file containing triplets: source bibcode/matched bibcode/confidence.')
    parser.add_argument('-a', '--action', help='ADD or DEL')
    args = parser.parse_args()
    if args.file and args.action:
        lines = read_lines(args.file)
        if args.action == 'ADD':
            print(to_add(lines))
        elif args.action == 'DEL':
            print(to_delete(lines))
        else:
            print('unrecognized action, ADD or DEL is accepted only')
            sys.exit(1)
    sys.exit(0)

import os, sys
import argparse
import requests
import json
from adsputils import load_config, setup_logging

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), "../"))
conf = load_config(proj_home=proj_home)

logger = setup_logging('docmatch_log_to_oracle')


class OracleManager(object):

    def __init__(self, url=None, token=None, maxlines=None, confidence=None):
        self.results = []
        self.formatted = []
        if url:
            self.url = url
        else:
            self.url = conf.get('API_DOCMATCHING_ORACLE_SERVICE_URL', None)
        if token:
            self.token = token
        else:
            self.token = conf.get('API_DOCMATCHING_TOKEN', None)
        if maxlines:
            self.max_lines_per_call = maxlines
        else:
            self.max_lines_per_call = conf.get('API_DOCMATCHING_MAX_RECORDS_TO_ORACLE', 2000)
        if confidence:
            self.confidence_value = confidence
        else:
            self.confidence_value = conf.get('API_DOCMATCHING_CONFIDENCE_VALUE', 1.1)

    def _read_lines(self, filename):
        """

        :param filename:
        :return:
        """
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
                    result += [self.confidence_value]
                self.results.append(result)


    def _format_lines(self, lines):
        """

        :param lines:
        :return:
        """
        for line in lines:
            self.formatted.append({
                "source_bibcode": line[0],
                "matched_bibcode": line[1],
                "confidence": line[2]
            })


    def _write_lines(self, filename):
        """

        :param filename:
        :param results:
        :return:
        """
        with open(filename, 'a') as fp:
            for result in self.results:
                fp.write('%s\t%s\t%s\n' % (result[0], result[1], result[2]))


    def to_add(self, filename):
        """

        :param lines:
        :return:
        """
        try:
            self._read_lines(filename)
            self._format_lines(self.results)
            data = self.formatted
        except Exception as err:
            raise Exception("error in to_add: %s" % err)
        try:
            count = 0
            url = self.url + '/add'
            headers={'Content-type': 'application/json',
                     'Accept': 'text/plain',
                     'Authorization': 'Bearer %s' % self.token}
            if not data:
                data = []
            if len(data) > 0:
                for i in range(0, len(data), self.max_lines_per_call):
                    slice_item = slice(i, i + self.max_lines_per_call, 1)
                    data = json.dumps(data[slice_item])
                    response = requests.put(
                        url=url,
                        headers=headers,
                        data=data,
                        timeout=60
                    )
                    if response.status_code == 200:
                        json_text = json.loads(response.text)
                        logger.info("%s:%s" % (slice_item, json_text))
                        count += self.max_lines_per_call
                    else:
                        logger.error('Oracle returned status code %d'%response.status_code)
                        return 'Stopped...'
                return 'Added %d to database'%count
            return 'No data!'
        except Exception as err:
            return 'Exception in to_add! %s'%err


    def to_delete(self, lines):
        """

        :param lines:
        :return:
        """
        max_lines_per_call = int(conf.get('API_DOCMATCHING_MAX_RECORDS_TO_ORACLE', 2000))
        data = self._format_lines(lines)
        results = []
        url = self.url + '/delete'
        headers={'Content-type': 'application/json',
                 'Accept': 'text/plain',
                 'Authorization': 'Bearer %s' % self.token}
        if len(data) > 0:
            for i in range(0, len(data), self.max_lines_per_call):
                slice_item = slice(i, i + self.max_lines_per_call, 1)
                data = json.dumps(data[slice_item])
                response = requests.delete(
                    url=url,
                    headers=headers,
                    data=data,
                    timeout=60
                )
                if response.status_code == 200:
                    json_text = json.loads(response.text)
                    results.append("%s:%s" % (slice_item, json_text))
                else:
                    results.append("%s:%s" % (slice_item, response.text))
            return ';'.join(results)
        return 'No data!'


    def query(self, filename, days):
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
        url = self.url + '/query'
        headers = {'Content-type': 'application/json',
                   'Accept': 'application/json',
                   'Authorization': 'Bearer %s' % self.token}
        while True:
            params = {'start': start}
            if days:
                params['days'] = int(days)
            response = requests.post(
                url=url,
                headers=headers,
                data=json.dumps(params),
                timeout=60
            )
            if response.status_code == 200:
                json_dict = json.loads(response.text)
                params = json_dict['params']
                results = json_dict['results']
                logger.info('[%d, %d]' % (start, start + len(results)))
                count += len(results)
                start += params['rows']
                if not results:
                    break
                self._write_lines(filename, results)
        return 'Got %d records from db.' % count


def main():
    try:
        args=get_args()
        om = OracleManager()
        if args.file and args.action:
            if args.action == 'add':
                logger.info(om.to_add(args.file))
            elif args.action == 'del':
                logger.info(om.to_delete(args.file))
            elif args.action == 'query':
                logger.info(om.query(args.file, args.days))
            else:
                logger.error('unrecognized action, add, del, or query are accepted only')
                sys.exit(1)
        else:
            logger.error('both filename and action params are required')
        sys.exit(0)
    except Exception as err:
        logger.error("Fatal error in main: %s" % err)

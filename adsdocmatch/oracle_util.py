import os
import requests
import json
import time
from unidecode import unidecode
import pandas as pd
import numpy as np
import re
import csv
from pathlib import Path

from adsputils import setup_logging, load_config

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), "../"))
config = load_config(proj_home=proj_home)

logger = setup_logging("docmatching", level=config.get("LOGGING_LEVEL", "WARN"), proj_home=proj_home, attach_stdout=config.get("LOG_STDOUT", "FALSE"))


class OracleUtil():

    # collabration can be listed before or after author list, also the word collabration can appear before or after the name (ie, Collabration, the ALICE, Planck Collaboration).
    COLLABORATION_PAT = re.compile(r"(?P<collaboration>[(\[]*[A-Za-z\s\-\/]+\s[Cc]ollaboration[s]?\s*[A-Z\.]*)(?:[\s.,;)\]]+|$)")
    COMMA_BEFORE_AND = re.compile(r"(,)?(\s+and)", re.IGNORECASE)
    WORDS_ONLY = re.compile(r"\w+")

    # all author lists coming in need to be case-folded
    # replaced van(?: der) with van|van der
    SINGLE_NAME_RE = "(?:(?:d|de|de la|del|De|des|Des|in '[a-z]|van|van der|van den|van de|von|Mc|[A-Z]')[' ]?)?[A-Z][a-z]['A-Za-z]*"
    LAST_NAME_PAT = re.compile(r"%s(?:[- ]%s)*" % (SINGLE_NAME_RE, SINGLE_NAME_RE))

    ETAL = r"(([\s,]*and)?[\s,]*[Ee][Tt][.\s]*[Aa][Ll][.\s]+)?"
    LAST_NAME_SUFFIX = r"([,\s]*[Jj][Rr][.,\s]+)?"

    # This pattern should match author names with initials behind the last name
    TRAILING_INIT_PAT = re.compile(r"(?P<last>%s%s)\s*,?\s+"
                                   r"(?P<first>(?:[A-Z]\.[\s-]*)+)" % (LAST_NAME_PAT.pattern, LAST_NAME_SUFFIX))
    # This pattern should match author names with initals in front of the last name
    LEADING_INIT_PAT = re.compile(r"(?P<first>(?:[A-Z]\.[\s-]*)+) "
                                  r"(?P<last>%s%s)\s*,?" % (LAST_NAME_PAT.pattern, LAST_NAME_SUFFIX))

    # This pattern should match author names with first/middle name behind the last name
    TRAILING_FULL_PAT = re.compile(r"(?P<last>%s%s)\s*,?\s+"
                                   r"(?P<first>(?:[A-Z][A-Za-z.]+\s*)(?:[A-Z][.\s])*)" % (
                                   LAST_NAME_PAT.pattern, LAST_NAME_SUFFIX))
    # This pattern should match author names with first/middle name in front of the last name
    LEADING_FULL_PAT = re.compile(r"(?P<first>(?:[A-Z][A-Za-z.]+\s*)(?:[A-Z][.\s])*) "
                                  r"(?P<last>%s%s)\s*,?" % (LAST_NAME_PAT.pattern, LAST_NAME_SUFFIX))

    AND_HOOK = re.compile(r"((?:[A-Z][.\s])?%s%s[,\s]+|%s%s[,\s]+(?:[A-Z][.\s])?)+(\b[Aa]nd|\s&)\s((?:[A-Z][.\s])?%s%s|%s%s(?:[A-Z][.\s])?)"
        % (LAST_NAME_PAT.pattern, LAST_NAME_SUFFIX, LAST_NAME_PAT.pattern, LAST_NAME_SUFFIX,
           LAST_NAME_PAT.pattern, LAST_NAME_SUFFIX, LAST_NAME_PAT.pattern, LAST_NAME_SUFFIX))

    REMOVE_AND = re.compile(r"(,?\s+and\s+)", re.IGNORECASE)

    def set_local_config_test(self):
        """
        set local config values during testing, not to make multiple attempts or wait

        :param addition:
        :return:
        """
        config.update({
            'DOCMATCHPIPELINE_API_ORACLE_SERVICE_ATTEMPTS': '1',
            'DOCMATCHPIPELINE_API_ORACLE_SERVICE_SLEEP_SEC': '0'
        })

    def get_authors_last_attempt(self, ref_string):
        """
        last attempt to identify author(s)

        :param ref_string:
        :return:
        """
        # if there is an and, used that as an anchor
        match = self.AND_HOOK.match(ref_string)
        if match:
            return match.group(0).strip()
        # grab first author's lastname and include etal
        match = self.LAST_NAME_PAT.findall(ref_string)
        if match:
            return '; '.join(match)
        return None

    def get_length_matched_authors(self, ref_string, matches):
        """
        make sure the author was matched from the beginning of the reference

        :param ref_string:
        :param matched:
        :return:
        """
        matched_str = ', '.join([' '.join(list(filter(None, author))).strip() for author in matches])
        count = 0
        for sub, full in zip(self.WORDS_ONLY.findall(matched_str), self.WORDS_ONLY.findall(ref_string)):
            if sub != full:
                break
            count += 1
        return count

    def get_collaborators(self, ref_string):
        """
        collabrators are listed at the beginning of the author list,
        return the length, if there are any collaborators listed

        :param ref_string:
        :return:
        """
        match = self.COLLABORATION_PAT.findall(self.COMMA_BEFORE_AND.sub(r',\2', ref_string))
        if len(match) > 0:
            collaboration = match[-1]
            return ref_string.find(collaboration), len(collaboration)

        return 0, 0

    def get_author_pattern(self, ref_string):
        """
        returns a pattern matching authors in ref_string.

        The problem here is that initials may be leading or trailing.
        The function looks for patterns pointing on one or the other direction;
        if unsure, an Undecidable exception is raised.

        :param ref_string:
        :return:
        """
        patterns = [self.TRAILING_INIT_PAT, self.LEADING_INIT_PAT, self.TRAILING_FULL_PAT, self.LEADING_FULL_PAT]
        lengths = [0] * len(patterns)

        for i, pattern in enumerate(patterns):
            # lengths[i] = len(pattern.findall(ref_string))
            lengths[i] = self.get_length_matched_authors(ref_string, pattern.findall(ref_string))

        indices_max = [index for index, value in enumerate(lengths) if value == max(lengths)]
        if len(indices_max) != 1:
            indices_match = [index for index, value in enumerate(lengths) if value > 0]

            # if there were multiple max and one min, pick the min
            if len(indices_match) - len(indices_max) == 1:
                return patterns[min(indices_match)]

            # see which two or more patterns recognized this reference, turn the indices_max to on/off, convert to binary,
            # and then decimal, note that 1, 2, 4, and 8 do not get there
            on_off_value = int(''.join(['1' if i in indices_max else '0' for i in list(range(4))]), 2)

            # all off, all on, or contradiction (ie, TRAILING on from one set of INIT or FULL with LEADING on from the other)
            if on_off_value in [0, 6, 9, 12, 15]:
                return None

            # 0011 pick fourth pattern
            # this happens when there is no init and last-first is not distinguishable with first-last,
            # so pick last-first
            if on_off_value == 3:
                return patterns[2]
            # 0101 and 0111 pick second pattern
            if on_off_value in [5, 7]:
                return patterns[1]
            # 1010 and 1011 pick first pattern
            if on_off_value in [10, 11]:
                return patterns[0]
            # 1101 pick fourth pattern
            if on_off_value == 13:
                return patterns[3]
            # 1110 pick third pattern
            if on_off_value == 14:
                return patterns[2]

        return patterns[indices_max[0]]

    def normalize_author_list(self, author_string):
        """
        tries to bring author_string in the form AuthorLast1; AuthorLast2

        If the function cannot make sense of author_string, it returns it unchanged.

        :param author_string:
        :return:
        """
        # if there is a collaboration included in the list of authors
        # remove that to be able to decide if the author list is trailing or ending
        collaborators_idx, collaborators_len = self.get_collaborators(author_string)

        # if there is a collaborator
        if collaborators_len > 0:
            collaborator = author_string[collaborators_idx:collaborators_idx+collaborators_len].strip()
            # if collaborator is listed before authors
            if collaborators_idx == 0:
                author_string = author_string[collaborators_len+1:]
            else:
                author_string = author_string[:collaborators_idx]
        else:
            collaborator = ""

        author_string = unidecode(self.REMOVE_AND.sub(',', author_string))
        pattern = self.get_author_pattern(author_string)
        if pattern:
            authors = "; ".join("%s, %s" % (match.group("last"), match.group("first")[0])
                             for match in pattern.finditer(author_string)).strip()
            if collaborator:
                return "%s; %s"%(collaborator, authors)
            else:
                return authors

        authors = self.get_authors_last_attempt(author_string)
        if authors:
            return authors
        return author_string

    def extract_doi(self, metadata):
        """

        :param metadata:
        :return:
        """
        comments = metadata.get('comments', [])
        dois = []
        if comments:
            try:
                dois = [comment.split('doi:')[1].strip(';').strip(',').strip('.') for comment in comments if comment.startswith('doi')]
            except:
                pass
        doi = [metadata.get('doi', '')]
        if dois:
            for one in dois:
                if one not in doi:
                    doi.append(one)
        if not ''.join(doi):
            return None
        return list(filter(None, doi))

    def get_matches(self, metadata, doctype, must_match=False, match_doctype=None):
        """

        :param metadata:
        :param doctype:
        :param must_match:
        :param match_doctype: list of doctypes, if specified only this type of doctype is matched
        :return:
        """
        results = []
        try:
            # 8/31 abstract can be empty, since oracle can match with title
            payload = {'abstract': metadata.get('abstract', '').replace('\n', ' '),
                       'title': metadata['title'].replace('\n', ' '),
                       'author': self.normalize_author_list(metadata['authors']),
                       'year': metadata['pubdate'][:4],
                       'doctype': doctype,
                       'bibcode': metadata['bibcode'],
                       'doi': self.extract_doi(metadata),
                       'mustmatch': must_match,
                       'match_doctype': match_doctype}
        except KeyError as e:
            results.append({
                'source_bibcode' : metadata['bibcode'],
                'comment' : 'Exception: KeyError, %s missing.' % str(e),
                'status_code': 'did not send request to oracle service'})

            return results

        sleep_sec = int(config.get('DOCMATCHPIPELINE_API_ORACLE_SERVICE_SLEEP_SEC', 5))
        try:
            num_attempts = int(config.get('DOCMATCHPIPELINE_API_ORACLE_SERVICE_ATTEMPTS', 5))
            for i in range(num_attempts):
                response = requests.post(
                    url=config.get('DOCMATCHPIPELINE_API_ORACLE_SERVICE_URL', 'http://localhost') + '/docmatch_add',
                    headers={'Authorization': 'Bearer %s' % config.get('DOCMATCHPIPELINE_API_TOKEN', '')},
                    data=json.dumps(payload),
                    timeout=60
                )
                status_code = response.status_code
                if status_code == 200:
                    logger.info('Got 200 for status_code at attempt # %d' % (i + 1))
                    break
                # if got 5xx errors from oracle, per alberto, sleep for five seconds and try again, attempt 3 times
                elif status_code in [502, 504]:
                    logger.info('Got %d status_code from oracle, waiting %d second and attempt again.' % (
                    status_code, num_attempts))
                    time.sleep(sleep_sec)
                # any other error, quit
                else:
                    logger.info('Got %s status_code from a call to oracle, stopping.' % status_code)
                    break
        except Exception as e:
            status_code = 500
            logger.info('Exception %s, stopping.' % str(e))

        if status_code == 200:
            json_text = json.loads(response.text)
            if 'match' in json_text:
                confidences = [one_match['confidence'] for one_match in json_text['match']]
                # do we have more than one match with the highest confidence
                if len(confidences) > 1:
                    # when confidence is low or multiple matches are found log them to be inspected
                    # in the case of multi matches, we want to return them all, and let curators decide which, if any, is correct
                    # in the case of low confidence, we want curators to check them out and see if the match is correct,
                    for i, one_match in enumerate(json_text['match']):
                        results.append({'source_bibcode': metadata['bibcode'],
                            'confidence': one_match['confidence'],
                            'label': 'Match' if one_match['matched'] == 1 else 'Not Match',
                            'scores': str(one_match['scores']),
                            'matched_bibcode': one_match['matched_bibcode'],
                            'comment': json_text.get('comment', '') + ('Multi match: %d of %d. ' % (i + 1, len(json_text['match'])) if len(
                                json_text['match']) > 1 else '' + json_text.get('comment', '')).strip()})
                    return results
                # single match
                results.append({'source_bibcode' : metadata['bibcode'],
                    'matched_bibcode' : json_text['match'][0]['matched_bibcode'],
                    'label' : 'Match' if json_text['match'][0]['matched'] == 1 else 'Not Match',
                    'confidence' : json_text['match'][0]['confidence'],
                    'score' : json_text['match'][0]['scores'],
                    'comment' : json_text.get('comment', '')})
                return results
            # no match
            results.append({'source_bibcode' : metadata['bibcode'],
                'matched_bibcode' : '.' * 19,
                'label' : 'Not Match',
                'confidence' : 0,
                'score' : '',
                'comment' : '%s %s' % (json_text.get('comment', None), json_text.get('no match', '').capitalize())})
            return results
        # when error
        # log it
        logger.error('From oracle got status code: %d' % status_code)
        results.append({'source_bibcode': metadata['bibcode'],
            'comment' : '%s error' % metadata['bibcode'],
            'status_code' : "got %d for the last failed attempt, shall be added to rerun list." % status_code})
        return results

    def read_google_sheet(self, input_filename):
        """

        :param input_filename:
        :return:
        """
        # first get the confidence scores for ADS curated and incorrect from oracle
        ads_add = str(self.get_source_score(config['DOCMATCHPIPELINE_SOURCE_ADS']))
        incorrect_delete = str(self.get_source_score(config['DOCMATCHPIPELINE_SOURCE_INCORRECT']))

        # Generate DataFrame from input excel file
        df = pd.read_excel(input_filename)
        dt = df[['source bibcode (link)', 'curator comment', 'verified bibcode', 'matched bibcode (link)']]
        cols = {'source bibcode (link)': 'source_bib',
                'curator comment': 'curator_comment',
                'verified bibcode': 'verified_bib',
                'matched bibcode (link)': 'matched_bib'}
        dt = dt.rename(columns=cols)

        # Drop unneeded rows where curator comment is: null, 'agree', 'disagree', 'no action', 'verify', 'miss'
        array = [np.nan, 'agree', 'disagree', 'no action', 'verify', 'miss']
        dt = dt.loc[~dt['curator_comment'].isin(array)]

        # Where verified bibcode is null, insert matched bibcode
        dt['verified_bib'] = dt['verified_bib'].fillna(dt['matched_bib'])

        # Set the db actions by given vocabulary (add, delete, or update)
        dt = dt.reset_index()
        for index, row in dt.iterrows():
            # if curator comment is not in vocabulary; print flag, and drop the row
            comments = ['update', 'add', 'delete']
            if row.curator_comment not in comments:
                logger.warning('Error: Bad curator comment at', row.source_bib)
                dt.drop(index, inplace=True)

            # where curator comment is 'update', duplicate row and rewrite actions;
            # assigns delete/-1 for mistaken matched bibcodes, and add/1.1 for verified bibcode
            # 5/4/23 set to the confidence values from what we got from oracle
            if row.curator_comment == 'update':
                dt = dt.replace(row.curator_comment, ads_add)
                new_row = {'source_bib': row.source_bib,
                           'curator_comment': incorrect_delete,
                           'verified_bib': row.matched_bib,
                           'matched_bib': row.matched_bib}
                # dt = dt.append(new_row, ignore_index=True)
                dt = pd.concat([dt, pd.DataFrame.from_dict([new_row])])

            # replace curator comments; 'add':'1.1' and 'delete':'-1'
            # 5/4/23 set to the confidence values from what we got from oracle
            if row.curator_comment == 'add':
                dt = dt.replace(row.curator_comment, ads_add)
            if row.curator_comment == 'delete':
                dt = dt.replace(row.curator_comment, incorrect_delete)

        # Format columns (preprint \t publisher \t action) for txt file
        # since eprint is arXiv record matched against publisher, while pub is publisher record matched against arXiv
        eprint_filename = Path(config.get('DOCMATCHPIPELINE_EPRINT_COMBINED_FILENAME', 'eprint')).stem
        pub_filename = Path(config.get('DOCMATCHPIPELINE_PUB_COMBINED_FILENAME', 'pub')).stem
        results = []
        input_filename_base = input_filename.split('/')[-1].replace('.xlsx','')
        try:
            if eprint_filename in input_filename_base:
                results = dt[['source_bib', 'verified_bib', 'curator_comment']]
            elif pub_filename in input_filename_base:
                results = dt[['verified_bib', 'source_bib', 'curator_comment']]
        except Exception as err:
            logger.warning('Error extracting results from %s: %s' % (input_filename, err))

        if type(results) == pd.core.frame.DataFrame:
            if not results.empty:
                return results.values.tolist()
            else:
                logger.warning('No results from %s' % input_filename)
        else:
            logger.warning('Input file %s is not a valid curated sheet' % input_filename)

    def make_params(self, matches):
        """

        :param matches:
        :return:
        """
        formatted = []
        for match in matches:
            formatted.append({
                "source_bibcode": match[0],
                "matched_bibcode": match[1],
                "confidence": match[2]
            })
        return formatted

    def add_to_db(self, matches):
        """

        :param matches:
        :return:
        """
        max_lines_one_call = int(config.get('DOCMATCHPIPELINE_API_MAX_RECORDS_TO_ORACLE', 2000))
        data = self.make_params(matches)
        count = 0
        if len(data) > 0:
            for i in range(0, len(data), max_lines_one_call):
                slice_item = slice(i, i + max_lines_one_call, 1)
                response = requests.put(
                    url=config.get('DOCMATCHPIPELINE_API_ORACLE_SERVICE_URL', 'http://localhost') + '/add',
                    headers={'Content-type': 'application/json', 'Accept': 'text/plain',
                             'Authorization': 'Bearer %s' % config.get('DOCMATCHPIPELINE_API_TOKEN', '')},
                    data=json.dumps(data[slice_item]),
                    timeout=60
                )
                if response.status_code == 200:
                    json_text = json.loads(response.text)
                    logger.info("%s:%s" % (slice_item, json_text))
                    count += len(data[slice_item])
                else:
                    logger.error('Oracle returned status code %d'%response.status_code)
                    return 'Stopped...'
            return 'Added %d records to database.'%count
        return 'No data!'

    def output_query_matches(self, filename, results):
        """

        :param filename:
        :param results:
        :return:
        """
        with open(filename, 'a') as fp:
            for result in results:
                fp.write('%s\t%s\t%s\n' % (result[0], result[1], result[2]))

    def query(self, output_filename, days=None):
        """

        :param output_filename:
        :param days: optinal query filter, how many days of update to include in the query, if none, all are included
        :return:
        """
        # remove the input file if it exitsted, since the subsequent calls use flag `a`.
        try:
            os.remove(output_filename)
        except OSError:
            pass

        start = 0
        count = 0
        headers = {'Content-type': 'application/json', 'Accept': 'application/json',
                   'Authorization': 'Bearer %s' % config.get('DOCMATCHPIPELINE_API_TOKEN', '')}
        url = config.get('DOCMATCHPIPELINE_API_ORACLE_SERVICE_URL', 'http://localhost') + '/query'
        while True:
            params = {'start': start}
            if days:
                params['days'] = int(days)
            response = requests.post(url=url, headers=headers, data=json.dumps(params), timeout=60)
            if response.status_code == 200:
                json_dict = json.loads(response.text)
                params = json_dict['params']
                results = json_dict['results']
                logger.info('[%d, %d]' % (start, start + len(results)))
                count += len(results)
                start += params['rows']
                if not results:
                    break
                self.output_query_matches(output_filename, results)
        return 'Got %d records from db.' % count

    def update_db_curated_matches(self, input_filename):
        """

        :param input_filename:
        :return:
        """
        matches = self.read_google_sheet(input_filename)
        if matches:
            return self.add_to_db(matches)
        return ''

    def get_source_score_list(self):
        """

        :return:
        """
        try:
            response = requests.get(
                url=config.get('DOCMATCHPIPELINE_API_ORACLE_SERVICE_URL', 'http://localhost') + '/source_score',
                headers={'Authorization': 'Bearer %s' % config.get('DOCMATCHPIPELINE_API_TOKEN', '')},
                timeout=60
            )
            if response.status_code == 200:
                source_score = json.loads(response.text)
                return source_score.get('results', [])
            else:
                logger.info('Got %s status_code from a call to oracle, stopping.' % response.status_code)
        except Exception as e:
            logger.info('Exception %s, stopping.' % str(e))

        return []

    def get_source_score(self, source):
        """

        :param source:
        :return:
        """
        try:
            response = requests.get(
                url=config.get('DOCMATCHPIPELINE_API_ORACLE_SERVICE_URL', 'http://localhost') + '/confidence/%s'%source,
                headers={'Authorization': 'Bearer %s' % config.get('DOCMATCHPIPELINE_API_TOKEN', '')},
                timeout=60
            )
            if response.status_code == 200:
                confidence = json.loads(response.text)
                return confidence.get('confidence', None)
            else:
                logger.info('Got %s status_code from a call to oracle, stopping.' % response.status_code)
        except Exception as e:
            logger.error('Exception %s, stopping.' % str(e))

        return None

    def update_db_sourced_matches(self, input_filename, source):
        """

        :param input_filename:
        :param source:
        :return:
        """
        confidence = self.get_source_score(source)
        if confidence:
            matches = []
            with open(input_filename, 'r') as f:
                for row in csv.reader(f, delimiter='\t'):
                    matches.append(row + [confidence])
            if matches:
                return self.add_to_db(matches)
        else:
            return "Unable to get confidence for source %s from oracle."%source

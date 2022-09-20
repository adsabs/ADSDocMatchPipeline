import os
import requests
import json
import time
from adsputils import setup_logging

logger = setup_logging('docmatch_log')

def get_doi(metadata):
    """

    :param metadata:
    :return:
    """
    comments =  metadata.get('comments', [])
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
    return doi

def get_matches(metadata, doctype, mustmatch=False, match_doctype=None):
    """

    :param metadata:
    :param doctype:
    :param mustmatch:
    :param match_doctype: list of doctypes, if specified only this type of doctype is matched
    :return:
    """
    try:
        # 8/31 abstract can be empty, since oracle can match with title
        payload = {'abstract': metadata.get('abstract', '').replace('\n',' '),
                   'title': metadata['title'].replace('\n',' '),
                   'author': metadata['authors'],
                   'year': metadata['pubdate'][:4],
                   'doctype': doctype,
                   'bibcode': metadata['bibcode'],
                   'doi': get_doi(metadata),
                   'mustmatch':mustmatch,
                   'match_doctype':match_doctype}
    except KeyError as e:
        result = {}
        result['source_bibcode'] = metadata['bibcode']
        result['matched_bibcode'] = '.' * 19
        result['confidence'] = 0
        result['score'] = ''
        result['comment'] = 'Exception: KeyError, %s missing.'%str(e)
        result['inspection'].append({
            'source_bibcode': '.' * 19,
            'confidence': -1,
            'label': '',
            'scores': [0],
            'matched_bibcode': '.' * 19,
            'comment': 'Exception: KeyError, %s missing.'%str(e)
        })
        return result

    sleep_sec = int(os.environ.get('API_DOCMATCHING_ORACLE_SERVICE_SLEEP_SEC'))
    try:
        for _ in range(int(os.environ.get('API_DOCMATCHING_ORACLE_SERVICE_ATTEMPTS'))):
            response = requests.post(
                url=os.environ.get('API_DOCMATCHING_ORACLE_SERVICE_URL') + '/docmatch',
                headers={'Authorization': 'Bearer %s'%os.environ.get('API_DOCMATCHING_TOKEN')},
                data=json.dumps(payload),
                timeout=60
            )
            status_code = response.status_code
            if status_code == 200:
                break
            # if got 5xx errors from solr, per alberto, sleep for five seconds and try again, attempt 3 times
            elif status_code in [502, 504]:
                logger.info('Got %s status_code from solr, waiting 5 second and attempt again.' % status_code)
                time.sleep(sleep_sec)
            # any other error, quit
            else:
                logger.info('Got %s status_code from solr, stopping.' % status_code)
                break
    except Exception as e:
        status_code = 500
        logger.info('Exception %s, stopping.'%str(e))

    result = {}

    if status_code == 200:
        json_text = json.loads(response.text)
        if 'match' in json_text:
            confidences = [one_match['confidence'] for one_match in json_text['match']]
            # do we have more than one match with the highest confidence
            if len(confidences) > 1:
                # when confidence is low or multiple matches are found log them to be inspected
                # in the case of multi matches, we want to return them all, and let curators decide which, if any, is correct
                # in the case of low confidence, we want curators to check them out and see if the match is correct,
                # hence do not display the bibcode in the output file, direct it to another file for inspection
                # include a comment that these were added to inspection file
                result['source_bibcode'] = metadata['bibcode']
                result['matched_bibcode'] = '.'*19
                result['label'] = 'Not Match'
                result['confidence'] = 'Multi match!'
                result['score'] = ''
                result['comment'] = (json_text.get('comment', '') + ' Match(es) for this bibcode is logged in the accompanied csv file.').strip()
                result['inspection'] = []
                for i, one_match in enumerate(json_text['match']):
                    result['inspection'].append({
                        'source_bibcode': metadata['bibcode'],
                        'confidence': one_match['confidence'],
                        'label': 'Match' if one_match['matched'] == 1 else 'Not Match',
                        'scores': str(one_match['scores']),
                        'matched_bibcode': one_match['matched_bibcode'],
                        'comment': ('Multi match: %d of %d. ' % (i + 1, len(json_text['match'])) if len(json_text['match']) > 1 else '' + json_text.get('comment', '')).strip()
                    })
                return result
            # single match
            result['source_bibcode'] = metadata['bibcode']
            result['matched_bibcode'] = json_text['match'][0]['matched_bibcode']
            result['label'] = 'Match' if json_text['match'][0]['matched'] == 1 else 'Not Match'
            result['confidence'] = json_text['match'][0]['confidence']
            result['score'] = json_text['match'][0]['scores']
            result['comment'] = json_text.get('comment', '')
            return result
        # no match
        result['source_bibcode'] = metadata['bibcode']
        result['matched_bibcode'] = '.' * 19
        result['label'] = 'Not Match'
        result['confidence'] = 0
        result['score'] = ''
        result['comment'] = '%s %s'%(json_text.get('comment', None), json_text.get('no match', '').capitalize())
        return result
    # when error
    # log it
    logger.error('From solr got status code: %d'%status_code)
    result['matched_bibcode'] = None
    result['status_code'] = "got %d for the last failed attempt."%status_code
    result['comment'] = '%s error'%metadata['bibcode']
    return result

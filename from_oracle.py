import os
import requests
import json
from adsputils import setup_logging

logger = setup_logging('docmatch_log')

def get_matches(metadata, doctype, mustmatch=False, match_doctype=None):
    """

    :param metadata:
    :param doctype:
    :param mustmatch:
    :param match_doctype: list of doctypes, if specified only this type of doctype is matched
    :return:
    """
    try:
        payload = {'abstract': metadata['abstract'].replace('\n',' '),
                   'title': metadata['title'].replace('\n',' '),
                   'author': metadata['authors'],
                   'year': metadata['pubdate'][:4],
                   'doctype': doctype,
                   'bibcode': metadata['bibcode'],
                   'doi': metadata.get('doi', None),
                   'mustmatch':mustmatch,
                   'match_doctype':match_doctype}
    except KeyError as e:
        result = {}
        result['source_bibcode'] = metadata['bibcode']
        result['matched_bibcode'] = '.' * 19
        result['confidence'] = 0
        result['score'] = ''
        result['comment'] = 'Exception: KeyError, %s missing.'%str(e)
        result['inspection'] = {
            'scores': [0],
            'bibcodes': ['.' * 19],
            'comment': 'Exception: KeyError, %s missing.'%str(e)
        }
        return result

    response = requests.post(
        url='https://api.adsabs.harvard.edu/v1/oracle/matchdoc',
        headers={'Authorization': 'Bearer %s'%os.environ.get('API_DOCMATCHING_TOKEN')},
        data=payload,
        timeout=60
    )

    result = {}
    result['source_bibcode'] = metadata['bibcode']

    if response.status_code == 200:
        json_text = json.loads(response.text)
        if 'match' in json_text:
            confidences = [one_match['confidence'] for one_match in json_text['match']]
            # do we have more than one match with the highest confidence
            count = confidences.count(confidences[0])
            # low confidence or we have multi match
            if (confidences[0] > 0 and confidences[0] <= 0.5) or count > 1:
                # when confidence is low or multiple matches are found log them to be inspected
                # in the case of multi matches, we want to return them all, and let curators decide which, if any, is correct
                # in the case of low confidence, we want curators to check them out and see if the match is correct,
                # hence do not display the bibcode in the output file, direct it to another file for inspection
                # include a comment that these were added to inspection file
                result['matched_bibcode'] = '.'*19
                result['confidence'] = confidences[0]
                result['score'] = ''
                result['comment'] = (json_text.get('comment', '') + ' Match(es) for this bibcode is logged in the accompanied csv file.').strip()
                result['inspection'] = {
                    'scores': [str(score) for score in [match['scores'] for match in json_text['match']][:count]],
                    'bibcodes': [match['bibcode'] for match in json_text['match']][:count],
                    'comment': 'Multi match. ' if count > 1 else 'Low confidence. ' + '%s'%json_text.get('comment', '')
                }
                return result
            # single match
            result['matched_bibcode'] = json_text['match'][0]['bibcode']
            result['confidence'] = json_text['match'][0]['confidence']
            result['score'] = json_text['match'][0]['scores']
            result['comment'] = json_text.get('comment', '')
            return result
        # no match
        result['matched_bibcode'] = '.' * 19
        result['confidence'] = 0
        result['score'] = ''
        result['comment'] = '%s %s'%(json_text.get('comment', None), json_text.get('no match', '').capitalize())
        return result
    # when error
    # log it
    logger.error('From solr got status code: %d'%response.status_code)
    result['matched_bibcode'] = None
    result['status_code'] = response.status_code
    result['comment'] = 'error'
    return result

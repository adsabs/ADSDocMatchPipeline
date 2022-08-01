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
        url='https://api.adsabs.harvard.edu/v1/oracle/docmatch',
        headers={'Authorization': 'Bearer %s'%os.environ.get('API_DOCMATCHING_TOKEN')},
        data=payload,
        timeout=60
    )

    result = {}

    if response.status_code == 200:
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
    logger.error('From solr got status code: %d'%response.status_code)
    result['matched_bibcode'] = None
    result['status_code'] = response.status_code
    result['comment'] = 'error'
    return result

import os
import requests
import json

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
        return (metadata['bibcode'], None, e)

    response = requests.post(
        url='https://api.adsabs.harvard.edu/v1/_oracle/matchdoc',
        headers={'Authorization': 'Bearer %s'%os.environ.get('API_DOCMATCHING_TOKEN')},
        data=payload,
        timeout=60
    )

    print response.text
    if response.status_code == 200:
        json_text = json.loads(response.text)
        if 'match' in json_text:
            # do we have more than one match
            confidences = [one_match['confidence'] for one_match in json_text['match']]
            count = confidences.count(confidences[0])
            if count > 1:
                # if confidence is high with multiple matches return them all
                # this signals possible duplicate records
                if confidences[0] > 0.5:
                    scores = '|'.join(str(score) for score in [one_match['scores'] for one_match in json_text['match']][:count])
                    bibcodes = '|'.join([one_match['bibcode'] for one_match in json_text['match']][:count])
                 # else, when confidence is low and we have multiple matches,
                # more than likely none is a correct match
                else:
                    scores = ''
                    bibcodes = '.'*19
                confidence = confidences[0]
                comment = (json_text.get('comment', '') + ' Multiple matches.').strip()
                return (metadata['bibcode'], bibcodes, confidence, scores, comment)
            # single match
            scores = json_text['match'][0]['scores']
            confidence = json_text['match'][0]['confidence']
            return (metadata['bibcode'], json_text['match'][0]['bibcode'], confidence, scores, json_text.get('comment', ''))
        return (metadata['bibcode'], '.'*19, 0, '%s %s'%(json_text.get('comment', None), json_text.get('no match', '').capitalize()))
    return (metadata['bibcode'], None, 'status_code=%d'%(response.status_code))

import requests
import json

def get_matches(metadata, doctype):
    """

    :param metadata:
    :return:
    """
    try:
        payload = {'abstract': metadata['abstract'].replace('\n',' '),
                   'title': metadata['title'].replace('\n',' '),
                   'author': metadata['authors'],
                   'year': metadata['pubdate'][:4],
                   'doctype': doctype,
                   'bibcode': metadata['bibcode']}
    except KeyError as e:
        return (metadata['bibcode'], None, e)

    response = requests.post(
        url='http://localhost:5000/matchdoc', # 'https://api.adsabs.harvard.edu/v1/_oracle/matchdoc',
        headers={'Authorization': 'Bearer: token here'},
        data=payload
    )

    if response.status_code == 200:
        json_text = json.loads(response.text)
        if 'match' in json_text:
            scores = json_text['match'][0]['scores']
            return (metadata['bibcode'], json_text['match'][0]['bibcode'], '%.2f'%sum(scores.values()),scores)
        else:
            return (metadata['bibcode'], '.'*19, 0.0)
    return (metadata['bibcode'], None, 'status_code=%d'%(response.status_code))



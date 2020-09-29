
import requests
import re

def query_solr(identifier):
    """

    :param identifier:
    :return:
    """
    params = {
        'q': 'identifier:(%s)'%(identifier),
        'fl': 'identifier'
    }

    response = requests.get(
        url='https://api.adsabs.harvard.edu/v1/search/query',
        headers={'Authorization': 'Bearer ' + 'token here'},
        params=params
    )

    if response.status_code == 200:
        from_solr = response.json()
        return from_solr, 200
    return None, response.status_code

re_match_arXiv = re.compile(r'(\d\d\d\darXiv.*)')
def verify():
    """

    :return:
    """
    with open('result_match_to_arxiv.txt', 'rU') as fp:
        for i, doc in enumerate(fp):
            doc = eval(doc.rstrip('\r\n'))
            from_solr, status_code = query_solr(doc[0])
            if from_solr:
                if len(from_solr['response']['docs']) > 0:
                    identifier = from_solr['response']['docs'][0].get('identifier')
                    if identifier:
                        if doc[1] and doc[1][:4].isdigit() and doc[1] in identifier:
                            print (i, doc[0],doc[1],doc[2],'matched correctly')
                        elif 'arXiv' in identifier and not doc[1][:4].isdigit():
                            arXiv_identifier = list(filter(re_match_arXiv.match, identifier))
                            if len(arXiv_identifier) >= 1:
                                print (i, doc[0], doc[1], doc[2], 'classic matched with', arXiv_identifier[0])
                        else:
                            print (i, doc[0],doc[1],doc[2],'no matches found')
                    else:
                        print (i, doc[0],doc[1],doc[2],'not in solr')
                else:
                    print (i, doc[0], doc[1], doc[2], 'no record returned from solr')
            else:
                print (i, doc[0],doc[1],doc[2], 'solr returned', status_code)

# this script is used to compare results of oracle with classic
if __name__ == '__main__':
    verify()



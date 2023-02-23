import json
import os
from adsputils import load_config

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), "../"))
config = load_config(proj_home=proj_home)

class FailedQueryException(Exception):
    pass


class QueryConfigException(Exception):
    pass


class NoResultsException(Exception):
    pass


class RepStatusException(Exception):
    pass


def RefereedStatus(bibstem):
    try:
        token = config.get("DOCMATCHPIPELINE_API_TOKEN", None)
        jdb_url = config.get("DOCMATCHPIPELINE_API_ORACLE_SERVICE_URL", None)
        if token and jdb_url:
            jdb_url = jdb_url.replace('v1/oracle', 'v1/journals')
            header = {'Authorization': 'Bearer:%s' % token}
            query = '/summary/' + bibstem
            request_url = jdb_url + query
            r = requests.get(request_url, headers=header)
            if r.status_code == 200:
                data = json.loads(r.json())
            else:
                raise FailedQueryException("Journals query failed with status code %s" % r.status_code)
            refereed = data.get('summary', {}).get('master', {}).get('refereed', None)
            if refereed == 'yes':
                return True
            elif refereed == 'no':
                return False
            else:
                raise NoResultsException("Bibstem not found in JournalsDB: %s" % bibstem)
        else:
            raise QueryConfigException("Failed to get one or more config values for API search")
    except Exception as err:
        raise RefStatusException(err)

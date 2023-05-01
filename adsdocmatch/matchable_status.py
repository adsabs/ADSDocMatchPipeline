import json
import os
import re
import requests
from adsputils import load_config

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), "../"))
config = load_config(proj_home=proj_home)

class FailedQueryException(Exception):
    pass


class QueryConfigException(Exception):
    pass


class NoResultsException(Exception):
    pass


class MatchableStatusException(Exception):
    pass

# selection criteria expressions from adspy.ArtDefs
RE_YEAR_START = re.compile(r'^\d')
RE_VOL_END = re.compile(r'.*\d$')


def matchable_status(bibstem):
    try:
        token = config.get("DOCMATCHPIPELINE_API_TOKEN", None)
        jdb_url = config.get("DOCMATCHPIPELINE_API_JOURNALS_SERVICE_URL", None)
        if token and jdb_url:
            header = {"Authorization": "Bearer:%s" % token}
            query = "/summary/" + bibstem
            request_url = jdb_url + query
            r = requests.get(request_url, headers=header)
            if r.status_code == 200:
                data = r.json()
            else:
                raise FailedQueryException("Journals query failed with status code %s" % r.status_code)
            bibstem = data.get("summary", {}).get("master", {}).get("bibstem", None)
            pubtype = data.get("summary", {}).get("master", {}).get("pubtype", None)
            noindex = data.get("summary", {}).get("master", {}).get("not_indexed", True)
            if (bibstem and pubtype):
                if pubtype == "Journal" \
                    and not noindex \
                    and not re.match(RE_YEAR_START, bibstem) \
                    and not re.match(RE_VOL_END, bibstem):
                    return True
                else:
                    return False
            else:
                raise NoResultsException("Bibstem not found in JournalsDB: %s" % bibstem)
        else:
            raise QueryConfigException("Failed to get one or more config values for API search")
    except Exception as err:
        raise MatchableStatusException(err)

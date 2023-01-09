import os
import requests
import urllib3
from datetime import datetime
from adsputils import load_config

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), "../"))
conf = load_config(proj_home=proj_home)


class SlackPublishError(Exception):
    pass


class SlackPublisher(object):
    def __init__(self, slackurl=None, slackvar = "message"):
        self.url = slackurl
        self.header = {"content-type": "application/json"}
        self.slackvar = slackvar

    def publish(self, message):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        data = "{'%s': '%s'}" % (self.slackvar, message)
        try:
            rQuery = requests.post(self.url, data=data, headers=self.header, verify=False)
        except Exception as err:
            raise SlackPublishError(err)
        else:
            if rQuery.status_code != 200:
                err = "Slack notification failed -- status code: %s" % rQuery.status_code
                raise SlackPublishError(err)

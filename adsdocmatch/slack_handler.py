import requests
import urllib3


class SlackPublishException(Exception):
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
            raise SlackPublishException(err)
        else:
            if rQuery.status_code != 200:
                err = "Slack notification failed -- status code: %s" % rQuery.status_code
                raise SlackPublishException(err)
        return True

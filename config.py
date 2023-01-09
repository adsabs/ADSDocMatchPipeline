import os

################################################################################
# - Key deployment variables
# Redefine these in your local environment and run the same docker image as
# in production, by example pointing to 'localhost' instead of 'adsvm' broker.
_INDEXER_HOST = os.getenv('_INDEXER_HOST', 'adsqb10g')
_INDEXER_PORT = os.getenv('_INDEXER_PORT', '9983')
_BROKER_HOST = os.getenv('_BROKER_HOST', 'adsvm03.cfa.harvard.edu')
_BROKER_PORT = os.getenv('_BROKER_PORT', '5682')
_API_PROTOCOL = os.getenv('_API_PROTOCOL', 'https')
_API_HOST = os.getenv('_API_HOST', 'api.adsabs.harvard.edu')
_API_PORT = os.getenv('_API_PORT', '443')
_MAIL_HOST = os.getenv('_MAIL_HOST', 'head.cfa.harvard.edu')
_MAIL_PORT = os.getenv('_MAIL_PORT', '25')
################################################################################

LOGGING_LEVEL = 'INFO'
LOG_STDOUT = True

#SCOPES is the list of scopes you want your service account to have;
# for most purposes "drive" is all you'll need.  You may need to add
# "sheets" in the future.

SCOPES = ['https://www.googleapis.com/auth/drive']

#FOLDER_ID is the folder where the service account is permitted access
# The folder id has to be explicitly shared with the email address of
# the service account

FOLDER_IDS = {
    # DocMatching folder
    "basedir":"dummy file ID1",
    # DocMatching / curated
    "curated":"dummy file ID2",
    # DocMatching / archive
    "archive":"dummy file ID3"}

#SECRETS_FILE is the full path to the file containing the service account
# credentials obtained from the Cloud Dashboard via
# https://console.cloud.google.com/apis/credentials?project=yourprojectname

SECRETS_FILE = './dummy_secrets.dat'

LOGDIR = "/proj/ads/abstracts/sources/ArXiv/log/"

DATA_DIR = './data/'

API_DOCMATCHING_MAX_RECORDS_TO_ORACLE=2000
API_DOCMATCHING_ORACLE_SERVICE_SLEEP_SEC=10
API_DOCMATCHING_ORACLE_SERVICE_ATTEMPTS=10
API_DOCMATCHING_TOKEN="Dummy oracle service API token string"
API_DOCMATCHING_ORACLE_SERVICE_URL="https://dummy_url.cfa.harvard.edu/v1/oracle"
API_DOCMATCHING_CONFIDENCE_VALUE=1.1

SLACK_CURATOR_URL="Use slack workflow URL here"

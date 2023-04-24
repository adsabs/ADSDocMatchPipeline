LOGGING_LEVEL="WARN"
LOG_STDOUT=True

DOCMATCHPIPELINE_API_TOKEN = 'api token'
DOCMATCHPIPELINE_API_ORACLE_SERVICE_URL = 'http://0.0.0.0:5000/v1/oracle'
DOCMATCHPIPELINE_API_JOURNALS_SERVICE_URL = 'http://0.0.0.0:5000/v1/journals'
DOCMATCHPIPELINE_API_MAX_RECORDS_TO_ORACLE = '2000'
DOCMATCHPIPELINE_API_ORACLE_SERVICE_ATTEMPTS = '10'
DOCMATCHPIPELINE_API_ORACLE_SERVICE_SLEEP_SEC = '1'

# input filenames
DOCMATCHPIPELINE_INPUT_FILENAME = '/match_oracle.input'

# classic match of arxiv to published, or vice versa
DOCMATCHPIPELINE_CLASSIC_MATCHES_FILENAME = '/match.out'

# intermediate step filenames
DOCMATCHPIPELINE_EPRINT_RESULT_FILENAME = '/matched_eprint.output.csv'
DOCMATCHPIPELINE_PUB_RESULT_FILENAME = '/matched_pub.output.csv'

# final filename to be uploaded to google drive
DOCMATCHPIPELINE_EPRINT_COMBINED_FILENAME = 'compare_eprint.csv'
DOCMATCHPIPELINE_PUB_COMBINED_FILENAME = 'compare_pub.csv'

# Google Drive integration
GOOGLE_SECRETS_FILENAME = "credentials.txt"
GOOGLE_API_SCOPE = "https://www.googleapis.com/auth/drive"
GOOGLE_BASEDIR_ID = "drive-id-1"
GOOGLE_CURATED_FOLDER_ID = "drive-id-2"
GOOGLE_ARCHIVE_FOLDER_ID = "drive-id-3"

# Slack integration
SLACK_WORKFLOW_URL = "https://hooks.slack.com/workflows/a/b/c/d"

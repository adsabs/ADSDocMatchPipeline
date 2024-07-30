LOGGING_LEVEL="WARN"
LOG_STDOUT=True

DOCMATCHPIPELINE_API_TOKEN = "api token"
DOCMATCHPIPELINE_API_ORACLE_SERVICE_URL = "http://0.0.0.0:5000"
DOCMATCHPIPELINE_API_JOURNALS_SERVICE_URL = "http://0.0.0.0:5050"
DOCMATCHPIPELINE_API_MAX_RECORDS_TO_ORACLE = "5000"
DOCMATCHPIPELINE_API_ORACLE_SERVICE_ATTEMPTS = "10"
DOCMATCHPIPELINE_API_ORACLE_SERVICE_SLEEP_SEC = "1"

# input filenames
DOCMATCHPIPELINE_INPUT_FILENAME = "/match_oracle.input"

# classic match of arxiv to published, or vice versa
DOCMATCHPIPELINE_CLASSIC_MATCHES_FILENAME = "/match.out"

# intermediate step filenames
DOCMATCHPIPELINE_EPRINT_RESULT_FILENAME = "/matched_eprint.output.csv"
DOCMATCHPIPELINE_PUB_RESULT_FILENAME = "/matched_pub.output.csv"

# final filename to be uploaded to google drive
DOCMATCHPIPELINE_EPRINT_COMBINED_FILENAME = "/compare_eprint.csv"
DOCMATCHPIPELINE_PUB_COMBINED_FILENAME = "/compare_pub.csv"

# filename to log failed metadata filenames
DOCMATCHPIPELINE_RERUN_FILENAME = "../rerun.input"

# Google Drive integration
GOOGLE_SECRETS_FILENAME = "credentials.txt"
GOOGLE_API_SCOPE = "https://www.googleapis.com/auth/drive"
GOOGLE_BASEDIR_ID = "drive-id-1"
GOOGLE_CURATED_FOLDER_ID = "drive-id-2"
GOOGLE_ARCHIVE_FOLDER_ID = "drive-id-3"

# Slack integration
SLACK_WORKFLOW_URL = "https://hooks.slack.com/workflows/a/b/c/d"

# source name to get confidence scores from the oracle service
DOCMATCHPIPELINE_SOURCE_ADS = "ADS"
DOCMATCHPIPELINE_SOURCE_INCORRECT = "incorrect"

# how many months to log the arXiv article that was not matched, among the classes of the arXiv that should have been matched
DOCMATCHPIPELINE_EPRINT_RERUN_MONTHS = 1

# backend maintenance directory and files
# define the correct DOCMATCHPIPELINE_PUBLISHED_DIR in deployment yamls
DOCMATCHPIPELINE_PUBLISHED_DIR="/tmp/"

DOCMATCHPIPELINE_MATCHES_KILL_FILE="matches.kill"
DOCMATCHPIPELINE_MATCHES_KILL_FROZEN_FILE="matches.kill.frozen"
DOCMATCHPIPELINE_ORACLE_DUMP_FILE="oracle_dump.tsv"
DOCMATCHPIPELINE_ORACLE_DUMP_AGE=9999
DOCMATCHPIPELINE_USER_SUBMITTED_FILE="user_submitted.list"
DOCMATCHPIPELINE_USER_SUBMITTED_FROZEN_FILE="user_submitted_frozen.list"



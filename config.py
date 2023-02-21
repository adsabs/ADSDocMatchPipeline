DOCMATCHPIPELINE_API_TOKEN = 'api token'
DOCMATCHPIPELINE_API_ORACLE_SERVICE_URL = 'http://0.0.0.0:5000'
DOCMATCHPIPELINE_API_ORACLE_SERVICE_ATTEMPTS = '10'
DOCMATCHPIPELINE_API_ORACLE_SERVICE_SLEEP_SEC = '10'

# input filenames
DOCMATCHPIPELINE_INPUT_FILENAME = '/match_oracle.input'

# match arxiv to published (i.e. starting from daily arxiv ingest)
DOCMATCHPIPELINE_CLASSIC_MATCHES_FILENAME = '/match.out'

# match published to arxiv (i.e. starting from collection index)
# DOCMATCHPIPELINE_CLASSIC_MATCHES_FILENAME = '/matches.output'

# intermediate step filenames
DOCMATCHPIPELINE_EPRINT_RESULT_FILENAME = '/matched_eprint.output.csv'
DOCMATCHPIPELINE_PUB_RESULT_FILENAME = '/matched_pub.output.csv'

# final filename to be uploaded to google drive
DOCMATCHPIPELINE_EPRINT_COMBINED_FILENAME = 'compare_eprint.csv'
DOCMATCHPIPELINE_PUB_COMBINED_FILENAME = 'compare_pub.csv'

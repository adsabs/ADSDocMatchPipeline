import argparse
import os
from adsdocmatch.match_w_metadata import MatchMetadata
from adsdocmatch.slack_handler import SlackPublisher
from adsdocmatch.oracle_util import OracleUtil
from adsputils import load_config, setup_logging
import adsdocmatch.utils as utils

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), "./"))
conf = load_config(proj_home=proj_home)

logger = setup_logging("docmatching", level=conf.get("LOGGING_LEVEL", "WARN"), proj_home=proj_home, attach_stdout=conf.get("LOG_STDOUT", "FALSE"))


def get_args():

    parser = argparse.ArgumentParser("Docmatch processing and curation management")

    parser.add_argument("-mp",
                        "--match_to_pub",
                        dest="match_to_pub",
                        action="store_true",
                        default=False,
                        help="Match eprints to published records")

    parser.add_argument("-me",
                        "--match_to_eprint",
                        dest="match_to_eprint",
                        action="store_true",
                        default=False,
                        help="Match published records to eprint records")

    parser.add_argument("-d",
                        "--date",
                        dest="process_date",
                        action="store",
                        default=None,
                        help="Date to process: YYYY-MM-DD")

    parser.add_argument("-p",
                        "--data-path",
                        dest="datapath",
                        action="store",
                        default="./data/",
                        help="Path to matching input file(s)")

    parser.add_argument("-ao",
                        "--add-to-oracle",
                        dest="add_to_oracle",
                        action="store_true",
                        default=False,
                        help="Fetch curated files and add to oracle")

    parser.add_argument("-q",
                        "--query-oracle",
                        dest="query_oracle",
                        action="store_true",
                        default=False,
                        help="Query oracle for recent matches")

    parser.add_argument("-n",
                        "--number-of-days",
                        dest="num_days",
                        action="store",
                        default=1,
                        help="Last N days to query")

    parser.add_argument("-o",
                        "--output-filename",
                        dest="output_filename",
                        action="store",
                        default="./output.csv",
                        help="Filename for oracle query output.")

    return parser.parse_args()


def main():
    '''
    The daily matching process attempts to match new arxiv results to pub using
    oracledb.  This process is contained within the module
    adsdocmatch.match_w_metadata.MatchMetadata, in the batch_match_to_arXiv
    method.
    '''

    try:
        args = get_args()
    except Exception as err:
        logger.error("Get Arguments failed: %s" % err)
    else:

        # daily: match new eprint records to published records
        if args.match_to_pub or args.match_to_eprint:
            path = None
            if args.datapath:
                path = args.datapath
            elif args.date:
                path = conf.get("EPRINT_BASE_DIRECTORY", "./") + "/" + args.date
            if path:
                try:
                    filesToUpload = []
                    # if successful, process_match returns the filename to
                    # be uploaded to google.  If a classic match file
                    # exists, the comparison filename will be returned.
                    # If no classic match file exists, the oracle match
                    # filename will be returned.
                    if args.match_to_pub:
                        outFile = MatchMetadata().process_match_to_pub(path)
                        filesToUpload.append(outFile)
                    if args.match_to_eprint:
                        fileList = MatchMetadata().process_match_to_arXiv(path)
                        filesToUpload.append(outFile)
                    # If either process created files to upload,
                    # send them to the Google Drive now.
                    for f in filesToUpload:
                        fileId = utils.upload_spreadsheet(f)
                        logger.info("File available in google drive: %s" % fileId)
                        try:
                            url_post = "https://docs.google.com/spreadsheets/d/%s" % fileId
                            url_slack = conf.get("SLACK_WORKFLOW_URL","")
                            slack = SlackPublisher(slackurl=url_slack,
                                                   slackvar="url")
                            slack.publish(url_post)
                        except Exception as err:
                            logger.warning("Failed to send notification to Slack: %s" % err)
                except Exception as err:
                        logger.warning("Match to pub/upload failed: %s" % err)
            else:
                logger.error("Path to records for matching not set, stopping.")

        # via cron: check for files in curated, and process/archive if found
        elif args.add_to_oracle:
            try:
                utils.process_curated_spreadsheets()
            except Exception as err:
                logger.error("Error adding matches to oracledb: %s" % err)

        elif args.query_oracle:
            try:
                query_results = OracleUtil().query(args.output_filename,
                                                 args.num_days)
                logger.info(query_results)
            except Exception as err:
                logger.error("Error querying oracledb: %s" % err)

        else:
            logger.debug("Nothing to do.")


if __name__ == "__main__":
    main()

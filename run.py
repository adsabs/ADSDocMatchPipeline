import argparse
import os

from adsdocmatch.match_w_metadata import MatchMetadata
from adsdocmatch.slack_handler import SlackPublisher
from adsdocmatch.oracle_util import OracleUtil
from adsdocmatch.spreadsheet_util import SpreadsheetUtil
from adsputils import load_config, setup_logging

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
                        help="Match eprints to published records.")

    parser.add_argument("-me",
                        "--match_to_eprint",
                        dest="match_to_eprint",
                        action="store_true",
                        default=False,
                        help="Match published records to eprint records.")

    parser.add_argument("-p",
                        "--data-path",
                        dest="datapath",
                        action="store",
                        default="./data/",
                        help="Path to top level directory to process.")

    parser.add_argument("-ao",
                        "--add-to-oracle",
                        dest="add_to_oracle",
                        action="store_true",
                        default=False,
                        help="Fetch curated files and add to oracle.")

    parser.add_argument("-q",
                        "--query-oracle",
                        dest="query_oracle",
                        action="store_true",
                        default=False,
                        help="Query oracle for recent matches.")

    parser.add_argument("-n",
                        "--number-of-days",
                        dest="num_days",
                        action="store",
                        default=1,
                        help="Include the last n days in the query.")

    parser.add_argument("-o",
                        "--output-filename",
                        dest="output_filename",
                        action="store",
                        default="./output.csv",
                        help="Filename for oracle query output.")

    parser.add_argument("-lss",
                        "--list-source-score",
                        dest="list_source_score",
                        action="store_true",
                        default=False,
                        help="List source name and score value for confidence.")

    parser.add_argument("-as",
                        "--apply-source",
                        dest="apply_source",
                        action="store",
                        default=False,
                        help="Apply source score before adding matches to oracle.")

    parser.add_argument("-mf",
                        "--matched-file",
                        dest="matched_file_to_oracle",
                        action="store",
                        default=False,
                        help="Add tab delimited two column matched bibcodes to oracle with confidence of the source.")

    parser.add_argument("-c",
                        "--cleanup",
                        dest="cleanup_oracle",
                        action="store_true",
                        default=False,
                        help="Clean up the db, removing tmp bibcodes and lower confidence of multi matches.")

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
                        outFile = MatchMetadata().process_match_to_arXiv(path)
                        filesToUpload.append(outFile)
                    # If either process created files to upload,
                    # send them to the Google Drive now.
                    for f in filesToUpload:
                        fileId = SpreadsheetUtil().upload(f)
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

        # via cron: check for files in curated, and process/archive if found and processed successfully
        elif args.add_to_oracle:
            try:
                spreadsheet_util = SpreadsheetUtil()
                oracle_util = OracleUtil()

                for spreadsheet_filename in spreadsheet_util.get_curated_filenames():
                    try:
                        filename = spreadsheet_util.download(spreadsheet_filename)
                        status = oracle_util.update_db_curated_matches(filename)
                        if status:
                            spreadsheet_util.archive(spreadsheet_filename)
                        logger.info("Processed file `%s`. %s" % (spreadsheet_filename, status))
                    except Exception as err:
                        logger.warning("Unable to add curated sheet (%s) to local oracledb: %s" % (spreadsheet_filename, err))

            except Exception as err:
                logger.error("Error adding matches to oracledb: %s" % err)

        elif args.query_oracle:
            try:
                query_results = OracleUtil().query(args.output_filename, args.num_days)
                logger.info(query_results)
            except Exception as err:
                logger.error("Error querying oracledb: %s" % err)

        elif args.list_source_score:
            try:
                results = OracleUtil().get_source_score_list()
                for result in results:
                    print(result)
            except Exception as err:
                logger.error("Error listing source score: %s" % err)

        elif args.matched_file_to_oracle or args.apply_source:
            if args.matched_file_to_oracle and args.apply_source:
                try:
                    status = OracleUtil().update_db_sourced_matches(args.matched_file_to_oracle, args.apply_source)
                    logger.info("Processed file `%s` using source `%s`. %s" % (args.matched_file_to_oracle, args.apply_source, status))
                except Exception as err:
                    logger.error("Error adding matches from %s with source %s to database: %s" % (args.matched_file_to_oracle, args.apply_source, err))

            else:
                logger.error("Both parameters are need to add matched bibcodes to oracle: file path (-mf) and the source to apply (-as).")

        elif args.cleanup_oracle:
            try:
                status = OracleUtil().cleanup_db()
                logger.info("The cleanup_db command was issued to oracle_service.")
            except Exception as err:
                logger.error("Error issuing cleanup_db command to oracle_service: %s" % err)
        else:
            logger.debug("Nothing to do.")


if __name__ == "__main__":
    main()

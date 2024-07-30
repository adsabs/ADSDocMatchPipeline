import argparse
import os

from adsdocmatch.match_w_metadata import MatchMetadata
from adsdocmatch.oracle_util import OracleUtil
from adsputils import load_config, setup_logging

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), "./"))
config = load_config(proj_home=proj_home)

logger = setup_logging("docmatching", level=config.get("LOGGING_LEVEL", "WARN"), proj_home=proj_home, attach_stdout=config.get("LOG_STDOUT", "FALSE"))


def get_args():

    parser = argparse.ArgumentParser("Docmatch processing and curation management")

    parser.add_argument("-mp",
                        "--match-to-pub",
                        dest="match_to_pub",
                        action="store_true",
                        default=False,
                        help="Match eprints to published records.")

    parser.add_argument("-me",
                        "--match-to-eprint",
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

    parser.add_argument("-do",
                        "--dump_oracle",
                        dest="dump_oracle",
                        action="store_true",
                        default=False,
                        help="Trigger a query and download of the entire oracle database, to a filename specified in config.")

    parser.add_argument("-us",
                        "--load-user-submitted",
                        dest="load_curated_file",
                        action="store_true",
                        default=False,
                        help="Submit the current user-submitted list to oracle, and empty the file contents into the frozen file.")

    parser.add_argument("-uk",
                        "--load-matches-kill",
                        dest="load_matches_kill",
                        action="store_true",
                        default=False,
                        help="Submit the current curated matches.kill list to oracle.")

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
                path = config.get("EPRINT_BASE_DIRECTORY", "./") + "/" + args.date
            if path:
                try:
                    if args.match_to_pub:
                        outFile = MatchMetadata().process_match_to_pub(path)
                    if args.match_to_eprint:
                        outFile = MatchMetadata().process_match_to_arXiv(path)
                except Exception as err:
                    logger.error("Doc matching failed for path %s: %s" % (path, err))
            else:
                logger.error("Path to records for matching not set, stopping.")

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
                if status:
                    logger.info("The cleanup_db command returned the result: %s" % status)
                else:
                    logger.warning("The cleanup_db command did not return a status.")
            except Exception as err:
                logger.error("Error issuing cleanup_db command to oracle_service: %s" % err)

        # daily: process and archive user submissions
        elif args.load_curated_file:
            OracleUtil().load_curated_file()

        # daily: process matches.kill without archiving
        elif args.load_matches_kill:
            input_filename = config.get("DOCMATCHPIPELINE_PUBLISHED_DIR", "/tmp/") + config.get("DOCMATCHPIPELINE_MATCHES_KILL_FILE", "matches.kill")
            frozen_filename = config.get("DOCMATCHPIPELINE_PUBLISHED_DIR", "/tmp/") + config.get("DOCMATCHPIPELINE_MATCHES_KILL_FROZEN_FILE", "matches.kill.frozen")
            if input_filename:
                OracleUtil().load_curated_file(input_filename=input_filename, frozen_filename=frozen_filename, input_score=-1.0, do_backup=False)

        # daily: dump the oracle database to file
        elif args.dump_oracle:
            try:
                OracleUtil().dump_oracledb()
            except Exception as err:
                logger.error("Error dumping oracle db to file: %s" % err)
        else:
            logger.debug("Nothing to do.")


if __name__ == "__main__":
    main()

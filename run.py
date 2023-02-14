import argparse
import os
from adsdocmatch.match_w_metadata import MatchMetadata
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
                    if args.match_to_pub:
                        # if successful, process_match returns the filename to
                        # be uploaded to google.
                        # fileList[0] is result_filename,
                        # fileList[1] is combined_result_filename
                        fileList = MatchMetadata().process_match_to_pub(path)
                        filesToUpload.append(fileList[1])
                    if args.match_to_eprint:
                        fileList = MatchMetadata().process_match_to_arXiv(path))
                        filesToUpload.append(fileList[1])
                    for f in filesToUpload:
                        fileId = utils.upload_spreadsheet(f)
                        logger.info("File available in google drive: %s" % fileId)
                except Exception as err:
                        logger.warning("Match to pub/upload failed: %s" % err)
            else:
                logger.error("Path to records for matching not set, stopping.")

        # via cron: check for files in curated, and process/archive if found
        elif args.add_to_oracle:
            try:
                utils.add_to_oracle()
            except Exception as err:
                logger.error("Error adding matches to oracledb: %s" % err)
        else:
            logger.debug("Nothing to do.")


if __name__ == "__main__":
    main()

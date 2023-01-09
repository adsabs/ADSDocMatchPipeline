import argparse
import os
from adsdocmatch.exceptions import *
from adsdocmatch.oraclemgr import OracleManager
from adsdocmatch.parser import PandasParser
from adsdocmatch.gmanager import GoogleManager
from adsdocmatch.pubmatcher import PubMatcher
from adsdocmatch.classiccomp import ClassicComparer
from adsdocmatch.slackhandler import SlackPublisher
from adsputils import load_config, setup_logging
from glob import glob

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), "./"))
conf = load_config(proj_home=proj_home)

logger = setup_logging("docmatching", level=conf.get("LOGGING_LEVEL", "WARN"), proj_home=proj_home, attach_stdout=conf.get("LOG_STDOUT", "FALSE"))

def get_args():

    parser = argparse.ArgumentParser(description="Match arXiv with Publisher")

    parser.add_argument("-d",
                        "--daily",
                        dest="daily",
                        action="store_true",
                        default=False,
                        help="Trigger daily docmatching run and upload for curators")

    parser.add_argument("-f",
                        "--filename",
                        dest="filename",
                        action="store",
                        default=None,
                        help="Name of csv file to upload.")

    parser.add_argument("-u",
                        "--upload",
                        dest="upload",
                        action="store_true",
                        default=False,
                        help="Upload a file to google.")

    parser.add_argument("-pc",
                        "--process-curated",
                        dest="process",
                        action="store_true",
                        default=False,
                        help="Download and process curated sheets from google.")

    parser.add_argument("-df",
                        "--delete-intermediate-files",
                        dest="delete",
                        action="store_true",
                        default=False,
                        help="Delete intermediate files after they're added to oracle.")

    parser.add_argument("-l",
                        "--list",
                        dest="list",
                        action="store_true",
                        default=False,
                        help="List files in Google folder")

    parser.add_argument("-mi",
                        "--match-input-list",
                        dest="matchInputList",
                        action="store",
                        default=None,
                        help="Match a list of arxiv files to pub")

    parser.add_argument("-ms",
                        "--match-single-file",
                        dest="matchSingleFile",
                        action="store",
                        default=None,
                        help="Path to a single arxiv file to be matched to pub")

    parser.add_argument("-mo",
                        "--match-output-file",
                        dest="matchOutputFile",
                        action="store",
                        default=None,
                        help="Output file for oracle matches")


    parser.add_argument("-cr",
                        "--classic-results",
                        dest="classicResultsFile",
                        action="store",
                        default="./data/match.out",
                        help="Path to a classic results file (e.g. match.out)")

    parser.add_argument("-cs",
                        "--compare-source-type",
                        dest="compareSource",
                        action="store",
                        default="eprint",
                        help="Specify if the source is eprint or pub (default=eprint")

    parser.add_argument("-cw",
                        "--compare-output-file",
                        dest="compareOutputFile",
                        action="store",
                        default=None,
                        help="Path to a file to hold output combined results")


    args = parser.parse_args()
    return args


def upload_file(filename=None, upload_name=None, folderId=None):
    """

    :param filename: csv filename
    :return:
    """
    try:
        gm = GoogleManager(authtype="service",
                           folderId=folderId,
                           secretsFile=conf.get("SECRETS_FILE", None),
                           scopes=conf.get("SCOPES", []))
    except Exception as err:
        logger.error("Can't instantiate GoogleManager: %s" % err)
    else:
        try:
            kwargs = {"infile": filename,
                      "upload_name": upload_name,
                      "mtype": "text/csv",
                      "meta_mtype": "application/vnd.google-apps.spreadsheet"}
            result = gm.upload_file(**kwargs)
        except Exception as err:
            logger.error("Error uploading file: %s" % err)
            return
        else:
            logger.info("Upload of %s successful" % filename)
            return result

def get_file_list(folderId=None):
    try:
        gm = GoogleManager(authtype="service",
                           folderId=folderId,
                           secretsFile=conf.get("SECRETS_FILE", None),
                           scopes=conf.get("SCOPES", []))
    except Exception as err:
        logger.error("Can't instantiate GoogleManager: %s" % err)
    else:
        try:
            return gm.list_files()
        except Exception as err:
            logger.warning("Error getting file list: %s" % err)
            return []

def process_datafile(googleFile=None, delete=False):
    try:
        filename = googleFile.get("name", None)
        fileid = googleFile.get("id", None)
        parentids = googleFile.get("parents", None)
        gm = GoogleManager(authtype="service",
                           folderId=conf.get("FOLDER_IDS", {}).get("curated",None),
                           secretsFile=conf.get("SECRETS_FILE", None),
                           scopes=conf.get("SCOPES", None))
        data = gm.export_sheet_contents(fileId=fileid, export_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        xlsfile = conf.get("DATA_DIR", "./") + filename + ".xlsx"
        with open(xlsfile, "wb") as fx:
            fx.write(data)

        # reparent file from "curated" folder to "archive"
        try:
            oldparentid = conf.get("FOLDER_IDS", {}).get("curated", None)
            newparentid = conf.get("FOLDER_IDS", {}).get("archive", None)
            if oldparentid in parentids:
                status = gm.reparent_file(fileId=fileid, removeParents=oldparentid, addParents=newparentid)
        except Exception as err:
            raise GoogleReparentException("Couldn't reparent file: %s" % err)
    except Exception as err:
        raise GoogleDownloadException("Error in process_datafile: %s" % err)
    else:

        # prep results for oracledb
        try:
            outfile = xlsfile + ".result"
            parser = PandasParser()
            results = parser.read_excel_file(xlsfile)
            finish = parser.write_output(results, outfile)
            logger.info("File %s processed: %s new matches" % (filename,finish))
        except Exception as err:
            raise ParserParseException(err)
        else:
            try:
                #add to oracledb
                url = conf.get("API_DOCMATCHING_ORACLE_SERVICE_URL", None)
                token = conf.get("API_DOCMATCHING_TOKEN", None)
                maxlines = conf.get("API_DOCMATCHING_MAX_RECORDS_TO_ORACLE",
                                    2000)
                confidence = conf.get("API_DOCMATCHING_CONFIDENCE_VALUE", 1.1)
                om = OracleManager(url=url,
                                   token=token,
                                   maxlines=maxlines,
                                   confidence=confidence)
                status = om.to_add(outfile)
                logger.info("Status message from OracleManager.to_add: %s" % status)
                if delete:
                    os.remove(xlsfile)
                    os.remove(outfile)
            except Exception as err:
                raise OracleAddRecordsException(err)


def main():
    args = get_args()

    if args.daily:
        try:
            if args.matchSingleFile or args.matchInputList:
                matcher = PubMatcher()
                if args.matchSingleFile:
                    matcher.single_match_output(arXiv_filename=args.matchSingleFile)
                elif args.matchInputList:
                    matcher.batch_match_to_pub(filename=args.matchInputList, result_filename=args.matchOutputFile)
                comparer = ClassicComparer()
                auditFile = args.matchOutputFile+".csv"
                comparer.compare(classic=args.classicResultsFile,
                                 audit=auditFile,
                                 output=args.compareOutputFile,
                                 source=args.compareSource)
                if os.path.exists(args.compareOutputFile):
                    basepath = args.compareOutputFile.split("/")[-2]
                    basename = args.compareOutputFile.split("/")[-1]
                    upload_name = basepath + "." + basename
                    result = upload_file(args.compareOutputFile,
                                         upload_name,
                                         conf.get("FOLDER_IDS", {}).get("basedir", None))
                    if not result:
                        raise Exception("Warning: %s not uploaded" % args.compareOutputFile)
                    else:
                        url_post = "https://docs.google.com/spreadsheets/d/%s" % result
                        url_slack = conf.get("SLACK_CURATOR_URL","")
                        slack = SlackPublisher(slackurl=url_slack,
                                               slackvar="url")
                        slack.publish(url_post)
            else:
                logger.info("No files specified, nothing to do for daily")
        except Exception as err:
            logger.error("Daily processing failed: %s" % err)
    elif args.process:
        files = get_file_list(conf.get("FOLDER_IDS", {}).get("curated", None))
        for f in files:
            try:
                process_datafile(googleFile=f, delete=args.delete)
            except Exception as err:
                logger.error("Fatal Error in process_datafile: %s" % err)
    else:
        logger.info("Currently only supports classic match and uploads to Google for curators.")


if __name__ == "__main__":
    main()

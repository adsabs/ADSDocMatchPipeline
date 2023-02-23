import os
from adsdocmatch.exceptions import *
from adsdocmatch.oracle_util import OracleUtil
from adsgcon.gmanager import GoogleManager
from adsputils import load_config, setup_logging


proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), "../"))
conf = load_config(proj_home=proj_home)

logger = setup_logging("docmatching", level=conf.get("LOGGING_LEVEL", "WARN"), proj_home=proj_home, attach_stdout=conf.get("LOG_STDOUT", "FALSE"))


def upload_spreadsheet(upload_filename):
    fx = upload_filename.split('/')
    upload_name = ".".join(fx[-2:])
    secretsPath = conf.get('GOOGLE_SECRETS_FILENAME', None)
    scopesList = [conf.get('GOOGLE_API_SCOPE', None)]
    folderId = conf.get("GOOGLE_BASEDIR_ID", None)

    gm = GoogleManager(authtype="service",
                       folderId=folderId,
                       secretsFile=secretsPath,
                       scopes=scopesList)
    kwargs = {"infile": upload_filename,
              "upload_name": upload_name,
              "mtype": "text/csv",
              "meta_mtype": "application/vnd.google-apps.spreadsheet"}

    return gm.upload_file(**kwargs)


def process_spreadsheet(gm, filemetadata):
    try:
        # first, download the curated spreadsheet, ...
        filename = filemetadata.get("name", None)
        fileId = filemetadata.get("id", None)
        kwargs = {"fileId": fileId,
                  "export_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
        data = gm.export_sheet_contents(**kwargs)
        xlsfile = conf.get("DOCMATCHPIPELINE_DATA_PATH", "./") + filename + ".xlsx"
        with open(xlsfile, "wb") as fx:
            fx.write(data)

        # # second, parse the xlsx and add the results to oracledb...
        oracleUtil = OracleUtil()
        oracleUtil.update_db_curated_matches(xlsfile)

    except Exception as err:
        raise GoogleDownloadException("Unable to download sheet to local .xlsx file: %s" % err)


def archive_spreadsheet(gm, filemetadata):
    try:
        # third, reparent curated to archive on Google Drive, ...
        oldparentid = conf.get("GOOGLE_CURATED_FOLDER_ID", None)
        newparentid = conf.get("GOOGLE_ARCHIVE_FOLDER_ID", None)
        parentids = filemetadata.get("parents", None)
        fileId = filemetadata.get("id", None)
        kwargs = {"fileId": fileId,
                  "removeParents": oldparentid,
                  "addParents": newparentid}
        if oldparentid in parentids:
            gm.reparent_file(**kwargs)
    except Exception as err:
        raise GoogleReparentException("Failed to archive curated file %s: %s" % (fileId, err))


def process_curated_spreadsheets():
    secretsPath = conf.get('GOOGLE_SECRETS_FILENAME', None)
    scopesList = [conf.get('GOOGLE_API_SCOPE', None)]
    folderId = conf.get("GOOGLE_CURATED_FOLDER_ID", None)
    try:
        gm = GoogleManager(authtype="service",
                           folderId=folderId,
                           secretsFile=secretsPath,
                           scopes=scopesList)
        files = gm.list_files()
    except Exception as err:
        logger.error("Couldn't initialize google manager: %s" % err)
    else:
        for f in files:
            try:
                process_spreadsheet(gm, f)
                archive_spreadsheet(gm, f)
            except Exception as err:
                logger.warning("Unable to add curated sheet (%s) to local oracledb: %s" % (f, err))
            else:
                logger.info("Added to oracle db: %s" % f)

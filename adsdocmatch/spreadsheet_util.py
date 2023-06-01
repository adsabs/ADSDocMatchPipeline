import os
from adsgcon.gmanager import GoogleManager
from adsputils import load_config, setup_logging


proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), "../"))
conf = load_config(proj_home=proj_home)

logger = setup_logging("docmatching", level=conf.get("LOGGING_LEVEL", "WARN"), proj_home=proj_home, attach_stdout=conf.get("LOG_STDOUT", "FALSE"))


class GoogleUploadException(Exception):
    pass


class GoogleDownloadException(Exception):
    pass


class GoogleArchiveException(Exception):
    pass



class SpreadsheetUtil():

    def __init__(self):
        """

        """
        # initially directory is set to top level
        folderId = conf.get("GOOGLE_BASEDIR_ID", None)
        secretsPath = conf.get("GOOGLE_SECRETS_FILENAME", None)
        scopesList = [conf.get("GOOGLE_API_SCOPE", None)]

        try:
            self.gm = GoogleManager(authtype="service",
                                    folderId=folderId,
                                    secretsFile=secretsPath,
                                    scopes=scopesList)

        except Exception as err:
            logger.error("Couldn't initialize google manager: %s" % err)

    def upload(self, filename):
        """

        :param filename:
        :return:
        """
        try:
            fx = filename.split("/")
            upload_name = ".".join(fx[-2:])
            kwargs = {"infile": filename,
                      "upload_name": upload_name,
                      "mtype": "text/csv",
                      "meta_mtype": "application/vnd.google-apps.spreadsheet"}
            # make sure the directory is set to curated
            self.gm.folderid = conf.get("GOOGLE_BASEDIR_ID", None)
            return self.gm.upload_file(**kwargs)

        except Exception as err:
            raise GoogleUploadException("Unable to upload file %s to google drive: %s" % (filename if filename else '?', err)) from None

    def download(self, metadata):
        """

        :param metadata:
        :return:
        """
        try:
            kwargs = {"fileId": metadata.get("id", None),
                      "export_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
            data = self.gm.export_sheet_contents(**kwargs)
            xls_filename = conf.get("DOCMATCHPIPELINE_DATA_PATH", "./") + metadata.get("name", None) + ".xlsx"
            with open(xls_filename, "wb") as fx:
                fx.write(data)
            return xls_filename

        except Exception as err:
            raise GoogleDownloadException("Unable to download sheet to local .xlsx file: %s" % err)

    def archive(self, metadata):
        """

        :param metadata:
        :return:
        """
        try:
            # reparent curated to archive on Google Drive, ...
            file_id = metadata.get("id", None)
            old_parent = conf.get("GOOGLE_CURATED_FOLDER_ID", None)
            kwargs = {"fileId": file_id,
                      "removeParents": old_parent,
                      "addParents": conf.get("GOOGLE_ARCHIVE_FOLDER_ID", None)}
            if old_parent in metadata.get("parents", []):
                # make sure the directory is set to top level
                self.gm.folderid = conf.get("GOOGLE_BASEDIR_ID", None)
                self.gm.reparent_file(**kwargs)

        except Exception as err:
            raise GoogleArchiveException("Failed to archive curated file %s: %s" % (file_id, err))

    def get_curated_filenames(self):
        """

        :return:
        """
        # make sure the directory is set to curated
        self.gm.folderid = conf.get("GOOGLE_CURATED_FOLDER_ID", None)
        return self.gm.list_files()

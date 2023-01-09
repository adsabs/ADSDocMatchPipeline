import io
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from adsdocmatch.exceptions import *

class GoogleManager(object):

    def __init__(self, authtype="service", folderId=None, secretsFile=None, scopes=None):
        self.allowed_authtypes = ["oauth2", "service"]
        self.folderid = folderId
        self.service = None
        try:
            if authtype not in self.allowed_authtypes:
                raise BadAuthtypeException(err)
            elif authtype == "oauth2":
                credentials = None
            elif authtype == "service":
                credentials = service_account.Credentials.from_service_account_file(secretsFile, scopes=scopes)
            self.service = build("drive", "v3", credentials=credentials)
            # self.service = build("drive", "v3", http=credentials.authorize(Http()), cache_discovery=False)
        except Exception as err:
            raise GoogleAuthException(err)

    def list_files(self):
        if self.service:
            kwargs = {"supportsAllDrives": True,
                      "includeItemsFromAllDrives": True,
                      "fields": "files(id,parents,name)"}
            if self.folderid:
                kwargs["q"] = "'%s' in parents" % self.folderid
            request = self.service.files().list(**kwargs).execute()
            return request["files"]

    def upload_file(self, infile=None, upload_name=None, folderID=None, mtype="text/plain", meta_mtype="text/plain"):

        if os.path.exists(infile):
            if not upload_name:
                upload_name = infile.split("/")[-1]
            filemeta = {"name": upload_name,
                        "mimeType": meta_mtype,
                        "parents": [self.folderid]}
            data = MediaFileUpload(infile,
                                   mimetype=mtype,
                                   resumable=False)
            try:
                upfile = self.service.files().create(body=filemeta,
                                                     media_body=data,
                                                     supportsAllDrives=True,
                                                     fields="id").execute()
                return upfile.get("id")
            except Exception as err:
                raise GoogleUploadException(err)
        else:
            raise MissingFileException(err)

    def download_file_contents(self, fileId=None, convert=True):
        # Note: this doesn't work on Workspace Doctypes (e.g. Sheets)!
        # Use self.export_sheet_contents() for those
        try:
            request = self.service.files().get_media(fileId=fileId)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            completed = False
            while not completed:
                status, done = downloader.next_chunk()
        except Exception as err:
            raise GoogleDownloadException(err)
        else:
            # return file.getvalue()
            return file.getbuffer()

    def export_sheet_contents(self, fileId=None, export_type="text/tab-separated-values"):
        try:
            request = self.service.files().export(fileId=fileId, mimeType=export_type).execute()
        except Exception as err:
            raise GoogleSheetExportException(err)
        else:
            return request

    def reparent_file(self, fileId=None, removeParents=None, addParents=None):
        try:
            kwargs = {"supportsAllDrives": True}
            request = self.service.files().update(fileId=fileId, removeParents=removeParents, addParents=addParents, **kwargs).execute()
        except Exception as err:
            raise GoogleReparentException(err)
        else:
            return request

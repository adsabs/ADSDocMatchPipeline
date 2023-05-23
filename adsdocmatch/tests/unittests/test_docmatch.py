import sys, os
project_home = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

import unittest
import mock
import json
import pandas as pd

from adsputils import load_config
from adsdocmatch.pub_parser.unicode import UnicodeHandler
from adsdocmatch.matchable_status import matchable_status, MatchableStatusException
import adsdocmatch.spreadsheet_util as spreadsheet_util
from adsdocmatch.spreadsheet_util import SpreadsheetUtil, GoogleUploadException, GoogleDownloadException, GoogleArchiveException
from adsgcon.gmanager import MissingFileException, GoogleSheetExportException, GoogleReparentException
from adsdocmatch.slack_handler import SlackPublisher, SlackPublishException

config = load_config(proj_home=project_home)


class TestDocMatch(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_unicode_functions(self):
        """ """
        entities = "&amp;, &reg;, &lt;, &gt;, &cent;, &pound;, &yen;, &euro;, &sect;, &copy;"
        expected = "&, ®, <, >, ¢, £, ¥, €, §, ©"
        results = UnicodeHandler().ent2u(entities)
        self.assertEqual(results, expected)

        entities = "&#33;, &#34;, &#35;, &#36;, &#37;, &#38;"
        expected = "!, \", #, $, %, &"
        results = UnicodeHandler().ent2u(entities)
        self.assertEqual(results, expected)

        entities = "&#x21;, &#x22;, &#x23;, &#x24;, &#x25;"
        expected = "!, \", #, $, %"
        results = UnicodeHandler().ent2u(entities)
        self.assertEqual(results, expected)

        input = "\ud800 remove \ud810 everything \ud820 except \ud830 these \ud840 non \ud850 control \ud860 chars"
        expected = "remove everything except these non control chars"
        results = UnicodeHandler().remove_control_chars(input)
        self.assertEqual(results, expected)

    def test_matchable_status(self):
        """ """
        return_value = {"summary":
                            {"master": {
                                  "bibstem": "ApJ",
                                  "journal_name": "The Astrophysical Journal",
                                  "pubtype": "Journal",
                                  "refereed": "yes",
                                  "collection": None,
                                  "notes": None,
                                  "not_indexed": False
                          }}
        }
        with mock.patch('requests.get') as get_mock:
            get_mock.return_value = mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.text = json.dumps(return_value)
            self.assertEqual(matchable_status('ApJ'), True)


        return_value = {"summary":
                            {"master": {
                                "bibstem": "ApJL",
                                "journal_name": "The Astrophysical Journal Letters",
                                "pubtype": "Other",
                                "refereed": "na",
                                "collection": None,
                                "notes": None,
                                "not_indexed": True
                            }}
        }
        with mock.patch('requests.get') as get_mock:
            get_mock.return_value = mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.text = json.dumps(return_value)
            self.assertEqual(matchable_status('ApJL'), False)

        with self.assertRaises(Exception) as context:
            with mock.patch('requests.get') as get_mock:
                get_mock.return_value = mock_response = mock.Mock()
                mock_response.status_code = 400
                mock_response.text = json.dumps(return_value)
                self.assertEqual (matchable_status(''), False)
        self.assertTrue('Journals query failed with status code 400' in str(context.exception))

        return_value = {"Error": "Search failed", "Error Info": "Bibstem '2022SPIE12038' not found."}
        with self.assertRaises(MatchableStatusException) as context:
            with mock.patch("requests.get") as get_mock:
                get_mock.return_value = mock_response = mock.Mock()
                mock_response.status_code = 200
                mock_response.text = json.dumps(return_value)
                self.assertEqual(matchable_status("2022SPIE12038"), False)
        self.assertTrue("Bibstem not found in JournalsDB: None" in str(context.exception))

    def test_spreadsheet_util(self):
        """ Mock GoogleManager to be able to test SpreadsheetUtil """

        class GoogleManagerForTesting:
            def __init__(self, authtype="service", folderId=None, secretsFile=None, scopes=None):
                pass

            def upload_file(self, infile=None, upload_name=None, folderID=None, mtype="text/plain", meta_mtype="text/plain"):
                # returns uploaded file id
                if infile:
                    return 1
                raise MissingFileException("No filename provided!")

            def export_sheet_contents(self, fileId=None, export_type="text/tab-separated-values"):
                # returns content of the test file
                if fileId:
                    with open(os.path.dirname(__file__) + "/stubdata/raw.dat", "rb") as f:
                        return f.read()
                raise GoogleSheetExportException('No fileID provided!')

            def reparent_file(self, fileId=None, removeParents=None, addParents=None):
                if fileId and removeParents and addParents:
                    return True
                raise GoogleReparentException('Unable to move the file.')

            def list_files(self):
                return ['one', 'two']

        with mock.patch.object(spreadsheet_util, "GoogleManager", GoogleManagerForTesting):
            spreadsheet = SpreadsheetUtil()

            # upload with filename
            self.assertEqual(spreadsheet.upload('/path/to/some/filename.csv'), 1)
            # upload with no filename, seeing exception
            with self.assertRaises(GoogleUploadException) as context:
                spreadsheet.upload('')
            self.assertTrue('Unable to upload file ? to google drive: No filename provided!' in str(context.exception))

            # download with filename
            filename = spreadsheet.download({'id': 1, 'name': 'testing.csv'})
            df = pd.read_excel(filename)
            self.assertTrue(df['this is a test'][0] == 1234)
            # and now remove the temporary file
            os.remove(filename)
            # download an unknown file, seeing exception
            with self.assertRaises(GoogleDownloadException) as context:
                spreadsheet.download({'id': None})
            self.assertTrue('Unable to download sheet to local .xlsx file: No fileID provided!' in str(context.exception))

            # move a file
            spreadsheet.archive({'id': 1, 'parents': config.get("GOOGLE_CURATED_FOLDER_ID", None)})
            # move unknown file, seeing exception
            with self.assertRaises(GoogleArchiveException) as context:
                spreadsheet.archive({'id': None, 'parents': config.get("GOOGLE_CURATED_FOLDER_ID", None)})
            self.assertTrue('Failed to archive curated file None: Unable to move the file.' in str(context.exception))

            # get list of files
            self.assertTrue(len(spreadsheet.get_curated_filenames()) == 2)

    def test_slack_handler(self):
        """ test SlackPublisher class """

        # test when everything goes well
        with mock.patch('requests.post') as slack_handler:
            slack_handler.return_value = mock_response = mock.Mock()
            mock_response.status_code = 200
            status = SlackPublisher().publish('a message')
            self.assertTrue(status)

        # test when slack returns non 200 status_code
        with mock.patch('requests.post') as slack_handler:
            slack_handler.return_value = mock_response = mock.Mock()
            mock_response.status_code = 400
            with self.assertRaises(SlackPublishException) as context:
                SlackPublisher().publish('a message')
            self.assertTrue('Slack notification failed -- status code: 400' in str(context.exception))

        # test when an exception happen while sending request to slack
        with mock.patch('requests.post') as slack_handler:
            slack_handler.side_effect = Exception(mock.Mock(status=404), 'not found')
            with self.assertRaises(Exception) as context:
                SlackPublisher().publish('a message')
            self.assertTrue('not found' in str(context.exception))


if __name__ == '__main__':
    unittest.main()

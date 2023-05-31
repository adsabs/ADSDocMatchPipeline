import sys, os
project_home = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

import unittest
import mock
import requests
import json

from adsputils import load_config
from adsdocmatch.match_w_metadata import MatchMetadata

config = load_config(proj_home=project_home)


class TestDocMatch(unittest.TestCase):

    def setUp(self):
        self.match_metadata = MatchMetadata()
        self.match_metadata.ORACLE_UTIL.set_local_config_test()

    def tearDown(self):
        pass

    def create_response(self, text):
        """ create a response object """
        response = requests.Response()
        response.status_code = 200
        response._content = bytes(json.dumps(text).encode('utf-8'))
        return response

    def test_match_to_arXiv_1(self):
        """ test match_to_arXiv when there are no matches """

        return_value = [{
            'source_bibcode': '2018ApJS..236...24F',
            'matched_bibcode': '...................',
            'label': 'Not Match', 'confidence': 0,
            'score': '',
            'comment': "No matches with DOI ['10.3847/1538-4365/aab760'] in pubnote, trying Abstract. No result from solr with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request."
        }]
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            with mock.patch.object(self.match_metadata, 'process_pub_metadata', return_value=1):
                matches = self.match_metadata.single_match_to_arXiv(pub_filename=os.path.dirname(__file__) + '/stubdata/K47-02665.abs')
                self.assertEqual(len(matches), 1)
                fields = matches[0].split('\t')
                self.assertEqual(len(fields), 6)
                self.assertEqual(fields[0], '2018ApJS..236...24F')
                self.assertEqual(fields[1], '...................')
                self.assertEqual(fields[2], 'Not Match')
                self.assertEqual(fields[3], '0')
                self.assertEqual(fields[4], '')
                self.assertEqual(fields[5], "No matches with DOI ['10.3847/1538-4365/aab760'] in pubnote, trying Abstract. No result from solr with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request.")

    def test_match_to_arXiv_2(self):
        """ test match_to_arXiv when a match is detected """

        return_value = [{
            'source_bibcode': '2022PhRvD.106i6008H',
            'matched_bibcode': '2021arXiv210806768H',
            'label': 'Match',
            'confidence': 0.9407689,
            'score': {'abstract': 0.93, 'title': 0.89, 'author': 1, 'year': 1},
            'comment': "No matches with DOI ['10.1103/PhysRevD.106.096008'] in pubnote, trying Abstract."
        }]
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            with mock.patch.object(self.match_metadata, 'process_pub_metadata', return_value=1):
                matches = self.match_metadata.single_match_to_arXiv(pub_filename=os.path.dirname(__file__) + '/stubdata/K88-62345.abs')
                self.assertEqual(len(matches), 1)
                fields = matches[0].split('\t')
                self.assertEqual(len(fields), 6)
                self.assertEqual(fields[0], '2022PhRvD.106i6008H')
                self.assertEqual(fields[1], '2021arXiv210806768H')
                self.assertEqual(fields[2], 'Match')
                self.assertEqual(fields[3], '0.9407689')
                self.assertEqual(fields[4], "{'abstract': 0.93, 'title': 0.89, 'author': 1, 'year': 1}")
                self.assertEqual(fields[5], "No matches with DOI ['10.1103/PhysRevD.106.096008'] in pubnote, trying Abstract.")

    def test_match_to_pub_1(self):
        """ test match_to_pub when there are no matches"""

        return_value = [{
            'source_bibcode': '2017arXiv170100200T',
            'matched_bibcode': '...................',
            'label': 'Not Match',
            'confidence': 0,
            'score': '',
            'comment': 'No matches with Abstract, trying Title. No document was found in solr matching the request.'
        }]
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            matches = self.match_metadata.single_match_to_pub(filename=os.path.dirname(__file__) + '/stubdata/1701.00200')
            self.assertEqual(len(matches), 1)
            fields = matches[0].split('\t')
            self.assertEqual(len(fields), 6)
            self.assertEqual(fields[0], '2017arXiv170100200T')
            self.assertEqual(fields[1], '...................')
            self.assertEqual(fields[2], 'Not Match')
            self.assertEqual(fields[3], '0')
            self.assertEqual(fields[4], '')
            self.assertEqual(fields[5], 'No matches with Abstract, trying Title. No document was found in solr matching the request.')

    def test_match_to_pub_2(self):
        """ test match_to_pub when a match is detected"""

        return_value = [{
            'source_bibcode': '2018arXiv180101021F',
            'matched_bibcode': '2018ApJS..236...24F',
            'label': 'Match',
            'confidence': 0.9957643,
            'score': {'abstract': 0.98, 'title': 0.98, 'author': 1, 'year': 1, 'doi': 1},
            'comment': ''
        }]
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            matches = self.match_metadata.single_match_to_pub(filename=os.path.dirname(__file__) + '/stubdata/1801.01021')
            self.assertEqual(len(matches), 1)
            fields = matches[0].split('\t')
            self.assertEqual(len(fields), 6)
            self.assertEqual(fields[0], '2018arXiv180101021F')
            self.assertEqual(fields[1], '2018ApJS..236...24F')
            self.assertEqual(fields[2], 'Match')
            self.assertEqual(fields[3], '0.9957643')
            self.assertEqual(fields[4], "{'abstract': 0.98, 'title': 0.98, 'author': 1, 'year': 1, 'doi': 1}")
            self.assertEqual(fields[5], '')

    def test_match_to_pub_3(self):
        """ test match_to_pub when match is in db"""

        return_value = [{
            'source_bibcode': '2007arXiv0708.1752V',
            'matched_bibcode': '2007A&A...474..653V',
            'label': 'Match',
            'confidence': 0.9961402,
            'score': {},
            'comment': ''
        }]
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            matches = self.match_metadata.single_match_to_pub(filename=os.path.dirname(__file__) + '/stubdata/0708.1752')
            self.assertEqual(len(matches), 1)
            fields = matches[0].split('\t')
            self.assertEqual(len(fields), 6)
            self.assertEqual(fields[0], '2007arXiv0708.1752V')
            self.assertEqual(fields[1], '2007A&A...474..653V')
            self.assertEqual(fields[2], 'Match')
            self.assertEqual(fields[3], '0.9961402')
            self.assertEqual(fields[4], "{}")
            self.assertEqual(fields[5], '')

    def test_match_to_pub_4(self):
        """ test match_to_pub when multiple matches are detected """

        return_value = [{
            'source_bibcode': '2021arXiv210607251P',
            'confidence': 0.8989977,
            'label': 'Match',
            'score': "{'abstract': None, 'title': 1.0, 'author': 1, 'year': 1}",
            'matched_bibcode': '2020PhDT........36P',
            'comment': 'Matching doctype `phdthesis;mastersthesis`. Multi match: 1 of 2.'
        }, {
            'source_bibcode': '2021arXiv210607251P',
            'confidence': 0.8933332,
            'label': 'Match',
            'score': "{'abstract': 1.0, 'title': 1.0, 'author': 1, 'year': 1}",
            'matched_bibcode': '2021PhDT........26P',
            'comment': 'Matching doctype `phdthesis;mastersthesis`. Multi match: 2 of 2.'
        }]
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            matches = self.match_metadata.single_match_to_pub(filename=os.path.dirname(__file__) + '/stubdata/2106.07251')
            self.assertEqual(len(matches), 2)
            expected_values = [
                ['2021arXiv210607251P','2020PhDT........36P','Match','0.8989977',"{'abstract': None, 'title': 1.0, 'author': 1, 'year': 1}",'Matching doctype `phdthesis;mastersthesis`. Multi match: 1 of 2.'],
                ['2021arXiv210607251P','2021PhDT........26P','Match','0.8933332',"{'abstract': 1.0, 'title': 1.0, 'author': 1, 'year': 1}",'Matching doctype `phdthesis;mastersthesis`. Multi match: 2 of 2.']
            ]
            for match, expected_value in zip(matches, expected_values):
                fields = match.split('\t')
                self.assertEqual(len(fields), 6)
                for i in range(len(fields)):
                    self.assertEqual(fields[i], expected_value[i])

    def test_batch_match_to_pub(self):
        """ test batch mode of match_to_pub """

        # setup filenames
        stubdata_dir = os.path.dirname(__file__) + '/stubdata'
        input_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_INPUT_FILENAME'])
        result_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_EPRINT_RESULT_FILENAME'])
        rerun_filename = os.path.abspath(os.path.join(stubdata_dir, config['DOCMATCHPIPELINE_RERUN_FILENAME']))

        # create input file with list of eprint filenames
        eprint_filenames = ['/2106.07251']
        with open(input_filename, "w") as f:
            for filename in eprint_filenames:
                f.write("%s\n"%(stubdata_dir+filename))
            f.close()

        return_value = [{
            'source_bibcode': '2021arXiv210607251P',
            'confidence': 0.8989977,
            'label': 'Match',
            'score': "{'abstract': None, 'title': 1.0, 'author': 1, 'year': 1}",
            'matched_bibcode': '2020PhDT........36P',
            'comment': 'Matching doctype `phdthesis;mastersthesis`. Multi match: 1 of 2.'
        }, {
            'source_bibcode': '2021arXiv210607251P',
            'confidence': 0.8933332,
            'label': 'Match',
            'score': "{'abstract': 1.0, 'title': 1.0, 'author': 1, 'year': 1}",
            'matched_bibcode': '2021PhDT........26P',
            'comment': 'Matching doctype `phdthesis;mastersthesis`. Multi match: 2 of 2.'
        }]

        expected_lines = [
            'source bibcode (link),verified bibcode,matched bibcode (link),label,confidence,matched scores,comment',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021arXiv210607251P/abstract"",""2021arXiv210607251P"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2020PhDT........36P/abstract"",""2020PhDT........36P"")",Match,0.8989977,"{\'abstract\': None, \'title\': 1.0, \'author\': 1, \'year\': 1}","Matching doctype `phdthesis;mastersthesis`. Multi match: 1 of 2."',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021arXiv210607251P/abstract"",""2021arXiv210607251P"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021PhDT........26P/abstract"",""2021PhDT........26P"")",Match,0.8933332,"{\'abstract\': 1.0, \'title\': 1.0, \'author\': 1, \'year\': 1}","Matching doctype `phdthesis;mastersthesis`. Multi match: 2 of 2."',
        ]

        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            self.match_metadata.batch_match_to_pub(input_filename=input_filename, result_filename=result_filename, rerun_filename=rerun_filename)

        # make sure output file is written properly
        with open(result_filename, "r") as f:
            for expected_line, actual_line in zip(expected_lines, f.readlines()):
                self.assertEqual(expected_line, actual_line[:-1])

        # remove temp files
        os.remove(input_filename)
        os.remove(result_filename)

    def test_batch_match_to_arXiv(self):
        """ test batch mode of match_to_arxiv """

        # setup filenames
        stubdata_dir = os.path.dirname(__file__) + '/stubdata'
        input_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_INPUT_FILENAME'])
        result_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_EPRINT_RESULT_FILENAME'])
        rerun_filename = os.path.abspath(os.path.join(stubdata_dir, config['DOCMATCHPIPELINE_RERUN_FILENAME']))

        # create input file with list of pub filenames
        pub_filenames = ['/K47-02665.abs']
        with open(input_filename, "w") as f:
            for filename in pub_filenames:
                f.write("%s\n"%(stubdata_dir+filename))
            f.close()

        return_value = [{
            'source_bibcode': '2018ApJS..236...24F',
            'matched_bibcode': '...................',
            'label': 'Not Match',
            'confidence': 0,
            'score': '',
            'comment': "No matches with DOI ['10.3847/1538-4365/aab760'] in pubnote, trying Abstract. No result from solr with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request."
        }]

        expected_lines = [
            'source bibcode (link),verified bibcode,matched bibcode (link),label,confidence,matched scores,comment',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2018ApJS..236...24F/abstract"",""2018ApJS..236...24F"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/.................../abstract"",""..................."")",Not Match,0,"","No matches with DOI [\'10.3847/1538-4365/aab760\'] in pubnote, trying Abstract. No result from solr with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request."',
        ]

        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            with mock.patch.object(self.match_metadata, 'process_pub_metadata', return_value=1):
                self.match_metadata.batch_match_to_arXiv(input_filename=input_filename, result_filename=result_filename, rerun_filename=rerun_filename)

        # make sure output file is written properly
        with open(result_filename, "r") as f:
            for expected_line, actual_line in zip(expected_lines, f.readlines()):
                self.assertEqual(expected_line, actual_line[:-1])

        # remove test files
        os.remove(input_filename)
        os.remove(result_filename)

    def test_output_combine_classic_docmatch_results_eprint(self):
        """ test combining classic matches with docmatching matches for eprint """

        # setup filenames
        stubdata_dir = os.path.dirname(__file__) + '/stubdata'
        result_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_EPRINT_RESULT_FILENAME'])
        classic_matched_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_CLASSIC_MATCHES_FILENAME'])
        combined_output_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_EPRINT_COMBINED_FILENAME'])

        # create output file
        docmatch_lines = [
            'source bibcode (link),verified bibcode,matched bibcode (link),label,confidence,matched scores,comment',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021arXiv210607251P/abstract"",""2021arXiv210607251P"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021PhDT........26P/abstract"",""2021PhDT........26P"")",Match,0.8933332,"{\'abstract\': 1.0, \'title\': 1.0, \'author\': 1, \'year\': 1}",""',
        ]
        with open(result_filename, "w") as f:
            for line in docmatch_lines:
                f.write("%s\n"%line)
            f.close()

        # create classic matched file
        classic_lines = [
            '2021arXiv210607251P\t2021PhDT........26P\t1.000',
            '2022arXiv220403455D\t2023PRXQ....4a0309D\t1.000',

        ]
        with open(classic_matched_filename, "w") as f:
            for line in classic_lines:
                f.write("%s\n"%line)
            f.close()

        # create combined classic and docmatch results
        self.match_metadata.merge_classic_docmatch_results(classic_filename=classic_matched_filename, docmatch_filename=result_filename, output_filename=combined_output_filename)

        # make sure output file is written properly
        expected_lines = [
            'source bibcode (link),classic bibcode (link),curator comment,verified bibcode,matched bibcode (link),comment,label,confidence,matched scores',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021arXiv210607251P/abstract"",""2021arXiv210607251P"")","=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021PhDT........26P/abstract"",""2021PhDT........26P"")",agree,,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021PhDT........26P/abstract"",""2021PhDT........26P"")","",Match,0.8933332,"{\'abstract\': 1.0, \'title\': 1.0, \'author\': 1, \'year\': 1}"',
        ]
        with open(combined_output_filename, "r") as f:
            for expected_line, actual_line in zip(expected_lines, f.readlines()):
                self.assertEqual(expected_line, actual_line[:-1])

        # remove test files
        os.remove(result_filename)
        os.remove(classic_matched_filename)
        os.remove(combined_output_filename)

    def test_output_combine_classic_docmatch_results_pub(self):
        """ test combining classic matches with docmatching matches for pub """

        # setup filenames
        stubdata_dir = os.path.dirname(__file__) + '/stubdata'
        result_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_PUB_RESULT_FILENAME'])
        classic_matched_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_CLASSIC_MATCHES_FILENAME'])
        combined_output_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_PUB_COMBINED_FILENAME'])

        # create output file
        docmatch_lines = [
            'source bibcode (link),verified bibcode,matched bibcode (link),label,confidence,matched scores,comment',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2018ApJS..236...24F/abstract"",""2018ApJS..236...24F"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/.................../abstract"",""..................."")",Not Match,0,"","No matches with DOI [\'10.3847/1538-4365/aab760\'] in pubnote, trying Abstract. No result from solr with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request."',
        ]
        with open(result_filename, "w") as f:
            for line in docmatch_lines:
                f.write("%s\n"%line)
            f.close()

        # create classic matched file
        classic_lines = [
            '2018arXiv180101021F\t2018ApJS..236...24F\t1.000',
            '2018arXiv180109119RD\t2018ApJS..236...22R\t1.000',

        ]
        with open(classic_matched_filename, "w") as f:
            for line in classic_lines:
                f.write("%s\n"%line)
            f.close()

        # create combined classic and docmatch results
        self.match_metadata.merge_classic_docmatch_results(classic_filename=classic_matched_filename, docmatch_filename=result_filename, output_filename=combined_output_filename)

        # make sure output file is written properly
        expected_lines = [
            'source bibcode (link),classic bibcode (link),curator comment,verified bibcode,matched bibcode (link),comment,label,confidence,matched scores',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2018ApJS..236...24F/abstract"",""2018ApJS..236...24F"")","=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2018arXiv180101021F/abstract"",""2018arXiv180101021F"")",miss,,,"No matches with DOI [\'10.3847/1538-4365/aab760\'] in pubnote, trying Abstract. No result from solr with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request.",Not Match,0,""',
        ]
        with open(combined_output_filename, "r") as f:
            for expected_line, actual_line in zip(expected_lines, f.readlines()):
                self.assertEqual(expected_line, actual_line[:-1])

        # remove test files
        os.remove(result_filename)
        os.remove(classic_matched_filename)
        os.remove(combined_output_filename)

    def test_process_match_to_arXiv_without_classic_output(self):
        """ test test batch mode of match_to_arxiv when there is no classic output file """

        # create input file with list of pub filenames
        stubdata_dir = os.path.dirname(__file__) + '/stubdata'
        input_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_INPUT_FILENAME'])
        pub_filenames = ['/K47-02665.abs']
        with open(input_filename, "w") as f:
            for filename in pub_filenames:
                f.write("%s\n"%(stubdata_dir+filename))
            f.close()

        return_value = [{
            'source_bibcode': '2018ApJS..236...24F',
            'matched_bibcode': '...................',
            'label': 'Not Match',
            'confidence': 0,
            'score': '',
            'comment': "No matches with DOI ['10.3847/1538-4365/aab760'] in pubnote, trying Abstract. No result from solr with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request."
        }]

        # until classic is not turned off two files are created, result and combined
        # for now the function returns the combined file, but the intermidate file is created as well
        # once classic is truned off only the result (intermidate file is created) and returned
        expected_output_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_PUB_COMBINED_FILENAME'])
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            with mock.patch.object(self.match_metadata, 'process_pub_metadata', return_value=1):
                result_filename = self.match_metadata.process_match_to_arXiv(os.path.dirname(__file__) + '/stubdata')
                self.assertEqual(result_filename, expected_output_filename)

        # remove temp files
        os.remove(result_filename)
        os.remove("%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_PUB_RESULT_FILENAME']))
        os.remove(input_filename)

    def test_process_match_to_arXiv_with_classic_output(self):
        """ test test batch mode of match_to_arxiv when there is a classic matches """

        # create input file with list of pub filenames
        stubdata_dir = os.path.dirname(__file__) + '/stubdata'
        input_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_INPUT_FILENAME'])
        pub_filenames = ['/K47-02665.abs']
        with open(input_filename, "w") as f:
            for filename in pub_filenames:
                f.write("%s\n" % (stubdata_dir + filename))
            f.close()

        return_value = [{
            'source_bibcode': '2018ApJS..236...24F',
            'matched_bibcode': '...................',
            'label': 'Not Match',
            'confidence': 0,
            'score': '',
            'comment': "No matches with DOI ['10.3847/1538-4365/aab760'] in pubnote, trying Abstract. No result from solr with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request."
        }]

        # create classic matched file
        classic_matched_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_CLASSIC_MATCHES_FILENAME'])
        classic_lines = [
            '2018arXiv180101021F\t2018ApJS..236...24F\t1.000',
            '2018arXiv180109119RD\t2018ApJS..236...22R\t1.000',

        ]
        with open(classic_matched_filename, "w") as f:
            for line in classic_lines:
                f.write("%s\n"%line)
            f.close()

        expected_result_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_PUB_COMBINED_FILENAME'])
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            with mock.patch.object(self.match_metadata, 'process_pub_metadata', return_value=1):
                result_filename = self.match_metadata.process_match_to_arXiv(os.path.dirname(__file__) + '/stubdata')
                self.assertEqual(result_filename, expected_result_filename)

        # remove temp files
        os.remove(result_filename)
        os.remove("%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_PUB_RESULT_FILENAME']))
        os.remove(classic_matched_filename)
        os.remove(input_filename)

    def test_process_match_to_pub_without_classic_output(self):
        """ test batch mode of match_to_pub when there is no classic output file"""

        # create input file with list of eprint filenames
        stubdata_dir = os.path.dirname(__file__) + '/stubdata'
        input_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_INPUT_FILENAME'])
        eprint_filenames = ['/2106.07251']
        with open(input_filename, "w") as f:
            for filename in eprint_filenames:
                f.write("%s\n"%(stubdata_dir+filename))
            f.close()

        return_value = [{
            'source_bibcode': '2021arXiv210607251P',
            'confidence': 0.8989977,
            'label': 'Match',
            'score': "{'abstract': None, 'title': 1.0, 'author': 1, 'year': 1}",
            'matched_bibcode': '2020PhDT........36P',
            'comment': 'Matching doctype `phdthesis;mastersthesis`. Multi match: 1 of 2.'
        }, {
            'source_bibcode': '2021arXiv210607251P',
            'confidence': 0.8933332,
            'label': 'Match',
            'score': "{'abstract': 1.0, 'title': 1.0, 'author': 1, 'year': 1}",
            'matched_bibcode': '2021PhDT........26P',
            'comment': 'Matching doctype `phdthesis;mastersthesis`. Multi match: 2 of 2.'
        }]

        # until classic is not turned off two files are created, result and combined
        # for now the function returns the combined file, but the intermidate file is created as well
        # once classic is truned off only the result (intermidate file is created) and returned
        expected_result_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_EPRINT_COMBINED_FILENAME'])
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            result_filename = self.match_metadata.process_match_to_pub(os.path.dirname(__file__) + '/stubdata')
            self.assertEqual(result_filename, expected_result_filename)

        # remove temp files
        os.remove(result_filename)
        os.remove("%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_EPRINT_RESULT_FILENAME']))
        os.remove(input_filename)

    def test_process_match_to_pub_with_classic_output(self):
        """ test test batch mode of match_to_arxiv when there is a classic matches """

        # create input file with list of eprint filenames
        stubdata_dir = os.path.dirname(__file__) + '/stubdata'
        input_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_INPUT_FILENAME'])
        eprint_filenames = ['/2106.07251']
        with open(input_filename, "w") as f:
            for filename in eprint_filenames:
                f.write("%s\n" % (stubdata_dir + filename))
            f.close()

        return_value = [{
            'source_bibcode': '2021arXiv210607251P',
            'confidence': 0.8989977,
            'label': 'Match',
            'score': "{'abstract': None, 'title': 1.0, 'author': 1, 'year': 1}",
            'matched_bibcode': '2020PhDT........36P',
            'comment': 'Matching doctype `phdthesis;mastersthesis`. Multi match: 1 of 2.'
        }, {
            'source_bibcode': '2021arXiv210607251P',
            'confidence': 0.8933332,
            'label': 'Match',
            'score': "{'abstract': 1.0, 'title': 1.0, 'author': 1, 'year': 1}",
            'matched_bibcode': '2021PhDT........26P',
            'comment': 'Matching doctype `phdthesis;mastersthesis`. Multi match: 2 of 2.'
        }]

        # create classic matched file
        classic_matched_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_CLASSIC_MATCHES_FILENAME'])
        classic_lines = [
            '2021arXiv210607251P\t2021PhDT........26P\t1.000',
            '2022arXiv220403455D\t2023PRXQ....4a0309D\t1.000',

        ]
        with open(classic_matched_filename, "w") as f:
            for line in classic_lines:
                f.write("%s\n" % line)
            f.close()

        expected_result_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_EPRINT_COMBINED_FILENAME'])
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            result_filename = self.match_metadata.process_match_to_pub(os.path.dirname(__file__) + '/stubdata')
            self.assertEqual(result_filename, expected_result_filename)

        # remove temp files
        os.remove(result_filename)
        os.remove("%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_EPRINT_RESULT_FILENAME']))
        os.remove(classic_matched_filename)
        os.remove(input_filename)


    def test_process_pub_metadata(self):
        """ test calling process_pub_metadata """

        # setup returned values from matchable_status
        results = [{'summary': {'master': {'bibstem': 'JEOS', 'pubtype': 'Journal', 'not_indexed': False}}},
                   {'Error': 'Search failed', 'Error Info': 'Bibstem "NanoC" not found.'},
                   {'summary': {'master': {'bibstem': 'AAS', 'pubtype': 'Conf. Proc.', 'not_indexed': False}}}]
        return_values = []
        for result in results:
            return_values.append(self.create_response(result))

        metadata = [
            {'bibcode': '2023JEOS...19....4D'},
            {'bibcode': '2023JEOS...19....3Y'},
            {'bibcode': '2023NanoC..10...18D'},
            {'bibcode': '2023AAS...24147406B'},
            {'bibcode': '2023AAS...24147405A'},
            {'bibcode': '2023JEOS...19....2P'},
            {'bibcode': '2023NanoC..10...18D'},
        ]
        expected_results = [1, 1, -1, 0, 0, 1, -1]
        with mock.patch('requests.get', side_effect=return_values):
            for meta, expected in zip(metadata, expected_results):
                self.assertEqual(self.match_metadata.process_pub_metadata(meta), expected)

    def test_write_results(self):
        """ test writing filenames to rerun files """
        stubdata_dir = os.path.dirname(__file__) + '/stubdata'
        result_filename = "%s%s" % (stubdata_dir, config['DOCMATCHPIPELINE_EPRINT_RESULT_FILENAME'])
        rerun_filename = os.path.abspath(os.path.join(stubdata_dir, config['DOCMATCHPIPELINE_RERUN_FILENAME']))
        eprint_filename = "%s%s"% (stubdata_dir, '/2305/03053')
        matches = self.match_metadata.process_results([{
            'source_bibcode': '2023arXiv230503053S',
            'status_flaw' : "got 502 for the last failed attempt, shall be added to rerun list."}], '\t')
        expected_results = [
            "source bibcode (link),verified bibcode,matched bibcode (link),label,confidence,matched scores,comment",
            "['2023arXiv230503053S  status_flaw=got 502 for the last failed attempt, shall be added to rerun list.']"
        ]
        expected_rerun = [eprint_filename]
        self.match_metadata.write_results(result_filename, matches, eprint_filename, rerun_filename)

        # also generate error for journalDB and see that it does not get logged
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=[]):
            with mock.patch.object(self.match_metadata, 'process_pub_metadata', return_value=0):
                self.match_metadata.single_match_to_arXiv(pub_filename=os.path.dirname(__file__) + '/stubdata/K88-62345.abs')
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=[]):
            with mock.patch.object(self.match_metadata, 'process_pub_metadata', return_value=-1):
                self.match_metadata.single_match_to_arXiv(pub_filename=os.path.dirname(__file__) + '/stubdata/K88-62345.abs')

        # verify content of files
        with open(result_filename, "r") as f:
            for expected_line, actual_line in zip(expected_results, f.readlines()):
                self.assertEqual(expected_line, actual_line[:-1])
        with open(rerun_filename, "r") as f:
            for expected_line, actual_line in zip(expected_rerun, f.readlines()):
                self.assertEqual(expected_line, actual_line[:-1])

        os.remove(result_filename)
        os.remove(rerun_filename)

if __name__ == '__main__':
    unittest.main()

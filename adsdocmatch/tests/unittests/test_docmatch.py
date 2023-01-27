import sys, os
project_home = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

import unittest
import mock

from adsputils import load_config
from adsdocmatch.match_w_metadata import MatchMetadata

config = load_config(proj_home=project_home)

class TestDocMatch(unittest.TestCase):

    def setUp(self):
        self.match_metadata = MatchMetadata()

    def tearDown(self):
        pass

    def test_match_to_arXiv_1(self):
        """ test match_to_arXiv when there are no matches """

        return_value = {
            'source_bibcode': '2018ApJS..236...24F',
            'matched_bibcode': '...................',
            'label': 'Not Match', 'confidence': 0,
            'score': '',
            'comment': "No matches with DOI ['10.3847/1538-4365/aab760'] in pubnote, trying Abstract. No result from solr with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request."
        }
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            single_match, multi_matches = self.match_metadata.single_match_to_arXiv(pub_filename=os.path.dirname(__file__) + '/stubdata/K47-02665.abs')
            single_match = single_match.split('\t')
            assert(single_match[0] == '2018ApJS..236...24F')
            assert(single_match[1] == '...................')
            assert(single_match[2] == 'Not Match')
            assert(single_match[3] == '0')
            assert(single_match[4] == '')
            assert(single_match[5] == "No matches with DOI ['10.3847/1538-4365/aab760'] in pubnote, trying Abstract. No result from solr with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request.")
            assert(multi_matches == None)
            
    def test_match_to_arXiv_2(self):
        """ test match_to_arXiv when a match is detected """

        return_value = {
            'source_bibcode': '2022PhRvD.106i6008H',
            'matched_bibcode': '2021arXiv210806768H',
            'label': 'Match',
            'confidence': 0.9407689,
            'score': {'abstract': 0.93, 'title': 0.89, 'author': 1, 'year': 1},
            'comment': "No matches with DOI ['10.1103/PhysRevD.106.096008'] in pubnote, trying Abstract."
        }
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            single_match, multi_matches = self.match_metadata.single_match_to_arXiv(pub_filename=os.path.dirname(__file__) + '/stubdata/K88-62345.abs')
            single_match = single_match.split('\t')
            assert(single_match[0] == '2022PhRvD.106i6008H')
            assert(single_match[1] == '2021arXiv210806768H')
            assert(single_match[2] == 'Match')
            assert(single_match[3] == '0.9407689')
            assert(single_match[4] == "{'abstract': 0.93, 'title': 0.89, 'author': 1, 'year': 1}")
            assert(single_match[5] == "No matches with DOI ['10.1103/PhysRevD.106.096008'] in pubnote, trying Abstract.")
            assert(multi_matches == None)

    def test_match_to_pub_1(self):
        """ test match_to_pub when there are no matches"""

        return_value = {
            'source_bibcode': '2017arXiv170100200T',
            'matched_bibcode': '...................',
            'label': 'Not Match',
            'confidence': 0,
            'score': '',
            'comment': 'No matches with Abstract, trying Title. No document was found in solr matching the request.'
        }
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            single_match, multi_matches = self.match_metadata.single_match_to_pub(arXiv_filename=os.path.dirname(__file__) + '/stubdata/1701.00200')
            single_match = single_match.split('\t')
            assert(single_match[0] == '2017arXiv170100200T')
            assert(single_match[1] == '...................')
            assert(single_match[2] == 'Not Match')
            assert(single_match[3] == '0')
            assert(single_match[4] == '')
            assert(single_match[5] == 'No matches with Abstract, trying Title. No document was found in solr matching the request.')
            assert(multi_matches == None)

    def test_match_to_pub_2(self):
        """ test match_to_pub when a match is detected"""

        return_value = {
            'source_bibcode': '2018arXiv180101021F',
            'matched_bibcode': '2018ApJS..236...24F',
            'label': 'Match',
            'confidence': 0.9957643,
            'score': {'abstract': 0.98, 'title': 0.98, 'author': 1, 'year': 1, 'doi': 1},
            'comment': ''
        }
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            single_match, multi_matches = self.match_metadata.single_match_to_pub(arXiv_filename=os.path.dirname(__file__) + '/stubdata/1801.01021')
            single_match = single_match.split('\t')
            assert(single_match[0] == '2018arXiv180101021F')
            assert(single_match[1] == '2018ApJS..236...24F')
            assert(single_match[2] == 'Match')
            assert(single_match[3] == '0.9957643')
            assert(single_match[4] == "{'abstract': 0.98, 'title': 0.98, 'author': 1, 'year': 1, 'doi': 1}")
            assert(single_match[5] == '')
            assert(multi_matches == None)

    def test_match_to_pub_3(self):
        """ test match_to_pub when match is in db"""

        return_value = {
            'source_bibcode': '2007arXiv0708.1752V',
            'matched_bibcode': '2007A&A...474..653V',
            'label': 'Match',
            'confidence': 0.9961402,
            'score': {},
            'comment': ''
        }
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            single_match, multi_matches = self.match_metadata.single_match_to_pub(arXiv_filename=os.path.dirname(__file__) + '/stubdata/0708.1752')
            single_match = single_match.split('\t')
            assert(single_match[0] == '2007arXiv0708.1752V')
            assert(single_match[1] == '2007A&A...474..653V')
            assert(single_match[2] == 'Match')
            assert(single_match[3] == '0.9961402')
            assert(single_match[4] == "{}")
            assert(single_match[5] == '')
            assert(multi_matches == None)

    def test_match_to_pub_4(self):
        """ test match_to_pub when multiple matches are detected """

        return_value = {
            'source_bibcode': '2021arXiv210607251P',
            'matched_bibcode': '...................',
            'label': 'Not Match',
            'confidence': 'Multi match!',
            'score': '',
            'comment': 'Matching doctype `phdthesis;mastersthesis`. Match(es) for this bibcode is in the `inspection` field.',
            'inspection': [
                            {
                                'source_bibcode': '2021arXiv210607251P',
                                'confidence': 0.8989977,
                                'label': 'Match',
                                'scores': "{'abstract': None, 'title': 1.0, 'author': 1, 'year': 1}",
                                'matched_bibcode': '2020PhDT........36P',
                                'comment': 'Multi match: 1 of 2.'
                            }, {
                                'source_bibcode': '2021arXiv210607251P',
                                'confidence': 0.8933332,
                                'label': 'Match',
                                'scores': "{'abstract': 1.0, 'title': 1.0, 'author': 1, 'year': 1}",
                                'matched_bibcode': '2021PhDT........26P',
                                'comment': 'Multi match: 2 of 2.'
                            }
            ]
        }
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            single_match, multi_matches = self.match_metadata.single_match_to_pub(arXiv_filename=os.path.dirname(__file__) + '/stubdata/2106.07251')
            single_match = single_match.split('\t')
            assert(single_match[0] == '2021arXiv210607251P')
            assert(single_match[1] == '...................')
            assert(single_match[2] == 'Not Match')
            assert(single_match[3] == 'Multi match!')
            assert(single_match[4] == '')
            assert(single_match[5] == "Matching doctype `phdthesis;mastersthesis`. Match(es) for this bibcode is in the `inspection` field.")
            assert(len(multi_matches) == 2)
            assert(multi_matches[0]['source_bibcode'] == '2021arXiv210607251P')
            assert(multi_matches[0]['matched_bibcode'] == '2020PhDT........36P')
            assert(multi_matches[0]['label'] == 'Match')
            assert(multi_matches[0]['confidence'] == 0.8989977)
            assert(multi_matches[0]['scores'] == "{'abstract': None, 'title': 1.0, 'author': 1, 'year': 1}")
            assert(multi_matches[0]['comment'] == 'Multi match: 1 of 2.')
            assert(multi_matches[1]['source_bibcode'] == '2021arXiv210607251P')
            assert(multi_matches[1]['matched_bibcode'] == '2021PhDT........26P')
            assert(multi_matches[1]['label'] == 'Match')
            assert(multi_matches[1]['confidence'] == 0.8933332)
            assert(multi_matches[1]['scores'] == "{'abstract': 1.0, 'title': 1.0, 'author': 1, 'year': 1}")
            assert(multi_matches[1]['comment'] == 'Multi match: 2 of 2.')

    def test_batch_match_to_pub(self):
        """ """
        # create input file with list of eprint filenames
        eprint_filenames = ['/stubdata/0708.1752', '/stubdata/1701.00200', '/stubdata/1801.01021', '/stubdata/2106.07251']
        path = os.path.dirname(__file__)
        with open(path + '/stubdata/eprint.input', "w") as f:
            for filename in eprint_filenames:
                f.write("%s\n"%(path+filename))
            f.close()
        # create output file
        self.match_metadata.batch_match_to_pub(input_filename=path + '/stubdata/eprint.input', result_filename=os.path.dirname(__file__) + '/stubdata/eprint.output')
        expected_lines = [
            'source bibcode (link),verified bibcode,matched bibcode (link),label,confidence,matched scores,comment',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2007arXiv0708.1752V/abstract"",""2007arXiv0708.1752V"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2007A&A...474..653V/abstract"",""2007A&A...474..653V"")",Match,0.9961402,"{}",""',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2017arXiv170100200T/abstract"",""2017arXiv170100200T"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/.................../abstract"",""..................."")",Not Match,0,"","No matches with Abstract, trying Title. No document was found in solr matching the request."',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2018arXiv180101021F/abstract"",""2018arXiv180101021F"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2018ApJS..236...24F/abstract"",""2018ApJS..236...24F"")",Match,0.9957643,"{\'abstract\': 0.98, \'title\': 0.98, \'author\': 1, \'year\': 1, \'doi\': 1}",""',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021arXiv210607251P/abstract"",""2021arXiv210607251P"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2020PhDT........36P/abstract"",""2020PhDT........36P"")",Match,0.8989977,"{\'abstract\': None, \'title\': 1.0, \'author\': 1, \'year\': 1}","Multi match: 1 of 2."',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021arXiv210607251P/abstract"",""2021arXiv210607251P"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021PhDT........26P/abstract"",""2021PhDT........26P"")",Match,0.8933332,"{\'abstract\': 1.0, \'title\': 1.0, \'author\': 1, \'year\': 1}","Multi match: 2 of 2."',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2007arXiv0708.1752V/abstract"",""2007arXiv0708.1752V"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2007A&A...474..653V/abstract"",""2007A&A...474..653V"")",Match,0.9961402,"{}",""',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2017arXiv170100200T/abstract"",""2017arXiv170100200T"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/.................../abstract"",""..................."")",Not Match,0,"","No matches with Abstract, trying Title. No document was found in solr matching the request."',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2018arXiv180101021F/abstract"",""2018arXiv180101021F"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2018ApJS..236...24F/abstract"",""2018ApJS..236...24F"")",Match,0.9957643,"{\'abstract\': 0.98, \'title\': 0.98, \'author\': 1, \'year\': 1, \'doi\': 1}",""',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021arXiv210607251P/abstract"",""2021arXiv210607251P"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2020PhDT........36P/abstract"",""2020PhDT........36P"")",Match,0.8989977,"{\'abstract\': None, \'title\': 1.0, \'author\': 1, \'year\': 1}","Multi match: 1 of 2."',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021arXiv210607251P/abstract"",""2021arXiv210607251P"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021PhDT........26P/abstract"",""2021PhDT........26P"")",Match,0.8933332,"{\'abstract\': 1.0, \'title\': 1.0, \'author\': 1, \'year\': 1}","Multi match: 2 of 2."',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2007arXiv0708.1752V/abstract"",""2007arXiv0708.1752V"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2007A&A...474..653V/abstract"",""2007A&A...474..653V"")",Match,0.9961402,"{}",""',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2017arXiv170100200T/abstract"",""2017arXiv170100200T"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/.................../abstract"",""..................."")",Not Match,0,"","No matches with Abstract, trying Title. No document was found in solr matching the request."',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2018arXiv180101021F/abstract"",""2018arXiv180101021F"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2018ApJS..236...24F/abstract"",""2018ApJS..236...24F"")",Match,0.9957643,"{\'abstract\': 0.98, \'title\': 0.98, \'author\': 1, \'year\': 1, \'doi\': 1}",""',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021arXiv210607251P/abstract"",""2021arXiv210607251P"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2020PhDT........36P/abstract"",""2020PhDT........36P"")",Match,0.8989977,"{\'abstract\': None, \'title\': 1.0, \'author\': 1, \'year\': 1}","Multi match: 1 of 2."',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021arXiv210607251P/abstract"",""2021arXiv210607251P"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021PhDT........26P/abstract"",""2021PhDT........26P"")",Match,0.8933332,"{\'abstract\': 1.0, \'title\': 1.0, \'author\': 1, \'year\': 1}","Multi match: 2 of 2."',
        ]
        # make sure output file is written properly
        with open(path + '/stubdata/eprint.output.csv', "r") as f:
            for expected_line, actual_line in zip(expected_lines, f.readlines()):
                assert(expected_line == actual_line[:-1])
        # remove temp files
        os.remove(path + '/stubdata/eprint.input')
        os.remove(path + '/stubdata/eprint.output.csv')

    def test_batch_match_to_arXiv(self):
        """ """
        # create input file with list of pub filenames
        eprint_filenames = ['/stubdata/K47-02665.abs', '/stubdata/K88-62345.abs']
        path = os.path.dirname(__file__)
        with open(path + '/stubdata/pub.input', "w") as f:
            for filename in eprint_filenames:
                f.write("%s\n"%(path+filename))
            f.close()
        # create output file
        self.match_metadata.batch_match_to_arXiv(input_filename=path + '/stubdata/pub.input', result_filename=os.path.dirname(__file__) + '/stubdata/pub.output')
        expected_lines = [
            'source bibcode (link),verified bibcode,matched bibcode (link),label,confidence,matched scores,comment',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2018ApJS..236...24F/abstract"",""2018ApJS..236...24F"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/.................../abstract"",""..................."")",Not Match,0,"","No matches with DOI [\'10.3847/1538-4365/aab760\'] in pubnote, trying Abstract. No result from solr with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request."',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2022PhRvD.106i6008H/abstract"",""2022PhRvD.106i6008H"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021arXiv210806768H/abstract"",""2021arXiv210806768H"")",Match,0.9407689,"{}","No matches with DOI [\'10.1103/PhysRevD.106.096008\'] in pubnote, trying Abstract."',
        ]
        # make sure output file is written properly
        with open(path + '/stubdata/pub.output.csv', "r") as f:
            for expected_line, actual_line in zip(expected_lines, f.readlines()):
                assert(expected_line == actual_line[:-1])
        # remove temp files
        os.remove(path + '/stubdata/pub.input')
        os.remove(path + '/stubdata/pub.output.csv')

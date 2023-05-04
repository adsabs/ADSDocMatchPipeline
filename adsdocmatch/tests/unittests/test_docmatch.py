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

        return_value = [{
            'source_bibcode': '2018ApJS..236...24F',
            'matched_bibcode': '...................',
            'label': 'Not Match', 'confidence': 0,
            'score': '',
            'comment': "No matches with DOI ['10.3847/1538-4365/aab760'] in pubnote, trying Abstract. No result from solr with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request."
        }]
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            matches = self.match_metadata.single_match_to_arXiv(pub_filename=os.path.dirname(__file__) + '/stubdata/K47-02665.abs')
            assert(len(matches) == 1)
            fields = matches[0].split('\t')
            assert(len(fields) == 6)
            assert(fields[0] == '2018ApJS..236...24F')
            assert(fields[1] == '...................')
            assert(fields[2] == 'Not Match')
            assert(fields[3] == '0')
            assert(fields[4] == '')
            assert(fields[5] == "No matches with DOI ['10.3847/1538-4365/aab760'] in pubnote, trying Abstract. No result from solr with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request.")

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
            matches = self.match_metadata.single_match_to_arXiv(pub_filename=os.path.dirname(__file__) + '/stubdata/K88-62345.abs')
            assert(len(matches) == 1)
            fields = matches[0].split('\t')
            assert(len(fields) == 6)
            assert(fields[0] == '2022PhRvD.106i6008H')
            assert(fields[1] == '2021arXiv210806768H')
            assert(fields[2] == 'Match')
            assert(fields[3] == '0.9407689')
            assert(fields[4] == "{'abstract': 0.93, 'title': 0.89, 'author': 1, 'year': 1}")
            assert(fields[5] == "No matches with DOI ['10.1103/PhysRevD.106.096008'] in pubnote, trying Abstract.")

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
            matches = self.match_metadata.single_match_to_pub(arXiv_filename=os.path.dirname(__file__) + '/stubdata/1701.00200')
            assert(len(matches) == 1)
            fields = matches[0].split('\t')
            assert(len(fields) == 6)
            assert(fields[0] == '2017arXiv170100200T')
            assert(fields[1] == '...................')
            assert(fields[2] == 'Not Match')
            assert(fields[3] == '0')
            assert(fields[4] == '')
            assert(fields[5] == 'No matches with Abstract, trying Title. No document was found in solr matching the request.')

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
            matches = self.match_metadata.single_match_to_pub(arXiv_filename=os.path.dirname(__file__) + '/stubdata/1801.01021')
            assert(len(matches) == 1)
            fields = matches[0].split('\t')
            assert(len(fields) == 6)
            assert(fields[0] == '2018arXiv180101021F')
            assert(fields[1] == '2018ApJS..236...24F')
            assert(fields[2] == 'Match')
            assert(fields[3] == '0.9957643')
            assert(fields[4] == "{'abstract': 0.98, 'title': 0.98, 'author': 1, 'year': 1, 'doi': 1}")
            assert(fields[5] == '')

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
            matches = self.match_metadata.single_match_to_pub(arXiv_filename=os.path.dirname(__file__) + '/stubdata/0708.1752')
            assert(len(matches) == 1)
            fields = matches[0].split('\t')
            assert(len(fields) == 6)
            assert(fields[0] == '2007arXiv0708.1752V')
            assert(fields[1] == '2007A&A...474..653V')
            assert(fields[2] == 'Match')
            assert(fields[3] == '0.9961402')
            assert(fields[4] == "{}")
            assert(fields[5] == '')

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
            matches = self.match_metadata.single_match_to_pub(arXiv_filename=os.path.dirname(__file__) + '/stubdata/2106.07251')
            assert(len(matches) == 2)
            expected_values = [
                ['2021arXiv210607251P','2020PhDT........36P','Match','0.8989977',"{'abstract': None, 'title': 1.0, 'author': 1, 'year': 1}",'Matching doctype `phdthesis;mastersthesis`. Multi match: 1 of 2.'],
                ['2021arXiv210607251P','2021PhDT........26P','Match','0.8933332',"{'abstract': 1.0, 'title': 1.0, 'author': 1, 'year': 1}",'Matching doctype `phdthesis;mastersthesis`. Multi match: 2 of 2.']
            ]
            for match, expected_value in zip(matches, expected_values):
                fields = match.split('\t')
                assert(len(fields) == 6)
                for i in range(len(fields)):
                    assert(fields[i] == expected_value[i])

    def test_batch_match_to_pub(self):
        """ test batch mode of match_to_pub """

        # setup filenames
        path = os.path.dirname(__file__)
        current_dir = '/stubdata'
        input_filename = "%s%s%s" % (path, current_dir, config['DOCMATCHPIPELINE_INPUT_FILENAME'])
        result_filename = "%s%s%s" % (path, current_dir, config['DOCMATCHPIPELINE_EPRINT_RESULT_FILENAME'])

        # create input file with list of eprint filenames
        eprint_filenames = ['/2106.07251']
        with open(input_filename, "w") as f:
            for filename in eprint_filenames:
                f.write("%s\n"%(path+current_dir+filename))
            f.close()

        # create output file
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
            self.match_metadata.batch_match_to_pub(input_filename=input_filename, result_filename=result_filename)

        # make sure output file is written properly
        expected_lines = [
            'source bibcode (link),verified bibcode,matched bibcode (link),label,confidence,matched scores,comment',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021arXiv210607251P/abstract"",""2021arXiv210607251P"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2020PhDT........36P/abstract"",""2020PhDT........36P"")",Match,0.8989977,"{\'abstract\': None, \'title\': 1.0, \'author\': 1, \'year\': 1}","Matching doctype `phdthesis;mastersthesis`. Multi match: 1 of 2."',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021arXiv210607251P/abstract"",""2021arXiv210607251P"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2021PhDT........26P/abstract"",""2021PhDT........26P"")",Match,0.8933332,"{\'abstract\': 1.0, \'title\': 1.0, \'author\': 1, \'year\': 1}","Matching doctype `phdthesis;mastersthesis`. Multi match: 2 of 2."',
        ]
        with open(result_filename, "r") as f:
            for expected_line, actual_line in zip(expected_lines, f.readlines()):
                assert(expected_line == actual_line[:-1])

        # remove temp files
        os.remove(input_filename)
        os.remove(result_filename)

    def test_batch_match_to_arXiv(self):
        """ test batch mode of match_to_arxiv """

        # setup filenames
        path = os.path.dirname(__file__)
        current_dir = '/stubdata'
        input_filename = "%s%s%s" % (path, current_dir, config['DOCMATCHPIPELINE_INPUT_FILENAME'])
        result_filename = "%s%s%s" % (path, current_dir, config['DOCMATCHPIPELINE_EPRINT_RESULT_FILENAME'])

        print('lolwut i/o: %s /// %s' % (input_filename, result_filename))
        # create input file with list of pub filenames
        eprint_filenames = ['/K47-02665.abs']
        mocked_eprint_filenames = []
        with open(input_filename, "w") as f:
            for filename in eprint_filenames:
                f.write("%s\n"%(path+current_dir+filename))
                mocked_eprint_filenames.append("%s" % (path+current_dir+filename))
            f.close()

        print('i made it here... "create output file"')
        # create output file
        return_value = [{
            'source_bibcode': '2018ApJS..236...24F',
            'matched_bibcode': '...................',
            'label': 'Not Match', 'confidence': 0,
            'score': '',
            'comment': "No matches with DOI ['10.3847/1538-4365/aab760'] in pubnote, trying Abstract. No result from solr with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request."
        }]
        with mock.patch.object(self.match_metadata.ORACLE_UTIL, 'get_matches', return_value=return_value):
            with mock.patch.object(self.match_metadata, 'get_ads_record_filenames', return_value=mocked_eprint_filenames):
                self.match_metadata.batch_match_to_arXiv(input_filename=input_filename, result_filename=result_filename)
        expected_lines = [
            'source bibcode (link),verified bibcode,matched bibcode (link),label,confidence,matched scores,comment',
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2018ApJS..236...24F/abstract"",""2018ApJS..236...24F"")",,"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/.................../abstract"",""..................."")",Not Match,0,"","No matches with DOI [\'10.3847/1538-4365/aab760\'] in pubnote, trying Abstract. No result from solr with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request."',
        ]
        print('i made it here "make sure output file is written properly"')

        # make sure output file is written properly
        with open(result_filename, "r") as f:
            for expected_line, actual_line in zip(expected_lines, f.readlines()):
                assert(expected_line == actual_line[:-1])

        # remove test files
        os.remove(input_filename)
        os.remove(result_filename)

    def test_output_combine_classic_docmatch_results_eprint(self):
        """ test combining classic matches with docmatching matches for eprint """

        # setup filenames
        path = os.path.dirname(__file__)
        current_dir = '/stubdata'
        result_filename = "%s%s%s" % (path, current_dir, config['DOCMATCHPIPELINE_EPRINT_RESULT_FILENAME'])
        classic_matched_filename = "%s%s%s" % (path, current_dir, config['DOCMATCHPIPELINE_CLASSIC_MATCHES_FILENAME'])
        combined_output_filename = "%s%s%s" % (path, current_dir, config['DOCMATCHPIPELINE_EPRINT_COMBINED_FILENAME'])

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
                assert(expected_line == actual_line[:-1])

        # remove test files
        os.remove(result_filename)
        os.remove(classic_matched_filename)
        os.remove(combined_output_filename)

    def test_output_combine_classic_docmatch_results_pub(self):
        """ test combining classic matches with docmatching matches for pub """

        # setup filenames
        path = os.path.dirname(__file__)
        current_dir = '/stubdata'
        result_filename = "%s%s%s" % (path, current_dir, config['DOCMATCHPIPELINE_PUB_RESULT_FILENAME'])
        classic_matched_filename = "%s%s%s" % (path, current_dir, config['DOCMATCHPIPELINE_CLASSIC_MATCHES_FILENAME'])
        combined_output_filename = "%s%s%s" % (path, current_dir, config['DOCMATCHPIPELINE_PUB_COMBINED_FILENAME'])

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
            '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2018ApJS..236...24F/abstract"",""2018ApJS..236...24F"")","=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/2018arXiv180101021F/abstract"",""2018arXiv180101021F"")",disagree,,,"No matches with DOI [\'10.3847/1538-4365/aab760\'] in pubnote, trying Abstract. No result from solr with Abstract, trying Title. No result from solr with Title. No document was found in solr matching the request.",Not Match,0,""',
        ]
        with open(combined_output_filename, "r") as f:
            for expected_line, actual_line in zip(expected_lines, f.readlines()):
                assert(expected_line == actual_line[:-1])

        # remove test files
        os.remove(result_filename)
        os.remove(classic_matched_filename)
        os.remove(combined_output_filename)

    def test_normalize_author_list(self):
        """ """
        eprint_filenames = ['/2106.07251', '/1701.00200', '/1801.01021', '/2106.07251']
        path = os.path.dirname(__file__)
        current_dir = '/stubdata'

        expected_authors = ['Proxauf, B', 'Tang, X', 'Frey, K; Accomazzi, A', 'Proxauf, B']
        for filename, authors in zip(eprint_filenames, expected_authors):
            fullpath = path + current_dir + filename
            with open(fullpath, 'rb') as arxiv_fp:
                metadata = self.match_metadata.ARXIV_PARSER.parse(arxiv_fp)
                self.assertEqual(self.match_metadata.ORACLE_UTIL.normalize_author_list(metadata['authors']), authors)

    def test_extract_doi(self):
        """ """
        eprint_filenames = ['/2106.07251', '/1701.00200', '/1801.01021', '/2106.07251']
        path = os.path.dirname(__file__)
        current_dir = '/stubdata'

        expected_dois = [['10.53846/goediss-8502'], None, ['10.3847/1538-4365/aab760'], ['10.53846/goediss-8502']]
        for filename, doi in zip(eprint_filenames, expected_dois):
            fullpath = path + current_dir + filename
            with open(fullpath, 'rb') as arxiv_fp:
                metadata = self.match_metadata.ARXIV_PARSER.parse(arxiv_fp)
                self.assertEqual(self.match_metadata.ORACLE_UTIL.extract_doi(metadata), doi)

    def test_read_google_sheet(self):
        """ """
        match_w_pub_filename = os.path.dirname(__file__) + '/stubdata/' + '2023-01-25.compare_eprint.csv.xlsx'
        results = self.match_metadata.ORACLE_UTIL.read_google_sheet(match_w_pub_filename)
        expected = [
            ['2021arXiv210913594W', '2023Quant...7..900W', '1.1'],
            ['2021arXiv211102596P', '2023Quant...7..898P', '1.1'],
            ['2022arXiv220400632S', '2023PhRvL.130d3601S', '1.1'],
            ['2022arXiv220405794W', '2023Quant...7..903W', '1.1'],
            ['2022arXiv220412715L', '2023NJPh...25a3009L', '1.1'],
            ['2022arXiv220503149P', '2023PhRvC.107a4910P', '1.1'],
            ['2022arXiv220508471N', '2023E&ES.1136a2018N', '1.1'],
            ['2022arXiv220602637S', '2023NJPh...25a3015S', '1.1'],
            ['2022arXiv220611916G', '2023PhRvB.107d1301G', '1.1'],
            ['2022arXiv220612105S', '2023PhRvA.107a2422S', '1.1'],
            ['2022arXiv220705646C', '2023Quant...7..902C', '1.1'],
            ['2022arXiv220709366B', '2023PhRvL.130d1901B', '1.1'],
            ['2022arXiv220809620C', '2023PhRvA.107a3307C', '1.1'],
            ['2022arXiv220814400A', '2023PhRvB.107c5424A', '1.1'],
            ['2022arXiv220905830T', '2023PhRvB.107c5125T', '1.1'],
            ['2022arXiv221015213I', '2023PhRvD.107a6011I', '1.1'],
            ['2022arXiv221100521S', '2023PhRvM...7a4003S', '1.1'],
            ['2022arXiv221104744P', '2023PhRvA.107a2812P', '1.1'],
            ['2022arXiv221107207G', '2023PhRvL.130d3602G', '1.1'],
            ['2022arXiv221107754C', '2023JHEP...01..071C', '1.1'],
            ['2022arXiv221108072G', '2023PhRvB.107b4416G', '1.1'],
            ['2022arXiv221112960L', '2023PhRvD.107a3006L', '1.1'],
            ['2023arXiv230109795G', '2023Symm...15..259G', '1.1'],
            ['2023arXiv230109798L', '2023PhRvE.107a5105L', '1.1'],
            ['2021arXiv210607251P', '2021PhDT........26P', '1.1'],
            ['2021arXiv210607251P', '2021PhDT........26P', '1.1'],
            ['2023arXiv230110072K', '2021OExpr..2923736K', '1.1'],
            ['2021arXiv210607251P', '2020PhDT........36P', '-1']
        ]
        assert(results == expected)

        match_w_eprint_filename = os.path.dirname(__file__) + '/stubdata/' + '2023-01-24.compare_pub.csv.xlsx'
        results = self.match_metadata.ORACLE_UTIL.read_google_sheet(match_w_eprint_filename)
        expected = [
            ['2023arXiv230108396S', '2023JPhCo...7a5001S', '1.1'],
            ['2022arXiv220911954M', '2022ConPh..63...34M', '1.1'],
            ['2022arXiv220600058K', '2023ITAP...71..650K', '1.1'],
            ['2022arXiv221007569T', '2023JPSJ...92b3601T', '1.1'],
            ['2019arXiv191101730S', '2020Quant...4..240S', '1.1'],
            ['2019arXiv191110999D', '2022AIHPC..39.1485D', '1.1'],
            ['2020arXiv200909163Z', '2022ITSP...70.6272Z', '1.1'],
            ['2021arXiv211104351I', '2022Quant...6..718I', '-1'],
            ['2022arXiv220306611J', '2022Quant...6..669J', '1.1'],
            ['2020arXiv201206687J', '2022Quant...6..669J', '-1']
        ]
        assert(results == expected)

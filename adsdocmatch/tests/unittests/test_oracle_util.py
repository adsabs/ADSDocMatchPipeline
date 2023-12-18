import sys, os
project_home = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

import unittest
import mock
import json
import requests

from adsputils import load_config
from adsdocmatch.match_w_metadata import MatchMetadata
from adsdocmatch.pub_parser import get_pub_metadata

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

    def test_normalize_author_list(self):
        """ """
        eprint_filenames = ['X18-10145.abs', 'X10-50737.abs', 'X11-85081.abs', 'X23-45511.abs']
        stubdata_dir = os.path.dirname(__file__) + '/stubdata/'

        expected_authors = ['Proxauf, B', 'Tang, X', 'Frey, K; Accomazzi, A', 'Shapurian, G; Kurtz, M; Accomazzi, A']
        for filename, authors in zip(eprint_filenames, expected_authors):
            fullpath = stubdata_dir + filename
            with open(fullpath, 'rb') as arxiv_fp:
                metadata = get_pub_metadata(arxiv_fp.read())
                self.assertEqual(self.match_metadata.ORACLE_UTIL.normalize_author_list(metadata['authors']), authors)

        # what if only lastnames are provided
        author_lastnames_only = 'Proxauf; Tang; Frey'
        self.assertEqual(self.match_metadata.ORACLE_UTIL.normalize_author_list(author_lastnames_only), author_lastnames_only)

        # with collabration
        collabrations = ['the ALICE Collaboration; Lijiao, Liu', 'Lijiao, Liu; the ALICE Collaboration']
        for collab in collabrations:
            self.assertEqual(self.match_metadata.ORACLE_UTIL.normalize_author_list(collab), 'the ALICE Collaboration; Lijiao, L')

        # only collabration
        self.assertEqual(self.match_metadata.ORACLE_UTIL.normalize_author_list('the ALICE Collaboration'), 'the ALICE Collaboration')

        authors = {
            'Frey, K, Accomazzi, A': 'Frey; Accomazzi',
            'Frey, K., Accomazzi, A.': 'Frey, K; Accomazzi, A',
            'K. Frey, A. Accomazzi': 'Frey, K; Accomazzi, A',
            'Katie Frey, Alberto Accomazzi': 'Frey, K; Accomazzi, A',
            'Frey, Katie, Accomazzi, Alberto': 'Frey, K; Accomazzi, A',
            'Frey and Accomazzi': 'Frey; Accomazzi',
            'K Frey, A Accomazzi': 'Frey; Accomazzi',
            'K. Frey and A. Accomazzi': 'Frey, K; Accomazzi, A',
            'Frey, K, Accomazzi, A etal.': 'Frey; Accomazzi',
        }
        for authors_raw, authors_normalized in authors.items():
            self.assertEqual(self.match_metadata.ORACLE_UTIL.normalize_author_list(authors_raw), authors_normalized)

    def test_extract_doi(self):
        """ """
        eprint_filenames = ['X18-10145.abs', 'X10-50737.abs', 'X11-85081.abs', 'X23-45511.abs']
        stubdata_dir = os.path.dirname(__file__) + '/stubdata/'

        expected_dois = [['10.53846/goediss-8502'], None, ['10.3847/1538-4365/aab760'], None]
        for filename, doi in zip(eprint_filenames, expected_dois):
            fullpath = stubdata_dir + filename
            with open(fullpath, 'rb') as arxiv_fp:
                metadata = get_pub_metadata(arxiv_fp.read())
                metadata, _, _, _ = self.match_metadata.parse_arXiv_comments(metadata)
                self.assertEqual(self.match_metadata.ORACLE_UTIL.extract_doi(metadata), doi)

    def test_read_google_sheet(self):
        """ test reading google sheet """

        # setup returned values from oracle source-score function
        results = [{'confidence': 1.3}, {'confidence': -1}]
        return_values = []
        for result in results:
            return_values.append(self.create_response(result))

        # test when matching with eprint
        match_w_pub_filename = os.path.dirname(__file__) + '/stubdata/' + '2023-01-25.compare_eprint.csv.xlsx'
        expected = [
            ['2021arXiv210913594W', '2023Quant...7..900W', '1.3'],
            ['2021arXiv211102596P', '2023Quant...7..898P', '1.3'],
            ['2022arXiv220400632S', '2023PhRvL.130d3601S', '1.3'],
            ['2022arXiv220405794W', '2023Quant...7..903W', '1.3'],
            ['2022arXiv220412715L', '2023NJPh...25a3009L', '1.3'],
            ['2022arXiv220503149P', '2023PhRvC.107a4910P', '1.3'],
            ['2022arXiv220508471N', '2023E&ES.1136a2018N', '1.3'],
            ['2022arXiv220602637S', '2023NJPh...25a3015S', '1.3'],
            ['2022arXiv220611916G', '2023PhRvB.107d1301G', '1.3'],
            ['2022arXiv220612105S', '2023PhRvA.107a2422S', '1.3'],
            ['2022arXiv220705646C', '2023Quant...7..902C', '1.3'],
            ['2022arXiv220709366B', '2023PhRvL.130d1901B', '1.3'],
            ['2022arXiv220809620C', '2023PhRvA.107a3307C', '1.3'],
            ['2022arXiv220814400A', '2023PhRvB.107c5424A', '1.3'],
            ['2022arXiv220905830T', '2023PhRvB.107c5125T', '1.3'],
            ['2022arXiv221015213I', '2023PhRvD.107a6011I', '1.3'],
            ['2022arXiv221100521S', '2023PhRvM...7a4003S', '1.3'],
            ['2022arXiv221104744P', '2023PhRvA.107a2812P', '1.3'],
            ['2022arXiv221107207G', '2023PhRvL.130d3602G', '1.3'],
            ['2022arXiv221107754C', '2023JHEP...01..071C', '1.3'],
            ['2022arXiv221108072G', '2023PhRvB.107b4416G', '1.3'],
            ['2022arXiv221112960L', '2023PhRvD.107a3006L', '1.3'],
            ['2023arXiv230109795G', '2023Symm...15..259G', '1.3'],
            ['2023arXiv230109798L', '2023PhRvE.107a5105L', '1.3'],
            ['2021arXiv210607251P', '2021PhDT........26P', '1.3'],
            ['2021arXiv210607251P', '2021PhDT........26P', '1.3'],
            ['2023arXiv230110072K', '2021OExpr..2923736K', '1.3'],
            ['2021arXiv210607251P', '2020PhDT........36P', '-1']
        ]

        with mock.patch('requests.get', side_effect=return_values):
            results = self.match_metadata.ORACLE_UTIL.read_google_sheet(match_w_pub_filename)
            self.assertEqual(results, expected)

        # test when matching with pub
        match_w_eprint_filename = os.path.dirname(__file__) + '/stubdata/' + '2023-01-24.compare_pub.csv.xlsx'
        expected = [
            ['2023arXiv230108396S', '2023JPhCo...7a5001S', '1.3'],
            ['2022arXiv220911954M', '2022ConPh..63...34M', '1.3'],
            ['2022arXiv220600058K', '2023ITAP...71..650K', '1.3'],
            ['2022arXiv221007569T', '2023JPSJ...92b3601T', '1.3'],
            ['2019arXiv191101730S', '2020Quant...4..240S', '1.3'],
            ['2019arXiv191110999D', '2022AIHPC..39.1485D', '1.3'],
            ['2020arXiv200909163Z', '2022ITSP...70.6272Z', '1.3'],
            ['2021arXiv211104351I', '2022Quant...6..718I', '-1'],
            ['2022arXiv220306611J', '2022Quant...6..669J', '1.3'],
            ['2020arXiv201206687J', '2022Quant...6..669J', '-1']
        ]
        with mock.patch('requests.get', side_effect=return_values):
            results = self.match_metadata.ORACLE_UTIL.read_google_sheet(match_w_eprint_filename)
            self.assertEqual(results, expected)

    def test_make_params(self):
        """ test sending raw data and getting structure to be send to oracle to get added in """

        # setup returned values from oracle source-score function
        results = [{'confidence': 1.3}, {'confidence': -1}]
        return_values = []
        for result in results:
            return_values.append(self.create_response(result))

        match_w_pub_filename = os.path.dirname(__file__) + '/stubdata/' + '2023-01-25.compare_eprint.csv.xlsx'
        expected = [
            {'source_bibcode': '2021arXiv210913594W', 'matched_bibcode': '2023Quant...7..900W', 'confidence': '1.3'},
            {'source_bibcode': '2021arXiv211102596P', 'matched_bibcode': '2023Quant...7..898P', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv220400632S', 'matched_bibcode': '2023PhRvL.130d3601S', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv220405794W', 'matched_bibcode': '2023Quant...7..903W', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv220412715L', 'matched_bibcode': '2023NJPh...25a3009L', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv220503149P', 'matched_bibcode': '2023PhRvC.107a4910P', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv220508471N', 'matched_bibcode': '2023E&ES.1136a2018N', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv220602637S', 'matched_bibcode': '2023NJPh...25a3015S', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv220611916G', 'matched_bibcode': '2023PhRvB.107d1301G', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv220612105S', 'matched_bibcode': '2023PhRvA.107a2422S', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv220705646C', 'matched_bibcode': '2023Quant...7..902C', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv220709366B', 'matched_bibcode': '2023PhRvL.130d1901B', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv220809620C', 'matched_bibcode': '2023PhRvA.107a3307C', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv220814400A', 'matched_bibcode': '2023PhRvB.107c5424A', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv220905830T', 'matched_bibcode': '2023PhRvB.107c5125T', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv221015213I', 'matched_bibcode': '2023PhRvD.107a6011I', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv221100521S', 'matched_bibcode': '2023PhRvM...7a4003S', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv221104744P', 'matched_bibcode': '2023PhRvA.107a2812P', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv221107207G', 'matched_bibcode': '2023PhRvL.130d3602G', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv221107754C', 'matched_bibcode': '2023JHEP...01..071C', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv221108072G', 'matched_bibcode': '2023PhRvB.107b4416G', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv221112960L', 'matched_bibcode': '2023PhRvD.107a3006L', 'confidence': '1.3'},
            {'source_bibcode': '2023arXiv230109795G', 'matched_bibcode': '2023Symm...15..259G', 'confidence': '1.3'},
            {'source_bibcode': '2023arXiv230109798L', 'matched_bibcode': '2023PhRvE.107a5105L', 'confidence': '1.3'},
            {'source_bibcode': '2021arXiv210607251P', 'matched_bibcode': '2021PhDT........26P', 'confidence': '1.3'},
            {'source_bibcode': '2021arXiv210607251P', 'matched_bibcode': '2021PhDT........26P', 'confidence': '1.3'},
            {'source_bibcode': '2023arXiv230110072K', 'matched_bibcode': '2021OExpr..2923736K', 'confidence': '1.3'},
            {'source_bibcode': '2021arXiv210607251P', 'matched_bibcode': '2020PhDT........36P', 'confidence': '-1'}
        ]
        with mock.patch('requests.get', side_effect=return_values):
            results = self.match_metadata.ORACLE_UTIL.make_params(self.match_metadata.ORACLE_UTIL.read_google_sheet(match_w_pub_filename))
            self.assertEqual(results, expected)

        match_w_eprint_filename = os.path.dirname(__file__) + '/stubdata/' + '2023-01-24.compare_pub.csv.xlsx'
        expected = [
            {'source_bibcode': '2023arXiv230108396S', 'matched_bibcode': '2023JPhCo...7a5001S', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv220911954M', 'matched_bibcode': '2022ConPh..63...34M', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv220600058K', 'matched_bibcode': '2023ITAP...71..650K', 'confidence': '1.3'},
            {'source_bibcode': '2022arXiv221007569T', 'matched_bibcode': '2023JPSJ...92b3601T', 'confidence': '1.3'},
            {'source_bibcode': '2019arXiv191101730S', 'matched_bibcode': '2020Quant...4..240S', 'confidence': '1.3'},
            {'source_bibcode': '2019arXiv191110999D', 'matched_bibcode': '2022AIHPC..39.1485D', 'confidence': '1.3'},
            {'source_bibcode': '2020arXiv200909163Z', 'matched_bibcode': '2022ITSP...70.6272Z', 'confidence': '1.3'},
            {'source_bibcode': '2021arXiv211104351I', 'matched_bibcode': '2022Quant...6..718I', 'confidence': '-1'},
            {'source_bibcode': '2022arXiv220306611J', 'matched_bibcode': '2022Quant...6..669J', 'confidence': '1.3'},
            {'source_bibcode': '2020arXiv201206687J', 'matched_bibcode': '2022Quant...6..669J', 'confidence': '-1'}
        ]
        with mock.patch('requests.get', side_effect=return_values):
            results = self.match_metadata.ORACLE_UTIL.make_params(self.match_metadata.ORACLE_UTIL.read_google_sheet(match_w_eprint_filename))
            self.assertEqual(results, expected)

    def test_update_db_curated_matches(self):
        """ test add_to_db function of OracleUtil """

        # test when data is added in
        with mock.patch('requests.put') as oracle_util:
            oracle_util.return_value = mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.text = json.dumps({"status": "updated db with new data successfully"})

            match_w_pub_filename = os.path.dirname(__file__) + '/stubdata/' + '2023-01-25.compare_eprint.csv.xlsx'
            status = self.match_metadata.ORACLE_UTIL.update_db_curated_matches(match_w_pub_filename)
            self.assertEqual(status, 'Added 28 records to database.')

        # test when data is failed to get added in
        with mock.patch('requests.put') as oracle_util:
            oracle_util.return_value = mock_response = mock.Mock()
            mock_response.status_code = 400
            mock_response.text = json.dumps({'error': 'no data received'})

            match_w_eprint_filename = os.path.dirname(__file__) + '/stubdata/' + '2023-01-24.compare_pub.csv.xlsx'
            status = self.match_metadata.ORACLE_UTIL.update_db_curated_matches(match_w_eprint_filename)
            self.assertEqual(status, 'Stopped...')

    def test_get_matches_1(self):
        """ test when everything goes right and there is only one match """

        metadata = {
            'bibcode': '2018arXiv180101021F',
            'title': 'The Unified Astronomy Thesaurus: Semantic Metadata for Astronomy and\n  Astrophysics',
            'authors': 'Frey, Katie; Accomazzi, Alberto',
            'pubdate': '2018-01-03',
            'abstract': "Several different controlled vocabularies have been developed and used by the\nastronomical community, each designed to serve a specific need and a specific\ngroup. The Unified Astronomy Thesaurus (UAT) attempts to provide a highly\nstructured controlled vocabulary that will be relevant and useful across the\nentire discipline, regardless of content or platform. As two major use cases\nfor the UAT include classifying articles and data, we examine the UAT in\ncomparison with the Astronomical Subject Keywords used by major publications\nand the JWST Science Keywords used by STScI's Astronomer's Proposal Tool.",
            'keywords': 'Astrophysics - Instrumentation and Methods for Astrophysics; Computer Science - Digital Libraries',
            'properties': {'HTML': 'http://arxiv.org/abs/1801.01021', 'DOI': 'doi:10.3847/1538-4365/aab760'},
            'comments': ['Submitted to the Astrophysical Journal Supplements, 10 pages, 3\n  tables', 'doi:10.3847/1538-4365/aab760'],
            'publication': 'eprint arXiv:1801.01021', 'doi': '10.3847/1538-4365/aab760'
        }

        returned_value = {
            'query': 'identifier:(\'10.3847/1538-4365/aab760\') doctype:(article OR inproceedings OR inbook)',
            'match': [{'source_bibcode': '2018arXiv180101021F',
                       'matched_bibcode': '2018ApJS..236...24F',
                       'confidence': 0.9957643,
                       'matched': 1,
                       'scores': {'abstract': 0.98, 'title': 0.98, 'author': 1, 'year': 1, 'doi': 1}
            }]
        }

        expected_value = [{
            'source_bibcode': '2018arXiv180101021F',
            'matched_bibcode': '2018ApJS..236...24F',
            'label': 'Match',
            'confidence': 0.9957643,
            'score': {'abstract': 0.98, 'title': 0.98, 'author': 1, 'year': 1, 'doi': 1},
            'comment': ''
        }]

        with mock.patch('requests.post') as mock_oracle_util:
            mock_oracle_util.return_value = mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.text = json.dumps(returned_value)

            results = self.match_metadata.ORACLE_UTIL.get_matches(metadata, doctype='eprint')
            self.assertEqual(results, expected_value)

    def test_get_matches_2(self):
        """ what if oracle was not responsive """

        metadata = {
            'bibcode': '2018arXiv180101021F',
            'title': 'The Unified Astronomy Thesaurus: Semantic Metadata for Astronomy and\n  Astrophysics',
            'authors': 'Frey, Katie; Accomazzi, Alberto',
            'pubdate': '2018-01-03',
            'abstract': "Several different controlled vocabularies have been developed and used by the\nastronomical community, each designed to serve a specific need and a specific\ngroup. The Unified Astronomy Thesaurus (UAT) attempts to provide a highly\nstructured controlled vocabulary that will be relevant and useful across the\nentire discipline, regardless of content or platform. As two major use cases\nfor the UAT include classifying articles and data, we examine the UAT in\ncomparison with the Astronomical Subject Keywords used by major publications\nand the JWST Science Keywords used by STScI's Astronomer's Proposal Tool.",
            'keywords': 'Astrophysics - Instrumentation and Methods for Astrophysics; Computer Science - Digital Libraries',
            'properties': {'HTML': 'http://arxiv.org/abs/1801.01021', 'DOI': 'doi:10.3847/1538-4365/aab760'},
            'comments': ['Submitted to the Astrophysical Journal Supplements, 10 pages, 3\n  tables', 'doi:10.3847/1538-4365/aab760'],
            'publication': 'eprint arXiv:1801.01021', 'doi': '10.3847/1538-4365/aab760'
        }

        returned_value = {
            'query': 'identifier:(\'10.3847/1538-4365/aab760\') doctype:(article OR inproceedings OR inbook)',
            'match': [{'source_bibcode': '2018arXiv180101021F',
                       'matched_bibcode': '2018ApJS..236...24F',
                       'confidence': 0.9957643,
                       'matched': 1,
                       'scores': {'abstract': 0.98, 'title': 0.98, 'author': 1, 'year': 1, 'doi': 1}
            }]
        }

        expected_value = [{
            'source_bibcode': '2018arXiv180101021F',
            'comment': 'Oracle service failure.',
            'status_flaw': 'got 502 for the last failed attempt -- shall be added to rerun list.'
        }]

        with mock.patch('requests.post') as mock_oracle_util:
            mock_oracle_util.return_value = mock_response = mock.Mock()
            mock_response.status_code = 502
            mock_response.text = json.dumps(returned_value)

            results = self.match_metadata.ORACLE_UTIL.get_matches(metadata, doctype='eprint')
            self.assertEqual(results, expected_value)

    def test_get_matches_3(self):
        """ if got an error from oracle """

        metadata = {
            'bibcode': '2018arXiv180101021F',
            'title': 'The Unified Astronomy Thesaurus: Semantic Metadata for Astronomy and\n  Astrophysics',
            'authors': 'Frey, Katie; Accomazzi, Alberto',
            'pubdate': '2018-01-03',
            'abstract': "Several different controlled vocabularies have been developed and used by the\nastronomical community, each designed to serve a specific need and a specific\ngroup. The Unified Astronomy Thesaurus (UAT) attempts to provide a highly\nstructured controlled vocabulary that will be relevant and useful across the\nentire discipline, regardless of content or platform. As two major use cases\nfor the UAT include classifying articles and data, we examine the UAT in\ncomparison with the Astronomical Subject Keywords used by major publications\nand the JWST Science Keywords used by STScI's Astronomer's Proposal Tool.",
            'keywords': 'Astrophysics - Instrumentation and Methods for Astrophysics; Computer Science - Digital Libraries',
            'properties': {'HTML': 'http://arxiv.org/abs/1801.01021', 'DOI': 'doi:10.3847/1538-4365/aab760'},
            'comments': ['Submitted to the Astrophysical Journal Supplements, 10 pages, 3\n  tables', 'doi:10.3847/1538-4365/aab760'],
            'publication': 'eprint arXiv:1801.01021', 'doi': '10.3847/1538-4365/aab760'
        }

        returned_value = {
            'query': 'identifier:(\'10.3847/1538-4365/aab760\') doctype:(article OR inproceedings OR inbook)',
            'match': [{'source_bibcode': '2018arXiv180101021F',
                       'matched_bibcode': '2018ApJS..236...24F',
                       'confidence': 0.9957643,
                       'matched': 1,
                       'scores': {'abstract': 0.98, 'title': 0.98, 'author': 1, 'year': 1, 'doi': 1}
            }]
        }

        expected_value = [{
            'source_bibcode': '2018arXiv180101021F',
            'comment': 'Oracle service failure.',
            'status_flaw': 'got 400 for the last failed attempt -- shall be added to rerun list.'
        }]
        with mock.patch('requests.post') as mock_oracle_util:
            mock_oracle_util.return_value = mock_response = mock.Mock()
            mock_response.status_code = 400
            mock_response.text = json.dumps(returned_value)

            results = self.match_metadata.ORACLE_UTIL.get_matches(metadata, doctype=None)
            self.assertEqual(results, expected_value)

    def test_get_matches_4(self):
        """ test when metadata is incomplete (ie, missing author) getting an error """

        metadata = {
            'bibcode': '2018arXiv180101021F',
            'title': 'The Unified Astronomy Thesaurus: Semantic Metadata for Astronomy and\n  Astrophysics',
            'pubdate': '2018-01-03',
            'abstract': "Several different controlled vocabularies have been developed and used by the\nastronomical community, each designed to serve a specific need and a specific\ngroup. The Unified Astronomy Thesaurus (UAT) attempts to provide a highly\nstructured controlled vocabulary that will be relevant and useful across the\nentire discipline, regardless of content or platform. As two major use cases\nfor the UAT include classifying articles and data, we examine the UAT in\ncomparison with the Astronomical Subject Keywords used by major publications\nand the JWST Science Keywords used by STScI's Astronomer's Proposal Tool.",
            'keywords': 'Astrophysics - Instrumentation and Methods for Astrophysics; Computer Science - Digital Libraries',
            'properties': {'HTML': 'http://arxiv.org/abs/1801.01021', 'DOI': 'doi:10.3847/1538-4365/aab760'},
            'comments': ['Submitted to the Astrophysical Journal Supplements, 10 pages, 3\n  tables', 'doi:10.3847/1538-4365/aab760'],
            'publication': 'eprint arXiv:1801.01021', 'doi': '10.3847/1538-4365/aab760'
        }

        expected_value = [{
            'source_bibcode': '2018arXiv180101021F',
            'comment': "Exception: KeyError, 'authors' missing.",
            'status_flaw': 'did not send request to oracle service'}]
        results = self.match_metadata.ORACLE_UTIL.get_matches(metadata, doctype='eprint')
        self.assertEqual(results, expected_value)

    def test_get_matches_5(self):
        """ when multiple records are matched """

        metadata = {
            'bibcode': '2002cond.mat..3492S',
            'title': 'Dynamical susceptibilities in strong coupling approach: General scheme\n  and Falikov-Kimball model',
            'authors': 'Shvaika, A. M.',
            'pubdate': '2002-03-24',
            'abstract': 'A general scheme to calculate dynamical susceptibilities of strongly\ncorrelated electron systems within the dynamical mean field theory is\ndeveloped. Approach is based on an expansion over electron hopping around the\natomic limit (within the diagrammatic technique for site operators: projection\nand Hubbard ones) in infinite dimensions. As an example, the Falicov-Kimball\nand simplified pseudospin-electron models are considered for which an\nanalytical expressions for dynamical susceptibilities are obtained.',
            'keywords': 'Condensed Matter - Strongly Correlated Electrons',
            'properties': {'HTML': 'http://arxiv.org/abs/cond-mat/0203492', 'DOI': 'doi:10.30970/jps.05.349'},
            'comments': ['6 pages, lecture given at the 2nd International Pamporovo Workshop on\n  Cooperative Phenomena in Condensed Matter (28th July - 7th August 2001,\n  Pamporovo, Bulgaria)', 'J. Phys. Stud. 5, 349 (2001)', 'doi:10.30970/jps.05.349'],
            'publication': 'eprint arXiv:cond-mat/0203492', 'doi': '10.30970/jps.05.349'}

        returned_value = {
            "query": "topn(10, similar(\"A general scheme to calculate dynamical susceptibilities of strongly correlated electron systems within the dynamical mean field theory is developed. Approach is based on an expansion over electron hopping around the atomic limit (within the diagrammatic technique for site operators: projection and Hubbard ones) in infinite dimensions. As an example, the Falicov-Kimball and simplified pseudospin-electron models are considered for which an analytical expressions for dynamical susceptibilities are obtained.\", input abstract, 20, 1, 1)) doctype:(article OR inproceedings OR inbook)",
            "comment": "No result from solr with DOI ['10.30970/jps.05.349'].",
            "match": [
                {
                    "source_bibcode": "2002cond.mat..3492S",
                    "matched_bibcode": "2001JPhSt...5..349S",
                    "confidence": 0.9957017,
                    "matched": 1,
                    "scores": {"abstract": 1.0, "title": 0.97, "author": 1, "year": 1, "doi": 1}
                }, {
                    "source_bibcode": "2002cond.mat..3492S",
                    "matched_bibcode": "2000PhyC..341..177S",
                    "confidence": 0.9804561,
                    "matched": 1,
                    "scores": {"abstract": 1.0, "title": 0.96, "author": 1, "year": 0.75}
                }
            ]
        }

        expected_value = [
            {
                'source_bibcode': '2002cond.mat..3492S',
                'confidence': 0.9957017,
                'label': 'Match',
                'scores': "{'abstract': 1.0, 'title': 0.97, 'author': 1, 'year': 1, 'doi': 1}",
                'matched_bibcode': '2001JPhSt...5..349S',
                'comment': "No result from solr with DOI ['10.30970/jps.05.349'].Multi match: 1 of 2."
            }, {
                'source_bibcode': '2002cond.mat..3492S',
                'confidence': 0.9804561,
                'label': 'Match',
                'scores': "{'abstract': 1.0, 'title': 0.96, 'author': 1, 'year': 0.75}",
                'matched_bibcode': '2000PhyC..341..177S',
                'comment': "No result from solr with DOI ['10.30970/jps.05.349'].Multi match: 2 of 2."
            }
        ]

        with mock.patch('requests.post') as mock_oracle_util:
            mock_oracle_util.return_value = mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.text = json.dumps(returned_value)

            results = self.match_metadata.ORACLE_UTIL.get_matches(metadata, doctype='eprint')
            self.assertEqual(results, expected_value)

    def test_get_matches_6(self):
        """ test when no matches are found """

        metadata = {
            'bibcode': '2017arXiv170100200T',
            'title': 'Post-Lie algebra structures on the Witt algebra',
            'authors': 'Tang, Xiaomin', 'pubdate': '2017-01-01',
            'abstract': 'In this paper, we characterize the graded post-Lie algebra structures and a\nclass of shifting post-Lie algebra structures on the Witt algebra. We obtain\nsome new Lie algebras and give a class of their modules. As an application, the\nhomogeneous Rota-Baxter operators and a class of non-homogeneous Rota-Baxter\noperators of weight $1$ on the Witt algebra are studied.',
            'keywords': 'Mathematics - Rings and Algebras; 17A30, 17A42, 17B60, 18D50',
            'properties': {'HTML': 'http://arxiv.org/abs/1701.00200'},
            'comments': ['24 pages'],
            'publication': 'eprint arXiv:1701.00200'}

        returned_value = {
            "query": "topn(10, similar(\"algebra structures on the Witt algebra\", input title, 4, 1, 1)) doctype:(article OR inproceedings OR inbook)",
            "comment": "No matches with Abstract, trying Title.",
            "no match": "no document was found in solr matching the request."
        }

        expected_value = [{
            'source_bibcode': '2017arXiv170100200T',
            'matched_bibcode': '...................',
            'label': 'Not Match',
            'confidence': 0,
            'score': '',
            'comment': 'No matches with Abstract, trying Title. No document was found in solr matching the request.'
        }]
        with mock.patch('requests.post') as mock_oracle_util:
            mock_oracle_util.return_value = mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.text = json.dumps(returned_value)

            results = self.match_metadata.ORACLE_UTIL.get_matches(metadata, doctype='eprint')
            self.assertEqual(results, expected_value)

    def test_get_source_score_list(self):
        """ """
        # test when everything goes right
        returned_value = {
            'results': [
                {'source': 'ADS', 'confidence': 1.3},
                {'source': 'incorrect', 'confidence': -1.0},
                {'source': 'author', 'confidence': 1.2},
                {'source': 'publisher', 'confidence': 1.1},
                {'source': 'SPIRES', 'confidence': 1.05}
            ]
        }

        expected_value = [
                {'source': 'ADS', 'confidence': 1.3},
                {'source': 'incorrect', 'confidence': -1.0},
                {'source': 'author', 'confidence': 1.2},
                {'source': 'publisher', 'confidence': 1.1},
                {'source': 'SPIRES', 'confidence': 1.05}
        ]

        with mock.patch('requests.get') as mock_oracle_util:
            mock_oracle_util.return_value = mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.text = json.dumps(returned_value)

            results = self.match_metadata.ORACLE_UTIL.get_source_score_list()
            self.assertEqual(results, expected_value)

        # test when oracle does not return the list
        with mock.patch('requests.get') as mock_oracle_util:
            mock_oracle_util.return_value = mock_response = mock.Mock()
            mock_response.status_code = 400

            results = self.match_metadata.ORACLE_UTIL.get_source_score_list()
            self.assertEqual(results, [])

        # test when an exception happen while sending request to oracle
        with mock.patch('requests.get') as mock_oracle_util:
            mock_oracle_util.side_effect = Exception(mock.Mock(status=404), 'not found')
            results = self.match_metadata.ORACLE_UTIL.get_source_score_list()
            self.assertEqual(results, [])

    def test_update_db_sourced_matches(self):
        """ """
        # test when everything goes right
        with mock.patch('requests.get') as mock_oracle_util_source_score:
            mock_oracle_util_source_score.return_value = mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.text = json.dumps({'confidence': 1.3})

            with mock.patch('requests.put') as oracle_util_add_to_db:
                oracle_util_add_to_db.return_value = mock_response = mock.Mock()
                mock_response.status_code = 200
                mock_response.text = json.dumps({"status": "updated db with new data successfully"})

                status = self.match_metadata.ORACLE_UTIL.update_db_sourced_matches(os.path.dirname(__file__) + "/stubdata/matched_bibcodes.txt", "ADS")
                self.assertEqual(status, 'Added 6 records to database.')

        # test when oracle does not return a confidence value
        with mock.patch('requests.get') as mock_oracle_util:
            mock_oracle_util.return_value = mock_response = mock.Mock()
            mock_response.status_code = 400

            status = self.match_metadata.ORACLE_UTIL.update_db_sourced_matches(os.path.dirname(__file__) + "/stubdata/matched_bibcodes.txt", "ADS")
            self.assertEqual(status, 'Unable to get confidence for source ADS from oracle.')

        # test when an exception happen while sending request to oracle
        with mock.patch('requests.get') as mock_oracle_util:
            mock_oracle_util.side_effect = Exception(mock.Mock(status=404), 'not found')
            status = self.match_metadata.ORACLE_UTIL.update_db_sourced_matches("a file", "source")
            self.assertEqual(status, 'Unable to get confidence for source source from oracle.')

    def test_query(self):
        """ """
        tmp_output_filename = os.path.dirname(__file__) + '/stubdata/query_output.txt'

        results = [
            {"params": {"start": 0, "days": 1, "rows": 2, "date_cutoff": "2023-05-05 12:00:00.123456+00:00"},
             "results": [["2015arXiv150504001F", "2015PhRvD..92c3003F", 1.3],
                         ["2019arXiv190610914P", "2020JPCM...32c5601P", 1.3]]},
            {"params": {"start": 0, "days": 1, "rows": 2, "date_cutoff": "2023-05-05 12:00:00.234567+00:00"},
             "results": [["2020arXiv200608648C", "2021JHEP...04..033C", 1.3],
                         ["2020arXiv200903580T", "2021JSP...182...16T", 1.3]]},
            {"params": {"start": 0, "days": 1, "rows": 2, "date_cutoff": "2023-05-05 12:00:00.345678+00:00"},
             "results": [["2020arXiv201001642A", "2021PhRvB.104s5415A", 1.3],
                         ["2020arXiv200905968B", "2022CMaPh.390..933B", 1.3]]},
            {"params": {"start": 0, "days": 1, "rows": 0, "date_cutoff": "2023-05-05 12:00:00.456789+00:00"},
             "results": []},
        ]

        return_values = []
        expected_lines = []
        for result in results:
            return_values.append(self.create_response(result))
            for match in result.get('results'):
                expected_lines.append('\t'.join([str(elem) for elem in match]))

        with mock.patch('requests.post', side_effect=return_values):
            status = self.match_metadata.ORACLE_UTIL.query(tmp_output_filename)
            self.assertEqual(status, 'Got 6 records from db.')
            with open(tmp_output_filename, "r") as f:
                actual_lines = f.readlines()
                self.assertEqual(len(actual_lines), len(expected_lines))
                for actual_line, expected_line in zip(actual_lines, expected_lines):
                    self.assertEqual(actual_line[:-1], expected_line)

        # remove temp files
        os.remove(tmp_output_filename)

    def test_cleanup(self):
        """ """
        with mock.patch('requests.get') as mock_oracle_util:
            mock_oracle_util.return_value = mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.text = '{"details": "This is one result."}'
            result = self.match_metadata.ORACLE_UTIL.cleanup_db()
            self.assertEqual(result, 'This is one result.')
            mock_response.status_code = 403
            mock_response.text = '{"details": "This is another result."}'
            result = self.match_metadata.ORACLE_UTIL.cleanup_db()
            self.assertEqual(result, 'This is another result.')
            mock_response.status_code = 502
            mock_response.text = '{"details": "This is yet another result."}'
            result = self.match_metadata.ORACLE_UTIL.cleanup_db()
            self.assertEqual(result, 'This is yet another result.')


if __name__ == '__main__':
    unittest.main()

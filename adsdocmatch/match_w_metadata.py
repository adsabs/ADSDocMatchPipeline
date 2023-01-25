import os
from adsputils import setup_logging
from pub_parser import get_pub_metadata
from from_oracle import get_matches
from pyingest.parsers.arxiv import ArxivParser
import time
import re
import csv

logger = setup_logging('docmatch_log_match_metadata')


class MatchMetadata():

    MUST_MATCH = ['Astrophysics', 'Physics']
    DOCTYPE_THESIS = ['phdthesis', 'mastersthesis']

    re_admin_notes = re.compile(r'arXiv admin note: (.*)$')
    re_doi = re.compile(r'doi:\s*(10\.\d{4,9}/\S+\w)', re.IGNORECASE)
    re_doctype_thesis = re.compile(r'\b(thesis)\b', re.IGNORECASE)
    re_doctype_errata = re.compile(r'(^errat(a|um))\b', re.IGNORECASE)
    re_doctype_bookreview = re.compile(r'\bbook[s|\s|\-]*review[s|ed]*', re.IGNORECASE)

    ARXIV_PARSER = ArxivParser()

    def get_filenames(self, filename):
        """
        read input file and return list of arXiv metadata full filenames

        :param filename:
        :return:
        """
        filenames = []
        try:
            with open(filename, 'r') as fp:
                for filename in fp.readlines():
                    filenames.append(filename.rstrip('\r\n'))
        except Exception as e:
            logger.error('Unable to open/read input file', e)
        return filenames

    def format_results(self, results, separator):
        """

        :param results:
        :param separator:
        :return:
        """
        if results.get('matched_bibcode', None):
            match = separator.join([str(results.get(field, '')) for field in ['source_bibcode', 'matched_bibcode', 'label', 'confidence', 'score', 'comment']])
            if len(results.get('inspection', [])) > 1:
                return match, results['inspection']
            # single match
            return match, None
        # when error, return status_code
        return '%s status_code=%s' % (results.get('comment', ''), results.get('status_code', '')), None

    def write_results(self, result_filename, a_match, inspection_hits):
        """
        for inspection list, also include matches, first write the match, and then if there are inspection_hits wrote those

        :param result_filename:
        :param a_match:
        :param inspection_hits:
        :return:
        """
        csv_file = result_filename + '.csv'
        if os.path.exists(csv_file):
            fp = open(csv_file, 'a')
        else:
            fp = open(csv_file, 'w')
            # new file, write header line
            fp.write(
                'source bibcode (link),verified bibcode,matched bibcode (link),label,confidence,matched scores,comment\n')

        hyperlink_format = '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/%s/abstract"",""%s"")"'
        double_quote = '"%s"'

        # include match only if inpsection_hits is empty
        # otherwise write inspection_hits
        if not inspection_hits and a_match:
            a_match_parts = a_match.split('\t')
            if len(a_match_parts) == 6:
                source_bibcode = a_match_parts[0]
                matched_bibcode = a_match_parts[1]
                fp.write('%s,,%s,%s,%s,%s,%s\n' % (
                    hyperlink_format % (source_bibcode, source_bibcode),
                    hyperlink_format % (matched_bibcode, matched_bibcode),
                    a_match_parts[2],
                    a_match_parts[3],
                    double_quote % a_match_parts[4],
                    double_quote % a_match_parts[5],
                ))
            else:
                # it is an error write it out
                fp.write("%s\n" % a_match)
        elif inspection_hits:
            for item in inspection_hits:
                source_bibcode = item['source_bibcode']
                matched_bibcode = item['matched_bibcode']
                # source bibcode, empty column reserved for curators adding verified bibcode, and the score
                fp.write('%s,,%s,%s,%s,%s,%s\n' % (
                    hyperlink_format % (source_bibcode, source_bibcode),
                    hyperlink_format % (matched_bibcode, matched_bibcode),
                    item['label'],
                    item['confidence'],
                    double_quote % item['scores'],
                    double_quote % item['comment'],
                ))
        fp.close()

    def match_to_arXiv(self, filename):
        """
        read and parse arXiv metadata file
        return list of bibcodes and scores for the matches in decreasing order
    
        :param filename:
        :return:
        """
        try:
            with open(filename, 'rb') as pub_fp:
                return get_matches(get_pub_metadata(pub_fp.read()), 'article')
        except Exception as e:
            logger.error('Exception: %s'%e)
            return
    
    def single_match_to_arXiv(self, pub_filename):
        """
        when user submits a single pub metadata file for matching
    
        :param pub_filename:
        :return:
        """
        results = self.match_to_arXiv(pub_filename)
        if results:
            return self.format_results(results, '\t')
        return None,None
    
    def single_match_to_arxiv_output(self, pub_filename):
        """
    
        :param pub_filename:
        :return:
        """
        a_match, for_inspection = self, self.single_match_to_arXiv(pub_filename)
        print(a_match)
        if for_inspection:
            print(for_inspection)
    
    def batch_match_to_arXiv(self, filename, result_filename):
        """
    
        :param filename:
        :param result_filename:
        :return:
        """
        filenames = self.get_filenames(filename)
        if len(filenames) > 0:
            if result_filename:
                # one file at a time, parse and score, and then write the result to the file
                for pub_filename in filenames:
                    a_match, for_inspection = self.single_match_to_arXiv(pub_filename)
                    self.write_results(result_filename, a_match, for_inspection)
                    # wait a second before the next attempt
                    time.sleep(1)
            else:
                for pub_filename in filenames:
                    self.single_match_to_arxiv_output(pub_filename)

    def match_to_pub(self, filename):
        """
        read and parse arXiv metadata file
        return list of bibcodes and scores for the matches in decreasing order
    
        :param filename:
        :return:
        """
        try:
            with open(filename, 'rb') as arxiv_fp:
                metadata = self.ARXIV_PARSER.parse(arxiv_fp)
                comments = ' '.join(metadata.get('comments', []))
                # extract doi out of comments if there are any
                match = self.re_doi.search(comments)
                if match:
                    metadata['doi'] = match.group(1)
                else:
                    doi = metadata.get('properties', {}).get('DOI', None)
                    if doi:
                        metadata['doi'] = doi.replace('doi:', '')
                match_doctype = None
                title = metadata.get('title')
                # check title for erratum
                match = self.re_doctype_errata.search(title)
                if match:
                    match_doctype = ['erratum']
                else:
                    match = self.re_doctype_bookreview.search(title)
                    if match:
                        match_doctype = ['bookreview']
                    else:
                        # check both comments and title for thesis
                        match = self.re_doctype_thesis.search("%s %s"%(comments, title))
                        if match:
                            match_doctype = ['phdthesis', 'mastersthesis']
                mustmatch = any(category in metadata.get('keywords', '') for category in self.MUST_MATCH)
                return self.add_metadata_comment(get_matches(metadata, 'eprint', mustmatch, match_doctype), comments)
        except Exception as e:
            logger.error('Exception: %s'%e)
            return
    
    def single_match_to_pub(self, arXiv_filename):
        """
        when user submits a single arxiv metadata file for matching
    
        :param arxiv_filename:
        :return:
        """
        results = self, self.match_to_pub(arXiv_filename)
        if results:
            return self.format_results(results, '\t')
        return None,None
    
    def single_match_to_pub_output(self, arXiv_filename):
        """
    
        :param arXiv_filename:
        :return:
        """
        a_match, for_inspection = self.single_match_to_pub(arXiv_filename)
        print('Match? -->', a_match)
        if for_inspection:
            print('Needs inspection -->', for_inspection)

    def batch_match_to_pub(self, filename, result_filename):
        """
    
        :param filename:
        :param result_filename:
        :return:
        """
        filenames = self.get_filenames(filename)
        if len(filenames) > 0:
            if result_filename:
                # one file at a time, parse and score, and then write the result to the file
                for arXiv_filename in filenames:
                    a_match, for_inspection = self.single_match_to_pub(arXiv_filename)
                    self.write_results(result_filename, a_match, for_inspection)
                    # wait a second before the next attempt
                    time.sleep(1)
            else:
                for arXiv_filename in filenames:
                    self.single_match_output(arXiv_filename)

    def add_metadata_comment(self, results, comments):
        """
    
        :param results:
        :param comments:
        :return:
        """
        match = self.re_admin_notes.search(comments)
        if match:
            admin_notes = match.group(1)
            results['comment'] = ('%s %s'%(results.get('comment', ''), admin_notes)).strip()
            for inspection in results.get('inspection', []):
                inspection['comment'] = ('%s %s'%(inspection.get('comment', ''), admin_notes)).strip()
        return results

    def read_classic_results(self, classic, source):
        """
    
        :param classic:
        :return:
        """
        results = {}
        with open(classic, 'r') as fp:
            for line in fp.readlines():
                if len(line) > 1:
                    columns = line[:-1].split('\t')
                    if source == 'eprint':
                        results[columns[0]] = columns[1]
                    elif source == 'pub':
                        results[columns[1]] = columns[0]
        return results
    
    def read_docmatch_results(self, filename):
        """
    
        :param filename:
        :return:
        """
        results = []
        with open(filename, 'r') as fp:
            reader = csv.reader(fp, delimiter=',')
            next(reader)
            for columns in reader:
                results.append(columns)
        return results

    def combine_classic_docmatch_results(self, classic_results, docmatch_results):
        """
    
        :param classic_results:
        :param docmatch_results:
        :return:
        """
        combined_results = []
        combined_results.append(['source bibcode (link)','classic bibcode (link)','curator comment','verified bibcode','matched bibcode (link)','comment','label','confidence','matched scores'])
    
        hyperlink_format = '"=HYPERLINK(""https://ui.adsabs.harvard.edu/abs/%s/abstract"",""%s"")"'
        for nowadays_result in docmatch_results:
            # if there was an error in the csv file, transfer it and move on
            if len(nowadays_result) == 1:
                combined_results.append(nowadays_result)
                continue
            # insert two columns: 'classic bibcode (link)','curator comment' between the source and matched bibcode columns
            classic_bibcode = classic_results.get(nowadays_result[0][-21:-2], '')
            classic_bibcode_link = hyperlink_format % (classic_bibcode, classic_bibcode) if classic_bibcode else ''
            # need to format the two linked columns again
            source_bibcode_link = '"%s"'%nowadays_result[0].replace('"','""')
            matched_bibcode_link = '"%s"'%nowadays_result[2].replace('"','""') if not nowadays_result[2][-21:-2].startswith('.') else ''
            combined_results.append([source_bibcode_link, classic_bibcode_link, '', '', matched_bibcode_link, '"%s"'%nowadays_result[6], nowadays_result[3], nowadays_result[4], '"%s"'%nowadays_result[5]])
        return combined_results
    
    def output_combined_results(self, combined_results, filename):
        """
    
        :param combined_results:
        :param filename:
        :return:
        """
        with open(filename, 'w') as fp:
            fp.write(','.join(combined_results[0]) + '\n')
            # error lines are one element that have no confidence column
            combined_results = sorted(combined_results[1:], key=lambda result: float(result[7]) if len(result) > 7 else -1)
            for combined_result in combined_results:
                # error lines are one element, include them
                if len(combined_result) == 1:
                    fp.write(','.join(combined_result) + '\n')
                # include only the lines with classic bibcode, or matched bibcode
                elif len(combined_result[1]) > 0 or len(combined_result[4]) > 0:
                    # if there is a classic match see if it agrees or disagrees with oracle
                    if len(combined_result[1]) > 0:
                        combined_result[2] = 'agree' if combined_result[1] == combined_result[4] else 'disagree'
                    # if there is a multi match and confidence is high
                    # or if there was no abstract for comparison and confidence is high
                    # mark it to be verified
                    elif (len(combined_result) >= 8 and float(combined_result[7]) >= 0.5 and
                              (('None' in combined_result[8]) or ('Multi match' in combined_result[5]))):
                        combined_result[2] = 'verify'
                    fp.write(','.join(combined_result)+'\n')

    def output_combine_classic_docmatch_results(self, source, classic_filename, docmatch_filename, output_filename):
        """

        :param source:
        :param classic_filename:
        :param docmatch_filename:
        :param output_filename:
        :return:
        """
        classic_results = self.read_classic_results(classic_filename, source)
        docmatch_results = self.read_docmatch_results(docmatch_filename)
        if classic_results and docmatch_results:
            combined_results = self.combine_classic_docmatch_results(classic_results, docmatch_results)
            if combined_results:
                self.output_combined_results(combined_results, output_filename)

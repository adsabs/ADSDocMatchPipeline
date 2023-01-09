import sys, os
import argparse
from adsputils import setup_logging
import pandas as pd
import numpy as np

class PandasParser(object):

    def __init__(self):
        pass


    def read_excel_file(self, input_filename):
        """
    
        :param input_filename: this can be a filename, file handle, or StringIO
        :return:
        """
        # Generate DataFrame from input excel file
        try:
            df = pd.read_excel(input_filename)
            dt = df[['source bibcode (link)', 'curator comment', 'verified bibcode', 'matched bibcode (link)']]
            cols = {'source bibcode (link)': 'source_bib',
                    'curator comment': 'curator_comment',
                    'verified bibcode': 'verified_bib',
                    'matched bibcode (link)': 'matched_bib'}
            dt = dt.rename(columns=cols)
    
            # Drop unneeded rows where curator comment is: null, 'agree', 'disagree', 'no action' or 'verify'
            array = [np.nan, 'agree', 'disagree', 'no action', 'verify']
            dt = dt.loc[~dt['curator_comment'].isin(array)]
    
            # Where verified bibcode is null, insert matched bibcode
            dt['verified_bib'] = dt['verified_bib'].fillna(dt['matched_bib'])
    
            # Set the db actions by given vocabulary (add, delete, or update)
            dt = dt.reset_index()
            for index, row in dt.iterrows():
    
                # If curator comment is not in vocabulary; print flag, and drop the row
                comments = ['update', 'add', 'delete']
                if row.curator_comment not in comments:
                    print('Error: Bad curator comment at', row.source_bib)
                    dt.drop(index, inplace=True)

                # Where curator comment is 'update', duplicate row and rewrite actions;
                #    Assigns delete/-1 for matched bibcode, add/1.1 for verified bibcode
                if row.curator_comment == 'update':
                    try:
                        dt = dt.replace(row.curator_comment, "1.1")
                        new_row = {'source_bib': row.source_bib,
                                   'curator_comment': '-1',
                                   'verified_bib': row.matched_bib,
                                   'matched_bib': row.matched_bib}
                        #dt = dt.append(new_row, ignore_index=True)
                        pd.concat(dt, new_row)
                    except Exception as err:
                        print("Error updating row %s\n\t%s" % (new_row, err))
    
                # Replace curator comments; 'add':'1.1' and 'delete':'-1'
                if row.curator_comment == 'add':
                    dt = dt.replace(row.curator_comment, "1.1")
                if row.curator_comment == 'delete':
                    dt = dt.replace(row.curator_comment, "-1")
    
            # Format columns (preprint \t publisher \t action) for txt file
            # since compare is arXiv matched against publisher, while pubcompare is publisher matched against arXiv
            if '.compare' in input_filename:
                results = dt[['source_bib', 'verified_bib', 'curator_comment']]
            elif '.pubcompare' in input_filename:
                results = dt[['verified_bib', 'source_bib', 'curator_comment']]
            else:
                results = []

            return results
        except Exception as err:
            raise ParserParseException(err)

    def write_output(self, results, output_filename):
        """
    
        :param results:
        :param input_filename:
        :param output_filename:
        :return:
        """
        try:
            # Output as txt file if there are db updates to send
            if len(results) > 0:
                to_txt = results.sort_values(by=['source_bib', 'curator_comment'])
                to_txt.to_csv(output_filename, index=False, header=False, sep='\t')
            return len(results)
        except Exception as err:
            raise ParserWriteException(Exception)
        else:
            return 0

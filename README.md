[![Build Status](https://travis-ci.org/adsabs/ADSDocMatchPipeline.svg)](https://travis-ci.org/adsabs/ADSDocMatchPipeline)
[![Coverage Status](https://coveralls.io/repos/adsabs/ADSDocMatchPipeline/badge.svg)](https://coveralls.io/r/adsabs/ADSDocMatchPipeline)

# ADS Doc Match Pipeline

ADSDocMatchPipeline centralizes the functionality in docmatch_scripts in a package with a single ``run.py``, similar to existing ADS backoffice pipelines.

## Automated matching of new content for curator review

### Match daily eprints (e.g. arXiv) to published records in Solr

This takes an input list of new eprints and attempts to match them to existing records in Solr.  The name of the input file is set in the config variable ``DOCMATCHPIPELINE_INPUT_FILENAME``

  ``python3 run.py -mp -p "/path/to/input/filename/"``

If docmatching is being run in parallel with the existing classic preprint matching process, the pipeline will then attempt to compare the two methods, and the comparison between them will be uploaded to the Google Drive folder set in the config variable ``GOOGLE_BASEDIR_ID`` with the filename ``DOCMATCHPIPELINE_EPRINT_COMBINED_FILENAME``, prefixed with the day's date.  If the classic script is not run, the results of docmatching alone will be uploaded with the filename set by ``DOCMATCHPIPELINE_EPRINT_RESULT_FILENAME``.

Note that the output file is a tab delimited text file, containing 6 columns, with no header line. The columns are source bibcode, matched bibcode, if any, label (ie, whether the system thinks it is a Match or Not Match), confidence score, similarity scores (ie, similarity scores between the source and matched bibcodes for abstract/title/author/year and doi if both contain the doi), and comments, if any. In addition to this tab delimitated output file, another output file with additional extension `csv` is created. As the extension specifies this output file is a comma delimited file, having header line, where bibcodes are linked to the ADS records.
In some cases, there might be more than one match for the source bibcode with the same exact confidence score. In the tab delimited output file, the comment would contain this information that multiple matches were detected, and in the comma delimited output file, the details of multi matched bibcodes and similarity scores are included. The logic is that the comma delimited file is for curators verification, and the tab delimited file is for system to ingest the matches.

### Match new published records to eprints in Solr

This takes an input list of newly published papers and attempts to match them to existing unmatched eprints in Solr.  The name of the input file is set in the config variable ``DOCMATCHPIPELINE_INPUT_FILENAME``

  ``python3 run.py -me -p "/path/to/input/filename/"``

If docmatching is being run in parallel with the existing classic matching process, the pipeline will then attempt to compare the two methods, and the comparison between them will be uploaded to the Google Drive folder set in the config variable ``GOOGLE_BASEDIR_ID`` with the filename ``DOCMATCHPIPELINE_PUB_COMBINED_FILENAME``, prefixed with the day's date.  If the classic script is not run, the results of docmatching alone will be uploaded with the filename set by ``DOCMATCHPIPELINE_PUB_RESULT_FILENAME``.


### Capabilities:

* For arXiv record if DOI is provided in the metadata, oracle tries to match with DOI only if the scores for abstract/title/author/year are high.
* For arXiv record if the word thesis appears in metadata, oracle tries to match the record with either PhD thesis or Masters thesis.
* For arXiv record if no result is returned from solr, if the arXiv class from metadata is either Astrophysics or Physics, title search is attempted. This is useful when abstrct has been changed dristically from the arXiv version to refeered version.
* Doctype eprint for arXiv is matched with doctypes of article, inproceedings, and inbook that are referred.
* For arXiv record publisher record has to be `refereed`.
* If more than one record has been matched, if the confidence score is high, both are output to signal duplicate records. However, if the confidence score is low, no matched is returned.    

    
## Add to, edit, or query curated records in the oracle database

### Add/update curated records to oracledb

This takes all files in the Google directory with identifier set by the config variable ``GOOGLE_CURATED_FOLDER_ID``, downloads each one, processes the data, and sends the results to the /add endpoint of oracle_service.  Following successful download, the files on Google are moved to the directory with identifier set by the config variable ``GOOGLE_ARCHIVE_FOLDER_ID`` for permanent storage.  To run the command, simply use the -oa option of run.py:

   ``python3 run.py -oa``
   
To manually add matches to the database, include a two column, tab delimited input file, with list of matched bibcodes, and the source of these matches.

   ``python3 run.py -mf "/path/to/input/filename/" -as <source>``
   
### Capabilities:

* To list all available source-score use command ``-lss``


### Query oracledb for matches added in the past N days

This queries the oracle_service api to obtain all matches added to oracle over a number of days specified by the user (default = 1), and outputs them to a local filename also specified by the user (default = './output.csv')

   ``python3 run.py -q -n <integer> -o <input filename>``


# Maintainers

* Golnaz Shapurian, ADS
* Matthew Templeton, ADS

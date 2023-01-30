[![Build Status](https://travis-ci.org/adsabs/ADSDocMatchPipeline.svg)](https://travis-ci.org/adsabs/ADSDocMatchPipeline)
[![Coverage Status](https://coveralls.io/repos/adsabs/ADSDocMatchPipeline/badge.svg)](https://coveralls.io/r/adsabs/ADSDocMatchPipeline)

# ADS Doc Match Pipeline

#===================== need to be updated
## Short Summary

Scripts to match publisher document with arXiv counterpart and vice versa.


## Setup (recommended)

    $ virtualenv python
    $ source python/bin/activate
    $ pip install --upgrade setuptools
    $ pip install -r requirements.txt
    
    Add your ADS token to `from_oracle.py` for oracle service.


### For finding matches for metadata

##### To match arXiv metadata to publisher bibcode in solr use script:
    
    match_to_pub.py
    
##### To match publisher metadata to arXiv bibcode in solr use script:

    match_to_arxiv.py

##### Command line arguments:

* -i is to specify path to an input file containing list of arXiv/publisher metadata files for processing, one file name per line.
* -o is to specify output file name to write the result in. This is optional and if not provided the matching results shall be written to console.
* -s is to specify filename for a single metadata file for processing. The result of match is written to console.

Note that the output file is a tab delimited text file, containing 6 columns, with no header line. The columns are source bibcode, matched bibcode, if any, label (ie, whether the system thinks it is a Match or Not Match), confidence score, similarity scores (ie, similarity scores between the source and matched bibcodes for abstract/title/author/year and doi if both contain the doi), and comments, if any. In addition to this tab delimitated output file, another output file with additional extension `csv` is created. As the extension specifies this output file is a comma delimited file, having header line, where bibcodes are linked to the ADS records. 
In some cases, there might be more than one match for the source bibcode with the same exact confidence score. In the tab delimited output file, the comment would contain this information that multiple matches were detected, and in the comma delimited output file, the details of multi matched bibcodes and similarity scores are included. The logic is that the comma delimited file is for curators verification, and the tab delimited file is for system to ingest the matches.

##### Capabilities:

* For arXiv record if DOI is provided in the metadata, oracle tries to match with DOI only if the scores for abstract/title/author/year are high.
* For arXiv record if the word thesis appears in metadata, oracle tries to match the record with either PhD thesis or Masters thesis.
* For arXiv record if no result is returned from solr, if the arXiv class from metadata is either Astrophysics or Physics, title search is attempted. This is useful when abstrct has been changed dristically from the arXiv version to refeered version.
* Doctype eprint for arXiv is matched with doctypes of article, inproceedings, and inbook that are referred.
* For arXiv record publisher record has to be `refereed`.
* If more than one record has been matched, if the confidence score is high, both are output to signal duplicate records. However, if the confidence score is low, no matched is returned.    

##### Command lines:
    
    python match_to_pub.py -i"match_oracle.input" -o"match_oracle.out"
    python match_to_arxiv.py -i <input filename> -o <output filename>
    
    
### To access oracle service database

##### To add/delete to/from database or query database use script:
    
    oracle_db.py
    
##### Command line arguments:

* -f is to specify path to either an input file containing list of source bibcode, matched bibcode, and confidence score, separated by tabs, for the add and delete actions, or an output file name to write the result of query to.
* -a is to specify the action to take `add`, `del`, or `query`.
* -d optional argument for query action to return the past number of days' matches only.

##### Capabilities:

* To add matches to db, in the input file, the confidence score can be ignored, in which case, the default value of 2.0 is used. However, for the matches to be deleted from db, the confidence score is necessary, since there could be multiple records with the same source and matched bibcodes, but different scores (ie, when abstract is missing from metadata or solr, and is included later on).
* The input file can contain comments, specified with `#`, which is ignored. Comments can at the beginning of the line, hence no data in the line, or as a fourth column of tab delimited line, with the first 2 to 3 columns containing the data.

##### Command lines:

    python oracle_db.py -a add -f <input filename>
    python oracle_db.py -a del -f <input filename>
    python oracle_db.py -a query -f <output filename> -d <include past number of days only> 


### To create results for verification

##### To combine the results of the new matching system with the classic system use script:

    compare_to_classic.py

##### Command line arguments:

* c is to specify path to an output results file from classic, containing three columns, tab delimited, source bibcode, matched bibcode, and score.
* n is to specify the path to an output results file from docmatching, this is the tab delimited output file.
* a is to specify the path to an output results file from docmatching, this is the comma delimited output file.
* o is to specify output file name to write the combined result of classic and new system to. This is optional and if not provided the combined results shall be written to console.
* o is to specify output file name to write the combined result of classic and new system to. This is optional and if not provided the combined results shall be written to console.
* s is to specify the source of the output results file, eprint or pub, to be able to match the right bibcodes with the source bibcode from the classic side.

##### Capabilities:

* Creates a comma delimited file, with 8 columns as follows: `source bibcode (link),verified bibcode,curator comment,classic bibcode (link),confidence,matched bibcode (link),matched score,comment`. Note that this is the header line included in the file.

##### Command lines:

    python compare_to_classic.py -c"match.out" -n"match_oracle.out" -o<output filename> -s"eprint"
    python compare_to_classic.py -c"match.out" -a"match_oracle.out.csv" -o<output filename> -s"pub"


### To extract curated matches

##### To extract curated matches to send to be sent to oracle db use script:

    extract_curated_matches.py

##### Command line arguments:

* -i is to specify path to an input excel file containing curated matches.
* -o is to specify output path to write the result in. Filename is the same as input with extension txt.

##### Capabilities:

* Creates a tab delimited file, with 3 columns as follows: eprint_bibcode, publisher_bibcode, score (1.1 to add to db and -1 to mark as having been deleted).

##### Command lines:

    python extract_curated_matches.py -i"/Downloads/2022-11-23.compare.xlsx" -o"output/"


## Maintainers

Golnaz

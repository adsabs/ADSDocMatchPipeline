# Docmatch Scripts

## Short Summary

Scripts to match publisher document with arXiv counterpart and vice versa.


## Setup (recommended)

    $ virtualenv python
    $ source python/bin/activate
    $ pip install --upgrade setuptools
    $ pip install -r requirements.txt
    
    Add your ADS token to `from_oracle.py` for oracle service.

### For matching arXiv bibcode to publisher bibcode in solr use script:
    
    match_to_pub.py
    
### For matching publisher bibcode to arXiv bibcode in solr use script:

    match_to_arxiv.py

### Command line arguments:

* -i is to specify path to an input file containing list of arXiv/publisher metadata files for processing, one file name per line.
* -o is to specify output file name to write the result in. This is optional and if not provided the matching results shall be written to console.
* -s is to specify filename for a single metadata file for processing. The result of match is written to console.

### Capabilities:
* For arXiv record if DOI is provided in the metadata, oracle tries to match with DOI only if the scores for abstract/title/author/year are high.
* For arXiv record if the word thesis appears in metadata, oracle tries to match the record with either PhD thesis or Masters thesis.
* For arXiv record if no result is returned from solr, if the arXiv class from metadata is either Astrophysics or Physics, title search is attempted. This is useful when abstrct has been changed dristically from the arXiv version to refeered version.
* Doctype eprint for arXiv is matched with doctypes of article, inproceedings, and inbook that are referred.
* For arXiv record publisher record has to be `refereed`.
* If more than one record has been matched, if the confidence score is high, both are output to signal duplicate records. However, if the confidence score is low, no matched is returned.

## Maintainers

Golnaz

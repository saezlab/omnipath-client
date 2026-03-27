# New OmniPath python client

Plans to replace the old [OmniPath Python client](https://github.com/saezlab/omnipath)

## Specification
* New Python package for accessing data from the new OmniPath web API: https://dev.omnipathdb.org/
* It is a FastAPI web service implemented in https://github.com/saezlab/omnipath-build
* The data comes as Parquet files by default
* These can be delivered to pandas, polars or pyarrow data frames
* Network (graph) like data should be delivered as [Annnet objects](https://github.com/saezlab/annnet)
* Validation for query parameters and values
* Access to possible endpoints, parameters and values
* Check for any issue with response error handling
* Unit tests
* Logging, session, etc (see #implementation_details)

## Implementation details
* [Create repo from project template](https://github.com/saezlab/python-project)
* [Cache manager](https://github.com/saezlab/cache-manager)
* [Download manager](https://github.com/saezlab/download-manager)
* [Logger and config manager](https://github.com/saezlab/pkg_infra)

## Further Plans
* Evaluate options for async downloads (cache and download manager should be updatednload)

## Structure

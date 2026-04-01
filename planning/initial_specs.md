# New OmniPath python client

Plans to replace the old [OmniPath Python client](https://github.com/saezlab/omnipath)

## Specification
* New Python package for accessing data from the new OmniPath web API: https://dev.omnipathdb.org/
* It is a FastAPI web service implemented in https://github.com/saezlab/omnipath-present
* The data comes as Parquet files by default
* These can be delivered to pandas, polars or pyarrow data frames and DuckDB
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
* [Session, logger and config manager](https://github.com/saezlab/pkg_infra)

## Further Plans
* Evaluate options for async downloads (cache and download manager should be updatednload)

## API docs

The web API is documented in https://dev.omnipathdb.org/api-docs (also
available here: https://github.com/saezlab/omnipath-present/blob/main/next-omnipath/src/app/api-docs/page.tsx). The client should populate its inventory of endpoints, arguments and allowed values based on the API docs. This ensures rapid development and updates of the API.

## First plan updates

- Config should be based on generic config solution in pkg_infra, which most
    likely doesn't exist, in this case we should create it
- Also for logging we should use the solution in `pkg_infra`, and update it as
    required.
- The concrete integration surface is the top-level `pkg_infra` package,
    notably `pkg_infra.get_session()` and `pkg_infra.session` /
    `pkg_infra.logger`, not the older `saezlab_core` module naming
- This client package in the future should be able accommodate different
    formats and API endpoints than Parquet files, the Parquet route is our
    first default solution
- Using `download-manager`, we should still aim for an async operation, and
    update the `download-manager` and `cache-manager` accordingly
- Very soon a standard FastAPI/swagger openapi.json will be available, until
    now we can rely on a parsing of the HTML API docs; this should be done on
    import to populate the Python API here, but download failure should not
    blokc import

## Run web service locally

```
git clone git@github.com:saezlab/omnipath-present.git
cd omnipath-present/api-service
uv sync
uv run uvicorn api_service.main:app --reload --port 8081
```

```
curl http://localhost:8081/openapi.json -o openapi.json
```

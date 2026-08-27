# Network datasets

A **dataset** is a named selection over the OmniPath interaction record:
LIANA is the ligand-receptor slice, MetaLinksDB is the metabolite-protein
one. The service holds the definitions, so this client does not carry a
list of dataset names. It reads them.

## Point the client at a service

The datasets are new, so they are on a development deployment first. Set
the base URL once, and every later call uses it:

```python
import omnipath_client as op

op.set_base_url('https://dev3.omnipathdb.org/api')
op.base_url()
```

```
'https://dev3.omnipathdb.org/api'
```

Set `OMNIPATH_BASE_URL` in the environment to do the same without a call,
for a script that must not name a deployment in its source.

## See what the service carries

```python
op.datasets.names()
```

```
['metalinksdb', 'liana']
```

These names come from the service, so tab completion after
`op.datasets.` offers what this deployment actually serves.

## Get a dataset as a DataFrame

```python
liana = op.datasets.liana
df = liana.get(limit = 5)

df.select(['source_label', 'target_label', 'interaction_type', 'resources'])
```

```
┌──────────────┬──────────────┬──────────────────┬──────────────────┐
│ source_label ┆ target_label ┆ interaction_type ┆ resources        │
╞══════════════╪══════════════╪══════════════════╪══════════════════╡
│ col5a1       ┆ ddr1         ┆ ligand_receptor  ┆ connectomedb2025 │
│ col5a1       ┆ sdc3         ┆ ligand_receptor  ┆ connectomedb2025 │
│ col5a1       ┆ ddr2         ┆ ligand_receptor  ┆ connectomedb2025 │
│ col5a1       ┆ itga2        ┆ ligand_receptor  ┆ connectomedb2025 │
│ col5a1       ┆ itgb1        ┆ ligand_receptor  ┆ connectomedb2025 │
└──────────────┴──────────────┴──────────────────┴──────────────────┘
```

The frame is polars by default, or the first backend installed. Ask for
another with `backend`:

```python
op.datasets.metalinksdb.get(limit = 5, backend = 'pandas')
```

The service pages, so `limit` is the size of one request. Page further
with the `cursor` a page returns:

```python
page = liana.get(limit = 1000)
```

## Ask what a dataset is made of

```python
liana.resources()
liana.attributes()
```

```
['connectomedb2025']
['endpoints', 'label', 'references', 'evidence']
```

`info()` gives the whole registry row: the contributing resources, the
interaction classes the dataset is restricted to, the attributes it
projects, and — for a dataset assembled from parts, as MetaLinksDB is —
the composition it is built by.

```python
op.datasets.metalinksdb.info()['curation']
```

```
{'chembl_curation': 'mechanism_of_action',
 'chemical_class_gate': 'metabolite',
 'excluded_from_combined': ['bindingdb']}
```

## Ask how much there is, without fetching it

```python
stats = liana.stats()
stats['total'], stats['total_is_estimate']
```

```
(27161, True)
```

Nothing stores the collapsed dataset, so a total is the cost governor's
estimate unless you ask for an exact count. `total_is_estimate` always
says which one you got. Restrict the scope to count a part of it:

```python
liana.stats(organism = '9606')
```

!!! note "Every summary describes the scope you asked for"

    Source counts, references and the sign and direction flags on each
    row describe the resources your query admits — not every resource in
    the build. Restricting to one resource therefore changes them, which
    is the point.

## Past the datasets

A dataset is a parameter, not a special case, so anything a dataset
accessor does not reach is reached through the general functions:

```python
op.interactions(
    filters = {
        'datasets': 'liana',
        'exclude_resources': 'connectomedb2025',
    },
    limit = 10,
)

op.interaction_stats(resources = 'signor', exact_total = True)
op.interaction_parameters(organism = '9606')
```

`op.interaction_parameters()` reports the values each parameter can still
take under the scope you have narrowed to — so a filter that would leave
nothing is visible before you run the query.

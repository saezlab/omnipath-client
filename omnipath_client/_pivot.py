"""Friendly aliases and wide-form pivots for entity / relation tables.

The OmniPath API returns identifiers in a long-form ``list[struct]``
column where each entry pairs a value with an MI/OM ontology code
(``MI:0474:Chebi``, ``OM:0202:Name``, …). End users almost always want
those values pivoted into named columns and to refer to id types with
short, lowercase aliases. This module owns the alias map and the
polars logic that does the pivot + join.

The alias map is the single source of truth used by both ``lookup()``
and ``related()``.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence


# Friendly alias -> ordered list of underlying identifier_type codes.
# Order matters: the first code that yields a hit wins.
ID_ALIASES: dict[str, tuple[str, ...]] = {
    'name': ('OM:0202:Name', 'OM:0200:Gene Name Primary'),
    'genesymbol': ('OM:0200:Gene Name Primary', 'MI:1801:Hgnc Symbol'),
    'chebi': ('MI:0474:Chebi',),
    'hmdb': ('OM:0004:Hmdb',),
    'kegg': ('MI:2012:Kegg Compound', 'MI:0470:Kegg'),
    'pubchem': ('OM:0002:Pubchem Compound', 'MI:0730:Pubchem'),
    'drugbank': ('MI:2002:Drugbank',),
    'chembl': ('MI:1349:Chembl',),
    'cas': ('MI:2011:Cas',),
    'uniprot': ('MI:1097:Uniprot', 'MI:0473:Uniprotkb'),
    'entrez': ('MI:0477:Entrez',),
    'ensembl': ('MI:0476:Ensembl',),
    'hgnc': ('MI:1095:Hgnc',),
    'mirbase': ('MI:0478:Mirbase',),
    'inchi': ('MI:2010:Standard Inchi',),
    'inchikey': ('MI:1101:Standard Inchi Key',),
    'smiles': ('MI:0239:Smiles',),
    'lipidmaps': ('OM:0204:Lipidmaps', 'MI:1108:Lipid Maps'),
    'swisslipids': ('OM:0205:Swisslipids',),
    'iupac': ('OM:0210:Iupac Name', 'OM:0211:Iupac Traditional Name'),
    'mass': ('OM:0602:Mass Dalton',),
    'formula': ('OM:0212:Molecular Formula',),
}


# Friendly alias -> participant-type / entity-type MI code.
# Used by ``related()``'s ``participant_types=`` filter and by
# ``lookup()``'s ``entity_types=`` filter.
PARTICIPANT_TYPE_ALIASES: dict[str, str] = {
    'protein': 'MI:0326:Protein',
    'small_molecule': 'MI:0328:Small Molecule',
    'complex': 'MI:0314:Complex',
    'mirna': 'MI:0682:Mirna',
    'gene': 'MI:0250:Gene',
    'rna': 'MI:0320:Ribonucleic Acid',
    'phenotype': 'MI:2261:Phenotype',
    'cv_term': 'OM:0012:Cv Term',
    'family': 'OM:0017:Family',
}


# Default ``id_types`` for ``lookup()`` / ``related()``. Narrow enough
# to keep output readable, broad enough to cover the most common
# downstream joins.
DEFAULT_ID_TYPES: tuple[str, ...] = (
    'name',
    'chebi',
    'hmdb',
    'uniprot',
    'genesymbol',
)


def expand_aliases(
    values: Iterable[str],
    alias_map: dict[str, Any],
) -> list[str]:
    """Expand friendly aliases to underlying ontology codes.

    Strings already in MI:/OM: form pass through unchanged. Unknown
    aliases also pass through (lets the user supply a raw code).

    Args:
        values:
            Aliases or codes to expand.
        alias_map:
            One of ``ID_ALIASES`` or ``PARTICIPANT_TYPE_ALIASES``.

    Returns:
        Flat list of ontology codes, in iteration order, deduplicated.
    """

    out: list[str] = []
    seen: set[str] = set()

    for v in values:
        if v in alias_map:
            mapped = alias_map[v]

            if isinstance(mapped, str):
                mapped = (mapped,)

            for code in mapped:
                if code not in seen:
                    out.append(code)
                    seen.add(code)

        else:
            if v not in seen:
                out.append(v)
                seen.add(v)

    return out


def _require_polars() -> Any:
    """Import polars or raise an informative error."""

    try:
        import polars as pl

    except ImportError as e:
        raise ImportError(
            'lookup() and related() require polars. '
            'Install with: pip install omnipath-client[polars]',
        ) from e

    return pl


def pivot_identifiers(
    entities_df: Any,
    id_types: Sequence[str] = DEFAULT_ID_TYPES,
    *,
    prefix: str = '',
    keep_canonical: bool = False,
) -> Any:
    """Pivot the long-form ``identifiers`` column into wide columns.

    For each alias in ``id_types`` the entity's matching identifiers
    are collected, the **shortest** value is picked as the
    representative, and a new column is added.

    Args:
        entities_df:
            A polars DataFrame with at least ``entity_pk`` and
            ``identifiers`` columns.
        id_types:
            Aliases (or raw codes) to pivot into columns.
        prefix:
            String prefixed to each new column name (e.g. ``'subject_'``).
        keep_canonical:
            If True, retain the raw ``canonical_identifier`` and
            ``identifiers`` columns; otherwise drop them.

    Returns:
        A polars DataFrame with one row per input row and one new
        column per requested ``id_type``.
    """

    pl = _require_polars()

    if 'identifiers' not in entities_df.columns:
        return entities_df

    long = (
        entities_df
        .select('entity_pk', 'identifiers')
        .explode('identifiers')
        .unnest('identifiers')
        .drop_nulls(subset=['identifier'])
        .with_columns(pl.col('identifier').str.len_chars().alias('_len'))
    )

    pivot = entities_df.select('entity_pk')

    for alias in id_types:
        codes = ID_ALIASES.get(alias, (alias,))
        col_name = f'{prefix}{alias}'

        priority = pl.col('identifier_type').replace_strict(
            {c: i for i, c in enumerate(codes)},
            default=len(codes),
        )

        per_entity = (
            long
            .filter(pl.col('identifier_type').is_in(list(codes)))
            .with_columns(priority.alias('_prio'))
            .sort(['_prio', '_len'])
            .group_by('entity_pk')
            .agg(pl.col('identifier').first().alias(col_name))
        )

        pivot = pivot.join(per_entity, on='entity_pk', how='left')

    drop_cols = [] if keep_canonical else [
        c for c in (
            'canonical_identifier',
            'canonical_identifier_type',
            'identifiers',
            'entity_attributes',
            'taxonomy_id',
        )
        if c in entities_df.columns
    ]

    rest = entities_df.drop(drop_cols)
    rest_renamed = rest.rename(
        {c: f'{prefix}{c}' for c in rest.columns if c != 'entity_pk'},
    )

    pivot_renamed = pivot.rename({'entity_pk': f'{prefix}entity_pk'}) \
        if prefix else pivot

    join_key = f'{prefix}entity_pk' if prefix else 'entity_pk'
    rest_renamed = rest_renamed.rename({'entity_pk': join_key}) \
        if 'entity_pk' in rest_renamed.columns else rest_renamed

    return rest_renamed.join(pivot_renamed, on=join_key, how='left')


def join_relations_with_entities(
    relations_df: Any,
    entities_df: Any,
    id_types: Sequence[str] = DEFAULT_ID_TYPES,
    *,
    keep_canonical: bool = False,
) -> Any:
    """Left-join entities to both sides of a relations table.

    Produces ``subject_*`` and ``object_*`` columns for every
    ``id_types`` entry plus ``subject_entity_type`` /
    ``object_entity_type``. The original relation columns
    (``relation_pk``, ``predicate``, ``relation_category``,
    ``evidence_count``, ``sources``) are preserved.

    Args:
        relations_df:
            A polars DataFrame from ``OmniPath.relations()``.
        entities_df:
            A polars DataFrame from ``OmniPath.entities()`` covering
            every entity_pk that appears as subject or object.
        id_types:
            Aliases to pivot.
        keep_canonical:
            Whether to retain canonical_identifier / identifiers columns
            on each side.

    Returns:
        A wide polars DataFrame.
    """

    pl = _require_polars()

    subj = pivot_identifiers(
        entities_df,
        id_types=id_types,
        prefix='subject_',
        keep_canonical=keep_canonical,
    )
    obj = pivot_identifiers(
        entities_df,
        id_types=id_types,
        prefix='object_',
        keep_canonical=keep_canonical,
    )

    out = (
        relations_df
        .join(subj, on='subject_entity_pk', how='left')
        .join(obj, on='object_entity_pk', how='left')
    )

    front = [c for c in (
        'subject_name', 'subject_entity_type', 'predicate',
        'object_name', 'object_entity_type', 'relation_category',
        'evidence_count', 'sources',
    ) if c in out.columns]
    rest = [c for c in out.columns if c not in front]

    return out.select(front + rest)

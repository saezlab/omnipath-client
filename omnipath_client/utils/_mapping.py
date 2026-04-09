"""ID translation client."""

from __future__ import annotations

from typing import Any
import logging

from omnipath_client.utils._base import _get, _post


_log = logging.getLogger(__name__)


def map_name(
    name: str,
    id_type: str,
    target_id_type: str,
    ncbi_tax_id: int = 9606,
    raw: bool = False,
    backend: str | None = None,
) -> set[str]:
    """Translate a single identifier via the web service."""

    params: dict[str, Any] = {
        'identifiers': name,
        'id_type': id_type,
        'target_id_type': target_id_type,
        'ncbi_tax_id': ncbi_tax_id,
        'raw': raw,
    }

    if backend:
        params['backend'] = backend

    data = _get('/mapping/translate', params)
    results = data.get('results', {})

    return set(results.get(name, []))


def map_names(
    names: list[str] | set[str],
    id_type: str,
    target_id_type: str,
    ncbi_tax_id: int = 9606,
    raw: bool = False,
    backend: str | None = None,
) -> set[str]:
    """Translate multiple identifiers, return union."""

    result = translate(
        list(names),
        id_type,
        target_id_type,
        ncbi_tax_id,
        raw=raw,
        backend=backend,
    )

    return set().union(*result.values())


def map_name0(
    name: str,
    id_type: str,
    target_id_type: str,
    ncbi_tax_id: int = 9606,
) -> str | None:
    """Translate, return single result."""

    result = map_name(name, id_type, target_id_type, ncbi_tax_id)

    return next(iter(result)) if result else None


def translate(
    identifiers: list[str],
    id_type: str,
    target_id_type: str,
    ncbi_tax_id: int = 9606,
    raw: bool = False,
    backend: str | None = None,
) -> dict[str, set[str]]:
    """Batch translate via POST (for large lists)."""

    body: dict[str, Any] = {
        'identifiers': identifiers,
        'id_type': id_type,
        'target_id_type': target_id_type,
        'ncbi_tax_id': ncbi_tax_id,
        'raw': raw,
    }

    if backend:
        body['backend'] = backend

    # Use POST for >10 IDs, GET for small queries
    if len(identifiers) > 10:
        data = _post('/mapping/translate', body)
    else:
        params: dict[str, Any] = {
            'identifiers': ','.join(identifiers),
            'id_type': id_type,
            'target_id_type': target_id_type,
            'ncbi_tax_id': ncbi_tax_id,
            'raw': raw,
        }

        if backend:
            params['backend'] = backend

        data = _get('/mapping/translate', params)

    results = data.get('results', {})

    return {k: set(v) for k, v in results.items()}


def translate_column(
    df: Any,
    column: str,
    id_type: str,
    target_id_type: str,
    ncbi_tax_id: int = 9606,
    new_column: str | None = None,
    keep_untranslated: bool = True,
    expand: bool = True,
    raw: bool = False,
    backend: str | None = None,
) -> Any:
    """Translate a DataFrame column via the web service.

    Works with pandas, polars, and pyarrow DataFrames via narwhals.
    """

    import narwhals as nw

    new_col = new_column or target_id_type
    nw_df = nw.from_native(df, eager_only=True)

    # Get unique values
    unique_vals = list(
        {str(v) for v in nw_df[column].to_list() if v is not None}
    )

    # Batch translate via service
    trans = translate(
        unique_vals,
        id_type,
        target_id_type,
        ncbi_tax_id,
        raw=raw,
        backend=backend,
    )

    native_ns = nw.get_native_namespace(nw_df)

    if expand:
        src_vals: list[str] = []
        tgt_vals: list[str | None] = []

        for src, targets in trans.items():
            if targets:
                for tgt in sorted(targets):
                    src_vals.append(src)
                    tgt_vals.append(tgt)
            elif keep_untranslated:
                src_vals.append(src)
                tgt_vals.append(None)

        all_sources = {
            str(v) for v in nw_df[column].to_list() if v is not None
        }

        for src in all_sources - set(trans.keys()):
            if keep_untranslated:
                src_vals.append(src)
                tgt_vals.append(None)

        _jk = '_join_key'
        mapping = nw.from_native(
            native_ns.DataFrame({_jk: src_vals, new_col: tgt_vals}),
            eager_only=True,
        )
        result = nw_df.with_columns(
            nw.col(column).cast(nw.String).alias(_jk),
        ).join(
            mapping,
            on=_jk,
            how='left' if keep_untranslated else 'inner',
        ).drop(_jk)

        if not keep_untranslated:
            result = result.filter(nw.col(new_col).is_not_null())
    else:
        values = [
            next(iter(sorted(trans.get(str(v), set()))))
            if v and trans.get(str(v))
            else None
            for v in nw_df[column].to_list()
        ]
        result = nw_df.with_columns(
            nw.new_series(
                name=new_col,
                values=values,
                native_namespace=native_ns,
            ),
        )

        if not keep_untranslated:
            result = result.filter(nw.col(new_col).is_not_null())

    return nw.to_native(result)


def translate_columns(
    df: Any,
    *translations: tuple[str, ...],
    ncbi_tax_id: int = 9606,
    keep_untranslated: bool = True,
    expand: bool = True,
) -> Any:
    """Translate multiple columns."""

    for t in translations:
        col, id_type_val, target = t[0], t[1], t[2]
        new_col = t[3] if len(t) > 3 else None
        df = translate_column(
            df,
            col,
            id_type_val,
            target,
            ncbi_tax_id=ncbi_tax_id,
            new_column=new_col,
            keep_untranslated=keep_untranslated,
            expand=expand,
        )

    return df


def id_types() -> list[dict]:
    """List all supported ID types."""

    return _get('/mapping/id-types')


def identify(
    identifiers: str | list[str],
    ncbi_tax_id: int = 9606,
) -> dict[str, list[dict]]:
    """Identify the type of given identifiers."""

    if isinstance(identifiers, str):
        identifiers = [identifiers]

    return _get(
        '/mapping/identify',
        {
            'identifiers': ','.join(identifiers),
            'ncbi_tax_id': ncbi_tax_id,
        },
    ).get('results', {})


def all_mappings(
    identifiers: str | list[str],
    id_type: str,
    ncbi_tax_id: int = 9606,
) -> dict[str, dict[str, list[str]]]:
    """Get all known mappings for identifiers."""

    if isinstance(identifiers, str):
        identifiers = [identifiers]

    return _get(
        '/mapping/all',
        {
            'identifiers': ','.join(identifiers),
            'id_type': id_type,
            'ncbi_tax_id': ncbi_tax_id,
        },
    ).get('results', {})


def translation_dict(
    id_type: str,
    target_id_type: str,
    ncbi_tax_id: int = 9606,
    identifiers: str | list[str] | None = None,
    raw: bool = False,
    backend: str | None = None,
) -> dict[str, set[str]]:
    """Get translation data as a dict.

    Downloads the full translation table by default. If identifiers are
    given, translates only those.

    Args:
        id_type: Source ID type.
        target_id_type: Target ID type.
        ncbi_tax_id: Organism (default: 9606).
        identifiers: Optional list of source IDs. None = full table.
        raw: Skip special-case handling.
        backend: Force specific backend.

    Returns:
        Dict mapping source IDs to sets of target IDs.

    Example::

        # Full table
        table = translation_dict('genesymbol', 'uniprot')
        table['TP53']  # {'P04637'}

        # Specific IDs only
        table = translation_dict(
            'genesymbol', 'uniprot', identifiers=['TP53', 'EGFR'],
        )
    """

    if identifiers is not None:
        if isinstance(identifiers, str):
            identifiers = [identifiers]

        return translate(
            identifiers,
            id_type,
            target_id_type,
            ncbi_tax_id,
            raw=raw,
            backend=backend,
        )

    # Full table download
    data = _get('/mapping/table', {
        'id_type': id_type,
        'target_id_type': target_id_type,
        'ncbi_tax_id': ncbi_tax_id,
    })
    table = data.get('table', {})

    return {k: set(v) for k, v in table.items()}


def translation_df(
    id_type: str,
    target_id_type: str,
    ncbi_tax_id: int = 9606,
    identifiers: str | list[str] | None = None,
    raw: bool = False,
    backend: str | None = None,
) -> Any:
    """Get translation data as a DataFrame.

    Downloads the full table by default. Returns a two-column DataFrame.

    Args:
        id_type: Source ID type.
        target_id_type: Target ID type.
        ncbi_tax_id: Organism (default: 9606).
        identifiers: Optional list of source IDs. None = full table.
        raw: Skip special-case handling.
        backend: Force specific backend.

    Example::

        df = translation_df('genesymbol', 'uniprot')
        # Full genesymbol -> uniprot table as DataFrame
    """

    trans = translation_dict(
        id_type,
        target_id_type,
        ncbi_tax_id,
        identifiers=identifiers,
        raw=raw,
        backend=backend,
    )

    src_vals: list[str] = []
    tgt_vals: list[str] = []

    for src, targets in trans.items():
        for tgt in sorted(targets):
            src_vals.append(src)
            tgt_vals.append(tgt)

    try:
        import polars as pl

        return pl.DataFrame({id_type: src_vals, target_id_type: tgt_vals})
    except ImportError:
        pass

    try:
        import pandas as pd

        return pd.DataFrame({id_type: src_vals, target_id_type: tgt_vals})
    except ImportError:
        pass

    _log.warning('No DataFrame library available, returning dict')

    return trans

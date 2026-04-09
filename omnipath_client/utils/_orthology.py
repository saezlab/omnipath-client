"""Orthology client."""

from __future__ import annotations

from typing import Any

from omnipath_client.utils._base import _get


def translate(
    identifiers: list[str],
    source: int = 9606,
    target: int = 10090,
    id_type: str = 'genesymbol',
    resource: str | None = None,
    min_sources: int = 1,
    raw: bool = False,
) -> dict[str, set[str]]:
    """Translate identifiers to orthologs via the web service."""

    params: dict[str, Any] = {
        'identifiers': ','.join(identifiers),
        'source': source,
        'target': target,
        'id_type': id_type,
        'min_sources': min_sources,
        'raw': raw,
    }

    if resource:
        params['resource'] = resource

    data = _get('/orthology/translate', params)
    results = data.get('results', {})

    return {k: set(v) for k, v in results.items()}


def translate_column(
    df: Any,
    column: str,
    source: int = 9606,
    target: int = 10090,
    id_type: str = 'genesymbol',
    new_column: str | None = None,
    keep_untranslated: bool = True,
    expand: bool = True,
    resource: str | None = None,
    min_sources: int = 1,
) -> Any:
    """Translate a DataFrame column to orthologs via the web service."""

    import narwhals as nw

    new_col = new_column or f'{column}_{target}'
    nw_df = nw.from_native(df, eager_only=True)

    unique_vals = list(
        {str(v) for v in nw_df[column].to_list() if v is not None}
    )
    trans = translate(
        unique_vals,
        source=source,
        target=target,
        id_type=id_type,
        resource=resource,
        min_sources=min_sources,
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

        for src in (
            {str(v) for v in nw_df[column].to_list() if v is not None}
            - set(trans.keys())
        ):
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
        )
        result = result.join(
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


def orthology_dict(
    identifiers: str | list[str],
    source: int = 9606,
    target: int = 10090,
    id_type: str = 'genesymbol',
    resource: str | None = None,
    min_sources: int = 1,
    raw: bool = False,
) -> dict[str, set[str]]:
    """Get orthology data as a dict.

    Example::

        table = orthology_dict(['TP53', 'EGFR'], source=9606, target=10090)
        table['TP53']  # {'Trp53'}
    """

    if isinstance(identifiers, str):
        identifiers = [identifiers]

    return translate(
        identifiers,
        source=source,
        target=target,
        id_type=id_type,
        resource=resource,
        min_sources=min_sources,
        raw=raw,
    )


def orthology_df(
    identifiers: str | list[str],
    source: int = 9606,
    target: int = 10090,
    id_type: str = 'genesymbol',
    resource: str | None = None,
    min_sources: int = 1,
    raw: bool = False,
) -> Any:
    """Get orthology data as a DataFrame.

    Example::

        df = orthology_df(['TP53', 'EGFR'], source=9606, target=10090)
    """

    if isinstance(identifiers, str):
        identifiers = [identifiers]

    trans = translate(
        identifiers,
        source=source,
        target=target,
        id_type=id_type,
        resource=resource,
        min_sources=min_sources,
        raw=raw,
    )

    src_vals: list[str] = []
    tgt_vals: list[str] = []

    for src, targets in trans.items():
        for tgt in sorted(targets):
            src_vals.append(src)
            tgt_vals.append(tgt)

    src_col = f'{id_type}_{source}'
    tgt_col = f'{id_type}_{target}'

    try:
        import polars as pl

        return pl.DataFrame({src_col: src_vals, tgt_col: tgt_vals})
    except ImportError:
        pass

    try:
        import pandas as pd

        return pd.DataFrame({src_col: src_vals, tgt_col: tgt_vals})
    except ImportError:
        pass

    return trans

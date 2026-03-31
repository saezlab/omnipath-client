# Installation

## Requirements

- Python >= 3.10

## Install with pip

```bash
pip install omnipath-client
```

## Install from source

```bash
pip install git+https://github.com/saezlab/omnipath-client.git
```

Or for development:

```bash
git clone https://github.com/saezlab/omnipath-client.git
cd omnipath-client
pip install -e ".[dev,tests]"
```

## Optional dependencies

omnipath-client supports multiple DataFrame backends. The default backend is
**polars**, which must be installed separately:

```bash
pip install polars
```

For other backends:

```bash
pip install pandas    # pandas backend
pip install pyarrow   # pyarrow backend (also required for Parquet reading)
```

For graph conversion to [annnet](https://github.com/saezlab/annnet) objects:

```bash
pip install annnet
```

## Using uv

If you use [uv](https://docs.astral.sh/uv/) for dependency management:

```bash
uv add omnipath-client
uv add polars  # or pandas, pyarrow
```

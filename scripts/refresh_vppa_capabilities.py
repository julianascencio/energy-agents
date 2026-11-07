"""Reuse the source-catalogue builder for a focused procurement inventory."""
import refresh_reserve_capabilities as builder

builder.PATHS = [
    'data-retrieval/src/energy_data_retrieval/wind_catalogue/catalogue.py',
    'data-retrieval/src/energy_data_retrieval/sources/elexon/client.py',
    'methods/src/energy_methods/offshore_wind_economics.py',
    'data-retrieval/pyproject.toml',
    'LICENSE',
]

if __name__ == '__main__':
    builder.main()

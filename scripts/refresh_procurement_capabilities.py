"""Refresh the bounded EDI context catalogue with the existing committed-blob builder."""
import refresh_reserve_capabilities as builder

builder.PATHS = [
    'data-retrieval/src/energy_data_retrieval/wind_catalogue/catalogue.py',
    'data-retrieval/src/energy_data_retrieval/wind_catalogue/grid_connections.py',
    'methods/src/energy_methods/offshore_wind_economics.py',
    'data-retrieval/pyproject.toml',
    'LICENSE',
]

if __name__ == '__main__':
    builder.main()

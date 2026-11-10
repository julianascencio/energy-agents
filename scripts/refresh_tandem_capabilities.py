"""Rebuild the focused tandem capability catalogue from committed EDI source."""
import refresh_reserve_capabilities as builder

builder.PATHS = [
    'methods/src/energy_methods/pv_repowering.py',
    'methods/src/energy_methods/pv_lifetime.py',
    'methods/src/energy_methods/pv_operation.py',
    'methods/pyproject.toml', 'LICENSE',
]

if __name__ == '__main__':
    builder.main()

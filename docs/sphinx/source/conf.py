from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
project = "Energy Agents"
author = "ASVA Consulting"
release = "0.1.0"
copyright = "2026, ASVA Consulting"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_gallery.gen_gallery",
]
html_theme = "pydata_sphinx_theme"
html_title = "Energy Agents"
html_static_path = ["_static"]
html_css_files = ["energy-agents.css"]
html_theme_options = {
    "github_url": "https://github.com/julianascencio/energy-agents",
    "navbar_align": "left",
    "show_toc_level": 2,
    "show_prev_next": False,
}
sphinx_gallery_conf = {
    "examples_dirs": str(ROOT / "examples"),
    "gallery_dirs": "gallery",
    "filename_pattern": r"/plot_",
    "download_all_examples": False,
    "abort_on_example_error": True,
}


def _build_operations_demo(app):
    from energy_agents.operations import synthetic_portfolio
    from energy_agents.operations.__main__ import export_review

    export_review(synthetic_portfolio(), Path(app.srcdir) / "_static" / "operations")


def setup(app):
    app.connect("builder-inited", _build_operations_demo)

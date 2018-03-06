# How to build
To build the documentation in this repository, you need `python`, `mkdocs` and `pymdown-extensions` (for LaTeX support).

The file `render_templates.py` renders files ending in `.md.j2` in the `docs/` folder and injects info on the current tags in
core from the GitLab API: this is used to build the releases page. 

To build the doc, you need to install mkdocs and some dependencies like so:

```
pip install mkdocs pymdown-extensions iso8601 jinja2 requests
```

then run the `render_templates.py` and subsequently `mkdocs build` (or `mkdocs serve`).


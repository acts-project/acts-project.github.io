# How to build
To build the documentation in this repository, you need `python`, `mkdocs` and `pymdown-extensions` (for LaTeX support).

To build the doc, you need to install mkdocs and some dependencies like so:

```
pip install mkdocs pymdown-extensions iso8601 jinja2 requests
```

A `mkdocs` plugin lives in `mkdocs_jinja_plugin`, which fetches dynamic data from external sources and provides it to the
markdown pages. You can therefore use [Jinja2 syntax](http://jinja.pocoo.org/docs/) in the markdown files to render this data. This is used for 
the Releases, Authors, Contributions and License pages.

The plugin needs to be activated by 
```
cd mkdocs_jinja_plugin && python setup.py install
```

This should make the plugin available to `mkdocs`.
Then run `mkdocs build` (or `mkdocs serve`) to build the site.


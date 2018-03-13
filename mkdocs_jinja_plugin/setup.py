from setuptools import setup, find_packages

setup(
    name='mkdocs-jinja-plugin',
    version='1.0',
    description='',
    author='Paul Gessinger',
    author_email='paul.gessinger@cern.ch',
    packages=["mkdocs_jinja_plugin"],
    entry_points={
        'mkdocs.plugins': [
            'jinja = mkdocs_jinja_plugin.plugin:JinjaPlugin'
        ]
    }
)


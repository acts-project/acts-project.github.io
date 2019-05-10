from __future__ import print_function

from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
from mkdocs import utils as mkdocs_utils
import mkdocs

import requests
from urllib.parse import urljoin, quote, urlparse, urlunparse
from datetime import datetime
import iso8601
from glob import glob
import os
import re
import logging
import gitlab
import concurrent.futures as cf
import copy

import jinja2 as j2

logger = logging.getLogger("jinja-plugin")

def get_tags(project):
    return project.tags.list(all=True)


def get_url_src(url):
    res = requests.get(url)
    return res.content.decode("utf-8")



class JinjaPlugin(BasePlugin):

    config_scheme = (
        ("gitlab_url", config_options.Type(mkdocs_utils.string_types)),
        ("repo", config_options.Type(mkdocs_utils.string_types)),
        ("url_imports", config_options.Type(dict, default={})),
    )

    tpl_data = None

    def __init__(self, *args, **kwargs):
        parent_logger = logging.getLogger("mkdocs")
        parent_logger_level = parent_logger.getEffectiveLevel()
        FORMAT = '%(asctime)-15s %(levelname)s - %(threadName)s: %(message)s'
        logging.basicConfig(level=parent_logger_level, format=FORMAT)


        logger.debug("init")

        self.env = j2.Environment()

        self.env.filters["as_datetime"] = lambda v, f: datetime.strptime(v, f)
        self.env.filters["iso8601"] = lambda v: iso8601.parse_date(v)
        self.env.filters["datetime_format"] = lambda v, f: v.strftime(f)

    # def on_serve(self, server, config):
        # JinjaPlugin.is_serve = True

    def _load_data(self, config):
        if JinjaPlugin.tpl_data is not None:
            return


        base_url = self.config["gitlab_url"]

        gl = gitlab.Gitlab(base_url)
        project = gl.projects.get(3031) # acts/acts-core

        with cf.ThreadPoolExecutor(max_workers=10) as tp:

            ft_tags = tp.submit(get_tags, project)

            JinjaPlugin.tpl_data = {
                "url_imports": {}
            }

            url_import_futures = {}


            for key, url in self.config["url_imports"].items():
                f = tp.submit(_handle_url_import, url, config["site_dir"])
                url_import_futures[key] = f

            # cf.wait(url_import_futures.values())

            for key, f in url_import_futures.items():
                md = f.result()
                self.tpl_data["url_imports"][key] = md
                
                
            JinjaPlugin.tpl_data["tags"] = ft_tags.result()


    def on_page_markdown(self, md, page, config, files):
        self._load_data(config)
        tpl_data = {}
        tpl = self.env.from_string(md)
        tpl_data.update(JinjaPlugin.tpl_data)
        output = tpl.render(**tpl_data)
        return output

def _handle_url_import(url, site_dir):
    logger.info("importing URL from %s", url)
    md = get_url_src(url)
    if url.endswith(".md"):
        md = _process_md_url_import(url, md, site_dir)
    logger.info("done importing URL from %s", url)
    return md

def _process_md_url_import(url, md, site_dir):
    logger.debug("processing md import")
    md_img_ex = r"!\[(?:.*?)\]\((.*?)\)"
    html_img_ex = r"<img.*src=\"(.*?)\".*>"
    
    url_parsed = urlparse(url)
    url_path_base = os.path.dirname(url_parsed.path)

    urls = []
    def repl(m):
        url = m.group(1)

        # only relative urls
        if bool(urlparse(url).netloc): return m.group(0)
        # target = os.path.join("figures", url.replace("/", "_"))

        target = "{}://{}/".format(url_parsed.scheme, url_parsed.netloc) +os.path.join(url_path_base, url)
        logger.debug("Rewrite image: %s => %s", url, target)
        

        urls.append((url, target))

        return "![]({})".format(target)

    md = re.sub(md_img_ex, repl, md)
    md = re.sub(html_img_ex, repl, md)
    
    logger.debug("Found %d images that need to be imported", len(urls))



    logger.debug("done processing md import")
    return md

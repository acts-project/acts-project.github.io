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

import jinja2 as j2

def get_tags(project, base_url):
    slug = quote(project, safe="")
    url = urljoin(base_url, "projects/"+slug+"/repository/tags")
    res = requests.get(url, params={})
    data = res.json()
    return data

def get_contributors(project, base_url, email_map, name_map, excludes, commit_threshold):
    slug = quote(project, safe="")
    url = urljoin(base_url, "projects/"+slug+"/repository/contributors")
    res = requests.get(url, params={})
    data = res.json()

    contrib_map = {}

    for contributor in data:
        email = contributor["email"]
        if email in excludes: continue
        contrib_map[email] = contributor
        if email in name_map:
            contrib_map[email]["name"] = name_map[email]
    
    remove = []

    for email, contributor in contrib_map.items():
        email = contributor["email"]
        if email in email_map:
            commits = contrib_map[email]["commits"]
            canonical_email = email_map[email]
            contrib_map[canonical_email]["commits"] += commits
            remove.append(email)


    for email in remove:
        del contrib_map[email]

    contrib_map = {k: v for k, v in contrib_map.items() if v["commits"] > commit_threshold}

    output = list(contrib_map.values())
    output = list(reversed(sorted(output, key=lambda c: c["commits"])))
    return output

def get_url_src(url):
    res = requests.get(url)
    return res.content.decode("utf-8")

class SiteNavigation(mkdocs.nav.SiteNavigation):
    def walk_pages(self):
        """
        Returns each page in the site in turn.
        Additionally this sets the active status of the pages and headers,
        in the site navigation, so that the rendered navbar can correctly
        highlight the currently active page and/or header item.
        """
        page = self.homepage
        page.set_active()
        self.url_context.set_current_url(page.abs_url)
        self.file_context.set_current_path(page.input_path)
        yield page
        while page.next_page:
            page.set_active(False)
            page = page.next_page
            if page.is_external: continue
            page.set_active()
            self.url_context.set_current_url(page.abs_url)
            self.file_context.set_current_path(page.input_path)
            yield page
        page.set_active(False)


# we need to do some monkey patching
def decorate_normpath(_normpath):
    def normpath(path):
        # check if is url
        if urlparse(path).scheme != "":
            return path
        return _normpath(path)
    return normpath
os.path.normpath = decorate_normpath(os.path.normpath)

def decorate_page(Page_):
    class Page(Page_):
        def __init__(self, title, path, url_context, config):
            # print("page init", path)
            self.is_external = urlparse(path).scheme != ""
            # print(self.is_external)
            self._url = path
            super().__init__(title, path, url_context, config)

        def indent_print(self, depth=0):
            indent = '    ' * depth
            active_marker = ' [*]' if self.active else ''
            title = self.title if (self.title is not None) else '[blank]'
            url = self.abs_url if not self.is_external else self._url
            return '%s%s - %s%s\n' % (indent, title, url, active_marker)

        @mkdocs.nav.Page.url.getter
        def url(self):
            # print("get my url", self._url)
            if self.is_external:
                return self._url
            else:
                # default behaviour
                return self.url_context.make_relative(self.abs_url)
    return Page
mkdocs.nav.Page = decorate_page(mkdocs.nav.Page)




class JinjaPlugin(BasePlugin):

    config_scheme = (
        ('gitlab_url', config_options.Type(mkdocs_utils.string_types)),
        ('repo', config_options.Type(mkdocs_utils.string_types)),
        ('url_imports', config_options.Type(dict, default={})),
        ('contributor_email_map', config_options.Type(dict, default={})),
        ('contributor_name_map', config_options.Type(dict, default={})),
        ('contributor_exclude', config_options.Type(list, default={})),
        ('contributor_commit_threshold', config_options.Type(int, default=15))
    )

    tpl_data = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.env = j2.Environment()

        self.env.filters["as_datetime"] = lambda v, f: datetime.strptime(v, f)
        self.env.filters["iso8601"] = lambda v: iso8601.parse_date(v)
        self.env.filters["datetime_format"] = lambda v, f: v.strftime(f)

    def _load_data(self, config):
        if self.tpl_data is not None:
            return

        base_url = self.config["gitlab_url"]

        name_map = self.config["contributor_name_map"]
        email_map = self.config["contributor_email_map"]
        excludes = self.config["contributor_exclude"]

        commit_threshold = self.config["contributor_commit_threshold"]
        contributors = get_contributors("acts/acts-core", base_url, email_map, name_map, excludes, commit_threshold)

        self.tpl_data = {
            "tags": get_tags("acts/acts-core", base_url),
            "contributors": contributors,
            "url_imports": {}
        }

        for key, url in self.config["url_imports"].items():
            print("importing URL from", url)
            md = get_url_src(url)
            if url.endswith(".md"):
                md = self._process_md_url_import(url, md, config["site_dir"])
            self.tpl_data["url_imports"][key] = md

    def _process_md_url_import(self, url, md, site_dir):
        md_img_ex = r"!\[(?:.*?)\]\((.*?)\)"
        html_img_ex = r"<img.*src=\"(.*?)\".*>"

        # md_m = re.findall(md_img_ex, md)
        # html_m = re.findall(html_img_ex, md)

        urls = []
        def repl(m):
            url = m.group(1)
            # print(m.group(0), url)

            # only relative urls
            if bool(urlparse(url).netloc): return m.group(0)
            slug = os.path.join("figures", url.replace("/", "_"))

            urls.append((url, slug))

            return "![]({})".format(slug)

        md = re.sub(md_img_ex, repl, md)
        md = re.sub(html_img_ex, repl, md)

        url_parsed = urlparse(url)
        url_path_base = os.path.dirname(url_parsed.path)
        for src, dest in urls:
            full_url = os.path.join(url_path_base, src)
            url_parts = list(url_parsed)
            url_parts[2] = full_url
            img_url = urlunparse(tuple(url_parts))

            dest_path = os.path.join(site_dir, dest)
            if os.path.exists(dest_path): continue

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            print("downloading", img_url, "=>", dest)
            r = requests.get(img_url, stream=True)
            if r.status_code == 200:
                with open(dest_path, 'wb') as f:
                    for chunk in r:
                        f.write(chunk)
            else:
                print(r.status_code, r.content)


        return md

    def on_page_markdown(self, md, page, config, site_navigation):
        self._load_data(config)
        # print(md)
        tpl = self.env.from_string(md)
        output = tpl.render(**self.tpl_data)
        return output
    def on_nav(self, site_navigation, config, **kwargs):
        # config_copy = config
        # config_copy["pages"] = self._pages
        # sn = SiteNavigation(config)
        # print(sn)
        return SiteNavigation(config)


#!/usr/bin/env python
from __future__ import print_function
import requests
from urllib.parse import urljoin, quote
from datetime import datetime
import iso8601
from glob import glob
import os

import jinja2 as j2

TOKEN = "PJdUKWtTSNLzNzWW6cgy"
BASE_URL = "https://gitlab.cern.ch/api/v4/"

def get_tags(project):
    slug = quote(project, safe="")
    url = urljoin(BASE_URL, "projects/"+slug+"/repository/tags")
    res = requests.get(url, params={})
    data = res.json()
    return data


def main():
    tags = get_tags("acts/acts-core")

    env = j2.Environment(
        loader=j2.FileSystemLoader("docs"),
        autoescape=j2.select_autoescape(["html", "xml"])
    )

    env.filters["as_datetime"] = lambda v, f: datetime.strptime(v, f)
    env.filters["iso8601"] = lambda v: iso8601.parse_date(v)
    env.filters["datetime_format"] = lambda v, f: v.strftime(f)

    print("Rendering all *.md.j2 files found in docs/")

    j2files = glob(os.path.join("docs", "**/*.md.j2"), recursive=True)
    for tplfile in j2files:
        bn = os.path.basename(tplfile).split(".", 1)[0]
        tplname = os.path.join(*(tplfile.split("/")[1:]))
        tpl = env.get_template(tplname)
        md = tpl.render(tags=tags)
        outfile = os.path.join("docs", bn+".md")
        with open(outfile, "w+") as f:
            f.write(md)
        print(tplname, "=>", outfile)



if "__main__" == __name__:
    main()

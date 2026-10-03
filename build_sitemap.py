#!/usr/bin/env python3
"""One sitemap, built from the files that actually exist.

Two generators each writing their own sitemap means whichever runs last wins
and silently drops the other's pages. This walks the directory instead, so a
page cannot be live and missing from the sitemap at the same time."""

import os
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://jaakoby.github.io"
SKIP = {"_style.html", "404.html"}


def urls():
    found = ["%s/" % SITE]
    for d in ("fix", "guides"):
        path = os.path.join(HERE, d)
        if not os.path.isdir(path):
            continue
        found.append("%s/%s/" % (SITE, d))
        for f in sorted(os.listdir(path)):
            if f.endswith(".html") and f not in SKIP and f != "index.html":
                found.append("%s/%s/%s" % (SITE, d, f))
    return found


def main():
    today = date.today().isoformat()
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls():
        pri = "1.0" if u == "%s/" % SITE else ("0.9" if u.endswith("/") else "0.8")
        out.append("  <url><loc>%s</loc><lastmod>%s</lastmod>"
                   "<priority>%s</priority></url>" % (u, today, pri))
    out.append("</urlset>")
    with open(os.path.join(HERE, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print("%d urls" % len(urls()))


if __name__ == "__main__":
    main()

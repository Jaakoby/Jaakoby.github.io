#!/usr/bin/env python3
"""Generate one page per failure mode, titled with the string people search.

The sales page contained ZERO literal error strings, so it could never appear
for the query its buyer actually types. Someone whose server just died pastes
the exception into Google -- that is the moment of maximum intent, and nothing
we had published could meet it. The dev.to article had the same problem from
the other side: tagged python/testing/debugging/regex, it reached developers who
appreciate the craft rather than people who run modded servers. 32 views, 0 sales.

Content comes from forge_doctor's own rule table -- the same root causes and
fixes the paid tool prints -- so these pages are the real answer, not bait. If
someone solves their crash from the page and never buys, that is a fair trade
and the honest version of this.

    python3 make_errorpages.py        # writes fix/*.html and sitemap.xml
"""

import html
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/mnt/e/ForgeServerDoctor")
import forge_doctor as fd  # noqa: E402

SITE = "https://jaakoby.github.io"
OUT = os.path.join(HERE, "fix")

# The literal string a person pastes into a search box, per rule. Derived from
# each rule's own patterns, then cleaned by hand -- a regex is not a search
# query, and this is the single thing each page has to get right.
QUERY = {
    "client-class-on-server": "Attempted to load class for invalid dist DEDICATED_SERVER",
    "client-only-mod": "mod has been loaded on the wrong server side",
    "missing-dependency": "Missing or unsupported mandatory dependencies Minecraft server",
    "duplicate-mods": "Found duplicate mods Forge server",
    "mixin-failure": "Mixin apply failed InvalidInjectionException",
    "world-lock": "Failed to check session lock minecraft server",
    "java-version": "UnsupportedClassVersionError class file version Minecraft",
    "out-of-memory": "java.lang.OutOfMemoryError Java heap space Minecraft server",
    "port-in-use": "java.net.BindException Address already in use Minecraft",
    "eula": "You need to agree to the EULA in order to run the server",
    "static-init": "java.lang.ExceptionInInitializerError Minecraft mod",
    "registry-remap": "Unknown registry entries Minecraft world",
    "loader-version": "mod is for mod loader which is not compatible",
    "watchdog": "A single server tick took 60.00 seconds ThreadStuckError",
    "nosuchmethod": "java.lang.NoSuchMethodError Minecraft mod",
    "config-crash": "ConfigLoadingException Forge server",
    "mod-rejections": "Mod rejections connection closed Minecraft",
    "datapack-recipe": "Couldn't parse data file recipe Minecraft",
    "own-class-missing": "NoClassDefFoundError Minecraft mod stale jar",
    "bad-resource-location": "ResourceLocationException Non [a-z0-9_.-] character in path",
    "ticking-entity-mod-bug": "Ticking entity crash Minecraft server mod",
    "mod-loading-wrapper": "java.lang.Exception Mod Loading has failed",
    "server-init-wrapper": "IllegalStateException Failed to initialize server Minecraft",
    "missing-mod-file": "is not a valid mod file Forge",
}

NAV = ('<p class="eyebrow"><a href="/">Forge Server Tools</a> · '
       '<a href="/fix/">every failure mode</a></p>')

# The free edition ships only these six. Pages for the other eighteen must NOT
# imply it will find their problem -- sending someone to a tool that cannot
# detect the thing they just searched for is how you lose them permanently.
FREE_IDS = {"eula", "port-in-use", "java-version", "out-of-memory",
            "world-lock", "duplicate-mods"}


def readable(pattern):
    """The literal text a human will actually see, pulled out of a regex.

    Decompiling the whole pattern does not work -- the first attempt turned
    `org\\.spongepowered\\.asm\\.mixin\\.(?:injection\\.)?throwables\\.\\w+` into
    "org.spongepowered.asm.mixin.:injection.throwables.w", which is worse than
    showing nothing. So take only the runs of plain literal characters and drop
    everything structural; a server admin searching their log needs a string
    they can paste, not a translation of the pattern."""
    out, buf = [], []
    i, n = 0, len(pattern)
    while i < n:
        c = pattern[i]
        if c == "\\" and i + 1 < n:
            nxt = pattern[i + 1]
            if nxt in ".-/: ":          # an escaped literal
                buf.append(nxt)
            else:                        # \w \s \S \d ... -- structural
                out.append("".join(buf)); buf = []
            i += 2
            continue
        if c in "[(":                    # skip the whole group or class
            depth, close = 1, {"[": "]", "(": ")"}[c]
            out.append("".join(buf)); buf = []
            i += 1
            while i < n and depth:
                if pattern[i] == "\\":
                    i += 2
                    continue
                if pattern[i] == c:
                    depth += 1
                elif pattern[i] == close:
                    depth -= 1
                i += 1
            continue
        if c in "{":
            out.append("".join(buf)); buf = []
            i = pattern.find("}", i) + 1 or n
            continue
        if c in "^$*+?|":
            out.append("".join(buf)); buf = []
            i += 1
            continue
        if c == ".":                     # unescaped dot = any char
            out.append("".join(buf)); buf = []
            i += 1
            continue
        buf.append(c)
        i += 1
    out.append("".join(buf))

    frags = [f.strip() for f in out if len(f.strip()) >= 6]
    return "  ...  ".join(frags) if frags else ""


def esc(t):
    return html.escape(t or "", quote=False)


def para(text):
    """Rule text is wrapped plain text; keep its line breaks where they are
    deliberate (lists) and join them where they are only wrapping."""
    out = []
    for block in re.split(r"\n\s*\n", (text or "").strip()):
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if sum(1 for l in lines if re.match(r"^(If |Watch |[-*\d])", l)) >= 2:
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % esc(l) for l in lines))
        else:
            out.append("<p>%s</p>" % esc(" ".join(lines)))
    return "\n".join(out)


def page(rule, css, query):
    title = "%s — what it means and how to fix it" % query
    desc = re.sub(r"\s+", " ", (rule.root_cause or rule.title))[:155]
    url = "%s/fix/%s.html" % (SITE, rule.id)
    sev = {"FATAL": "fatal", "ERROR": "warn", "WARN": "warn"}.get(rule.severity, "warn")

    if rule.id in FREE_IDS:
        cta = ("""<p>The free edition of Forge Server Doctor detects this one. It is a
  single Python file with no dependencies — point it at the report and it names
  the cause and the mod jar:</p>
  <div class="fixpre"><pre>python3 forge_doctor.py crash-reports/crash-....txt</pre></div>
  <div class="btnrow">
    <a class="btn" href="https://github.com/Jaakoby/forge-server-doctor">Free edition on GitHub</a>
  </div>""")
    else:
        cta = ("""<p>The free edition covers the six most common startup failures, and this
  is not one of them — it is in the paid tool, which checks all 24 and names the
  mod jar from the stack trace. The fix above is the same one it prints, so you
  do not need it to solve this.</p>
  <div class="btnrow">
    <a class="btn ghost" href="https://github.com/Jaakoby/forge-server-doctor">Free edition (6 checks)</a>
    <a class="btn" href="/#tools">All 24 checks</a>
  </div>""")

    # Schema.org so the answer can surface directly in search results.
    faq = (
        '<script type="application/ld+json">'
        '{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{'
        '"@type":"Question","name":%s,'
        '"acceptedAnswer":{"@type":"Answer","text":%s}}]}'
        "</script>"
    ) % (_json(query), _json(re.sub(r"\s+", " ", (rule.root_cause or "") + " " + (rule.fix or ""))[:900]))

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<link rel="icon" href="/img/icon.png">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(query)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/img/forge-server-doctor.png">
<meta name="twitter:card" content="summary_large_image">
{faq}
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;900&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
{css}
</head>
<body>
<div class="wrap fixbody">

<header class="top">
  {NAV}
  <h1>{esc(query)}</h1>
  <p class="deck">{esc(rule.title)} — <span class="sev {sev}">{esc(rule.severity)}</span></p>
</header>

<section>
  <h2>What this actually means</h2>
  {para(rule.root_cause)}
</section>

<section>
  <h2>How to fix it</h2>
  {para(rule.fix)}
</section>

<section>
  <h2>What it looks like in your log</h2>
  <p>Search your crash report or <code>latest.log</code> for any of these:</p>
  <div class="fixpre"><pre>{esc(chr(10).join(filter(None, (readable(p) for p in rule.patterns))))}</pre></div>
  {cta}
</section>

<footer>
  <p>Forge Server Tools — diagnostic aids, not authorities. Verify any diagnosis before acting on it, and keep a backup of your world.</p>
  <p>Not affiliated with Mojang, Microsoft, MinecraftForge or NeoForged. Minecraft is a trademark of Mojang AB.</p>
</footer>

</div>
</body>
</html>
"""


def _json(s):
    import json
    return json.dumps(s)


def index_page(rules, css):
    items = "\n".join(
        '<li><a href="/fix/%s.html">%s</a><span class="muted"> — %s</span></li>'
        % (r.id, esc(QUERY[r.id]), esc(r.title)) for r in rules)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Every way a modded Minecraft server dies, and the fix for each</title>
<meta name="description" content="24 failure modes for Forge and NeoForge dedicated servers, each with what it means and how to fix it. Crash reports, mixins, dependencies, memory, world locks.">
<link rel="canonical" href="{SITE}/fix/">
<link rel="icon" href="/img/icon.png">
<meta property="og:type" content="website">
<meta property="og:title" content="Every way a modded Minecraft server dies">
<meta property="og:description" content="24 failure modes for Forge and NeoForge dedicated servers, each with what it means and how to fix it.">
<meta property="og:url" content="{SITE}/fix/">
<meta property="og:image" content="{SITE}/img/forge-server-doctor.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;900&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
{css}
</head>
<body>
<div class="wrap">
<header class="top">
  <p class="eyebrow"><a href="/">Forge Server Tools</a></p>
  <h1>Every way a modded server dies</h1>
  <p class="deck">24 failure modes, each with what it means and the fix. Same
  root causes and remedies the tool prints — find yours below.</p>
</header>
<section><ul class="fixlist">
{items}
</ul></section>
<footer>
  <p>Not affiliated with Mojang, Microsoft, MinecraftForge or NeoForged.</p>
</footer>
</div>
</body>
</html>
"""


def main():
    css = open(os.path.join(HERE, "_style.html"), encoding="utf-8").read()
    os.makedirs(OUT, exist_ok=True)
    missing = [r.id for r in fd.RULES if r.id not in QUERY]
    if missing:
        raise SystemExit("no search query written for: %s" % missing)

    written = []
    for r in fd.RULES:
        p = os.path.join(OUT, "%s.html" % r.id)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(page(r, css, QUERY[r.id]))
        written.append(r)
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(index_page(written, css))

    today = date.today().isoformat()
    urls = ["%s/" % SITE, "%s/fix/" % SITE] + \
           ["%s/fix/%s.html" % (SITE, r.id) for r in written]
    with open(os.path.join(HERE, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in urls:
            pri = "1.0" if u.endswith("io/") else "0.8"
            fh.write("  <url><loc>%s</loc><lastmod>%s</lastmod>"
                     "<priority>%s</priority></url>\n" % (u, today, pri))
        fh.write("</urlset>\n")

    print("%d pages + index, %d sitemap urls" % (len(written), len(urls)))


if __name__ == "__main__":
    main()

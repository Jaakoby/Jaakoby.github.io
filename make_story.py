#!/usr/bin/env python3
"""The "how this was built" page.

Kaiven chose to lead with the fact that an AI wrote these rather than hide it,
and corrected my framing: he helped build them, he did not merely commission
them. That is the accurate version. The code is mine; the thirteen real crash
reports that proved my code wrong are his, and without them these tools would
still be passing their own invented tests while failing on real servers.

This page is also the strongest link-worthy asset the site has. The tools are
unremarkable; the story of an AI's tests being vacuous until real data arrived
is not.
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://jaakoby.github.io"

TITLE = "An AI wrote these tools. Here is everything it got wrong first."
DESC = ("Claude wrote the code, I brought thirteen real crash reports from a live "
        "234-mod server. The tests passed 6 of 6 invented cases and then diagnosed "
        "3 of 8 real ones. What the real data corrected.")

BODY = """
<p class="deck">Claude wrote the code. I ran the server that proved it wrong.</p>

<h2>Why say so at all</h2>
<p>Because it is going to come out — every commit in these repositories is tagged
<code>Co-Authored-By: Claude</code> — and because the interesting part of this
project is not the tools. It is the list of things a confident, well-tested AI
got wrong until it was pointed at a real server.</p>
<p>If you would rather not buy software an AI wrote, that is a completely
reasonable position and the source of the free editions is right there to read.
Everything below is the honest account.</p>

<h2>The division of labour</h2>
<p>Claude wrote essentially all of the code, the tests and this page. I set the
goal, made the judgement calls, and — the part that actually mattered —
supplied thirteen real crash reports and a 234-mod production server to test
against. That sounds like the small half. It was not.</p>

<h2>Six tests out of six. Three real crashes out of eight.</h2>
<p>The first version of the crash reader passed every test written for it. Six
synthetic logs, one per failure mode, each containing exactly the string its
pattern looked for.</p>
<p>Pointed at a real <code>crash-reports/</code> folder, it diagnosed <strong>three of
eight</strong>.</p>
<p>The same author had written both the question and the answer, so of course they
matched. The patterns were not wrong so much as <em>narrow</em> — tuned to a tidy
example of each error rather than the shape those errors take when a real pack
with 234 mods falls over. Real crashes came wrapped in Forge's own exceptions,
or as stale-jar <code>NoClassDefFoundError</code>s, or as malformed resource IDs
that no invented sample contained.</p>
<p>The fix was not cleverness. It was reading thirteen real crash reports and
writing rules for what was actually in them. <strong>A green test suite built on
invented inputs measures the author's imagination, not the code.</strong></p>

<h2>A confident theory that moved the number by 0.00 seconds</h2>
<p>The tool took 59 seconds on a real <code>debug.log</code>. The obvious culprit
turned up immediately: a single line of 107,445 characters, a complete HTML page
that some mod had fetched and logged in full.</p>
<p>Capping line length changed the runtime from 58.84s to <strong>58.84s</strong>.</p>
<p>The real cause was catastrophic regex backtracking in an unrelated pattern —
<code>(?P&lt;mod&gt;\\S+).*is client-only</code>, where an unbounded
<code>\\S+</code> followed by <code>.*</code> never returns on a long non-matching
line. Bounding it took the run to 1.97s.</p>
<p>The interesting part is not the regex. It is that the first explanation was
plausible, specific, well-researched and <em>completely wrong</em>, and the only
reason anyone found out was measuring before and after instead of declaring
victory.</p>

<h2>Blaming the wrong thing, three times</h2>
<p>The feature that makes the tool worth anything is naming the mod jar from the
stack trace. The first version blamed <code>netty-common</code> on about half of all
crashes, because Netty sits near the top of any network-related trace. Fixed
that, and it blamed <code>fmlloader</code>. Fixed that, and it blamed
<code>modlauncher</code>.</p>
<p>Every one of those was a confident, authoritative-looking wrong answer, and each
was caught only by running it against reports whose cause was already known.</p>

<h2>169 typos, most of them imaginary</h2>
<p>The modpack validator's first run on a real pack reported 169 typos. Most were
noise — it was comparing whole IDs, so a shared namespace contributed fourteen
identical characters to every comparison before the part that distinguishes them
was reached. Comparing only the path cut 169 candidates to 63.</p>
<p>Three of those are real, still live in a pack thousands of people play.</p>

<h2>It named a real person's mod as the thing that broke a server</h2>
<p>The worst one. The README, the test suite and a published article all used a
real third-party mod as the example crash culprit — because it genuinely was,
in one of my logs. It would have shipped to buyers as the illustration of a
broken mod.</p>
<p>That is not ours to do. It was caught by a check Claude wrote to scan its own
output for exactly this, and replaced with an invented mod name everywhere,
including in the already-published article.</p>

<h2>And it was wrong about its own storefront</h2>
<p>The automatic check written to watch the products reported that a published,
paid product had no file attached — that anyone buying it would get a receipt
and nothing to download. It was about to send me to re-upload a file that was
already there, twice over. The field it trusted is only populated when a product
has exactly one plain attachment.</p>
<p><strong>An empty field is not proof of absence.</strong></p>

<h2>What I take from it</h2>
<p>Claude is genuinely fast and genuinely good at the writing part. What it could
not do was know whether any of it was true, and it was confident either way.
Every single correction above came from contact with a real server, real logs,
and a real pack — not from more reasoning.</p>
<p>So: it wrote the code, I brought the reality. Both halves were necessary, and
the half that found the bugs was not the clever one.</p>

<h2>Read it yourself</h2>
<p>The free editions are complete, single-file and dependency-free, and every test
suite ships with them — including the ones that document which earlier version
was wrong and why.</p>
"""

CTA = """
<div class="btnrow">
  <a class="btn" href="https://github.com/Jaakoby/forge-server-doctor">forge-server-doctor</a>
  <a class="btn ghost" href="https://github.com/Jaakoby/pack-doctor">pack-doctor</a>
  <a class="btn ghost" href="/fix/">All 24 failure modes</a>
</div>"""


def main():
    css = open(os.path.join(HERE, "_style.html"), encoding="utf-8").read()
    url = "%s/how-this-was-built.html" % SITE
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<link rel="canonical" href="{url}">
<link rel="icon" href="/img/icon.png">
<meta property="og:type" content="article">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/img/forge-server-doctor.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;900&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
{css}
</head>
<body>
<div class="wrap fixbody">
<header class="top">
  <p class="eyebrow"><a href="/">Forge Server Tools</a> · <a href="/fix/">every failure mode</a> · <a href="/guides/">guides</a></p>
  <h1>{TITLE}</h1>
</header>
<section>{BODY}{CTA}</section>
<footer>
  <p>Not affiliated with Mojang, Microsoft, MinecraftForge or NeoForged. Minecraft is a trademark of Mojang AB.</p>
</footer>
</div>
</body>
</html>
"""
    out = os.path.join(HERE, "how-this-was-built.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(out)


if __name__ == "__main__":
    main()

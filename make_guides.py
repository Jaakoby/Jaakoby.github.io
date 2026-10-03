#!/usr/bin/env python3
"""Symptom-shaped guides, for people who have no error string to paste.

The /fix/ pages answer "I have this exception". These answer "my server keeps
dying and I don't know why", which is what people search before they have
found anything specific. Higher volume, more competitive, and the queries the
hosting companies are already writing for -- which is the clearest evidence
these pages convert, since those companies spend real money on them.

Content is hand-written, not generated: these are the questions where a thin
page is worse than no page.
"""

import html
import os
import re
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://jaakoby.github.io"
OUT = os.path.join(HERE, "guides")

GUIDES = [
    {
        "slug": "which-mod-is-crashing-my-server",
        "query": "How to find which mod is crashing your Minecraft server",
        "desc": "Forge stamps every stack frame with the jar it came from. Read the trace, skip the vanilla frames, and the first mod jar left is almost always the culprit.",
        "body": """
<h2>The short answer</h2>
<p>Forge annotates <strong>every stack frame with the jar it came from</strong>. Almost
nobody outside mod development knows this, and it turns a 400-line trace into a
one-line answer.</p>
<div class="fixpre"><pre>at com.example.wildlife.procedures.StalkerProcedure.execute
   (StalkerProcedure.java:250) ~[examplemod-1.20.1-2.1.11.jar%23205!/:?]</pre></div>
<p>That <code>~[examplemod-1.20.1-2.1.11.jar...]</code> is the mod. Not the package
name — the actual file sitting in your <code>mods/</code> folder.</p>

<h2>The procedure</h2>
<p>Open the newest file in <code>crash-reports/</code>. Read the stack trace from the
top down, and find the first frame whose jar is <em>not</em> one of these:</p>
<ul>
  <li><code>server-*.jar</code>, <code>client-*.jar</code>, anything <code>minecraft</code></li>
  <li><code>forge-*</code>, <code>neoforge-*</code>, <code>fmlcore</code>, <code>fmlloader</code>,
      <code>javafmllanguage</code>, <code>modlauncher</code>, <code>securejarhandler</code>,
      <code>bootstraplauncher</code></li>
  <li><code>mixin</code>, <code>asm</code>, <code>netty-*</code>, <code>guava</code>,
      <code>gson</code>, <code>log4j</code></li>
  <li>any frame with no <code>~[...]</code> annotation at all — that is the JDK</li>
</ul>
<p>The first jar left over is your answer.</p>

<h2>Why the skip list is the whole trick</h2>
<p>This is the part that goes wrong. A naive version of this blames
<code>netty-common</code> on roughly half of all crashes, because Netty sits near the
top of any network-related trace. Filter Netty out and it starts blaming
<code>fmlloader</code>. Filter that and it blames <code>modlauncher</code>.</p>
<p>Every one of those is a confident, authoritative-looking wrong answer. <strong>If
something tells you a Forge internal killed your server, it is wrong.</strong> Forge
is in every trace; being present is not being responsible.</p>

<h2>Always read <code>Caused by:</code> first</h2>
<p>Forge wraps failures in its own exceptions. A report opening with
<code>java.lang.Exception: Mod Loading has failed</code> tells you nothing at all.
Scroll to the <em>last</em> <code>Caused by:</code> and start there. The same goes for
<code>Failed to initialize server</code> and <code>Exception in server tick loop</code> —
all three are envelopes, not causes.</p>

<h2>When there is no stack trace</h2>
<p>If the process vanished with no crash report, nothing crashed in Java — it was
killed from outside. That is almost always the OS out-of-memory killer or your
host's watchdog. Check <a href="/fix/out-of-memory.html">heap size</a> first.</p>
""",
    },
    {
        "slug": "minecraft-server-keeps-restarting",
        "query": "Minecraft server keeps crashing and restarting in a loop",
        "desc": "A server that dies the same way twice will die that way a hundred times. How to tell a repeating crash from unrelated ones, and stop the loop.",
        "body": """
<h2>What is actually happening</h2>
<p>Every hosting panel, and every <code>start.sh</code> wrapped in <code>while true</code>,
restarts a dead server. None of them notice that it is dying the <em>same way</em>
every time.</p>
<p>The usual shape: a mod crashes on a block or entity that is still in the world.
The server restarts, loads that chunk, and crashes identically. Every 40 seconds,
all night, until the disk fills with identical crash reports or your host
suspends you for the restart churn.</p>

<h2>Diagnose it in ten seconds</h2>
<div class="fixpre"><pre>ls -t crash-reports/ | head -5</pre></div>
<p>Open those five and compare their <code>Caused by:</code> lines. If they match, the
server is looping and restarting it again will not help. Stop the server, fix
the cause, <em>then</em> start it.</p>

<h2>Compare crashes, don't count them</h2>
<p>The naive guard — "stop after 5 restarts" — gets this wrong in both directions.
It stops a server that crashed five times for five unrelated reasons, and it
cheerfully allows four identical crashes first.</p>
<p>What actually works is a signature built from two things:</p>
<ul>
  <li>the root cause line (the last <code>Caused by:</code>, or the top exception),
      <strong>with every run of digits replaced</strong>;</li>
  <li>the first non-vanilla jar in the trace.</li>
</ul>
<p>The digit-stripping is not optional and it is the step everyone skips. The same
bug reports a different index, coordinate or entity id every single time it
fires — <code>Index 42</code> then <code>Index 7</code>. Without normalising those, every
crash looks unique, and a loop detector built on exact matching never fires at
all.</p>

<h2>Finding what to actually fix</h2>
<p>Crash reports name the thing being ticked when the server died:</p>
<div class="fixpre"><pre>-- Entity being ticked --
-- Block entity being ticked --</pre></div>
<p>Those sections give coordinates. Load the world in single-player, go there, and
remove it — or disable that mod's spawning in its config. See
<a href="/fix/ticking-entity-mod-bug.html">ticking entity crashes</a>.</p>
""",
    },
    {
        "slug": "minecraft-server-wont-start-no-crash-report",
        "query": "Modded Minecraft server won't start and there is no crash report",
        "desc": "No crash report means nothing crashed in Java. The process was killed from outside, or it never got far enough to write one. Where to look instead.",
        "body": """
<h2>No crash report is itself the diagnosis</h2>
<p>Minecraft writes a crash report when Java throws something it cannot recover
from. If there is no file in <code>crash-reports/</code>, one of three things
happened, and they are easy to tell apart.</p>

<h2>1. The OS killed the process</h2>
<p>The most common cause on a rented box. You asked for more heap than the machine
has, so the kernel killed the whole JVM — which cannot write a crash report
because it no longer exists.</p>
<p>Symptoms: the log simply stops mid-line. No exception, no "Stopping server".</p>
<p>Fix: lower <code>-Xmx</code> to about 75% of the machine's real RAM. The JVM needs
memory outside the heap, and your host needs some too. On Linux, confirm it with
<code>dmesg | grep -i kill</code>.</p>

<h2>2. It failed before the game loaded</h2>
<p>Forge can fail during mod discovery, before the crash-report machinery exists.
Then the answer is in <code>logs/latest.log</code> or <code>logs/debug.log</code>, not in
<code>crash-reports/</code>.</p>
<p>Look for the first <code>ERROR</code> or <code>FATAL</code> line in the file, not the last.
<strong>Causes precede effects</strong>, and one early failure produces a cascade of
noise behind it. The last error is usually a symptom of the first.</p>
<p>Common at this stage:
<a href="/fix/missing-dependency.html">missing dependencies</a>,
<a href="/fix/duplicate-mods.html">duplicate jars</a>,
<a href="/fix/java-version.html">the wrong Java version</a> and
<a href="/fix/missing-mod-file.html">a non-mod jar in mods/</a>.</p>

<h2>3. A native crash</h2>
<p>If you find an <code>hs_err_pid*.log</code> next to the server jar, the JVM itself
died — usually a graphics driver or a native library. There is no Java trace to
read. That file names the failing library.</p>

<h2>Still nothing?</h2>
<p>Check the obvious ones before going deeper:
<a href="/fix/eula.html">the EULA</a>,
<a href="/fix/port-in-use.html">the port being taken</a>, and
<a href="/fix/world-lock.html">a second server already holding the world</a>.
Each produces a clear message and no crash report.</p>
""",
    },
    {
        "slug": "how-much-ram-modded-minecraft-server",
        "query": "How much RAM a modded Minecraft server actually needs",
        "desc": "Realistic heap figures by mod count, why giving the JVM all your memory backfires, and how to tell a too-small heap from a genuine memory leak.",
        "body": """
<h2>Realistic figures</h2>
<table>
<tr><th>Pack size</th><th>Heap (<code>-Xmx</code>)</th></tr>
<tr><td>Vanilla / light (under 50 mods)</td><td>2–4 GB</td></tr>
<tr><td>Around 100 mods</td><td>6 GB</td></tr>
<tr><td>200+ mods</td><td>8–10 GB</td></tr>
<tr><td>Large kitchen-sink packs, several players</td><td>10–12 GB</td></tr>
</table>
<p>These are heap, not machine memory. The machine needs meaningfully more.</p>

<h2>Never give the JVM everything</h2>
<p>The single most common mistake: a 8 GB box with <code>-Xmx8G</code>. The JVM needs
memory <em>outside</em> the heap — metaspace, thread stacks, direct buffers, the
JIT's own code cache — and the operating system needs some to function.</p>
<p>When it runs out, the kernel kills the entire process. You get no crash report,
no exception, just a log that stops mid-sentence. See
<a href="/guides/minecraft-server-wont-start-no-crash-report.html">no crash report</a>.</p>
<p><strong>Cap <code>-Xmx</code> at roughly 75% of physical RAM.</strong></p>

<h2>Set <code>-Xms</code> equal to <code>-Xmx</code></h2>
<p>Letting the heap grow gradually causes a class of GC stall during world
generation. Setting them equal avoids it — and has the useful side effect of
failing immediately if the value is impossible, rather than an hour in.</p>

<h2>More RAM is not always the fix</h2>
<p>This is the part worth internalising. If raising the heap only <em>delays</em> the
crash, you do not have a size problem — you have a leak, and more memory buys
proportionally more time before the same ending.</p>
<p>How to tell them apart:</p>
<ul>
  <li><strong>Too small:</strong> dies under predictable load — a big base, many chunks
      loading, several players. Raising it fixes it permanently.</li>
  <li><strong>A leak:</strong> survives a restart, then dies again, at a shorter interval
      each time. Suspect anything holding entity or chunk references — mob mods,
      chunk loaders, backpacks, anything with a "nearby entities" scan.</li>
  <li><strong>A worldgen spike:</strong> dies at the same place every time, with plenty of
      headroom otherwise. Check what loaded just before.</li>
</ul>
<p>Watch heap usage across <em>hours</em>, not minutes. A leak is invisible on any
shorter scale.</p>
<p>See also <a href="/fix/out-of-memory.html">java.lang.OutOfMemoryError</a>.</p>
""",
    },
    {
        "slug": "how-to-read-a-minecraft-crash-report",
        "query": "How to read a Minecraft crash report",
        "desc": "Which four lines of a 400-line crash report actually matter, in what order to read them, and the sections most people never scroll to.",
        "body": """
<h2>Read it in this order</h2>
<p>A crash report is long and almost all of it is irrelevant. Four things matter,
and they are not at the top.</p>

<h3>1. The last <code>Caused by:</code></h3>
<p>Not the first exception — the <em>last</em> <code>Caused by:</code>. Everything above it
is wrapping. <code>Mod Loading has failed</code>, <code>Failed to initialize server</code>
and <code>Exception in server tick loop</code> are all envelopes that tell you
nothing about the actual fault.</p>

<h3>2. The first non-vanilla jar in the trace</h3>
<p>Forge tags every frame with its source jar in <code>~[...]</code>. Skip Minecraft,
Forge, the JDK and bundled libraries; the first mod jar remaining is almost
always responsible. Full method in
<a href="/guides/which-mod-is-crashing-my-server.html">finding the mod at fault</a>.</p>

<h3>3. The <code>-- being ticked --</code> sections</h3>
<p>Most people never scroll this far, and it is frequently the most actionable part
of the file:</p>
<div class="fixpre"><pre>-- Entity being ticked --
Entity Type: examplemod:stalker
Entity's Exact location: 412.50, 68.00, -1893.25</pre></div>
<p>That is the exact thing that killed your server, with coordinates. If it is
still in the world, the server will die again the moment that chunk loads.</p>

<h3>4. System Details</h3>
<p>Near the bottom. Confirms the Java version, the heap actually in use, and —
usefully — the real Forge version:</p>
<div class="fixpre"><pre>Forge: net.minecraftforge:47.4.10</pre></div>
<p>Use that line rather than the jar filename.
<code>forge-1.20.1-47.4.10-universal.jar</code> contains <em>two</em> version numbers, and
reading the first as the loader version is a mistake that looks completely
plausible — 1.20.1 is a real version string that appears everywhere in the log.</p>

<h2>What to ignore</h2>
<ul>
  <li>The joke line at the top. It is random.</li>
  <li>Mixin frames in the middle of a trace — a mixin being present does not mean
      it is at fault.</li>
  <li>Everything after the first fatal error in <code>latest.log</code>. Causes precede
      effects; a single early failure produces pages of consequences.</li>
</ul>

<h2>The whole list</h2>
<p>Every failure mode worth recognising, with its fix:
<a href="/fix/">all 24 →</a></p>
""",
    },
    {
        "slug": "players-kicked-mod-mismatch",
        "query": "Players getting kicked from a modded server for a mod mismatch",
        "desc": "Why clients bounce at Joining world, which mods must match and which must not, and how to read the rejection list.",
        "body": """
<h2>What the server is telling you</h2>
<p>Clients disconnect at "Joining world", or with a list of mods in the kick
message. Forge compares the client's registry and mod list against the
server's, and refuses anything that does not line up.</p>

<h2>The rule that resolves most of these</h2>
<p>Mods fall into three groups, and people routinely treat them as one:</p>
<ul>
  <li><strong>Client-only</strong> — shaders, minimaps, zoom, HUD and animation mods.
      These belong on clients and <em>must not</em> be on the server. Putting one
      there causes a different crash entirely; see
      <a href="/fix/client-only-mod.html">client-only mod on the server</a>.</li>
  <li><strong>Server-only</strong> — performance and management mods. Fine on the server,
      must not be required of clients.</li>
  <li><strong>Both</strong> — anything adding blocks, items, entities or recipes. These
      must match <em>exactly</em>, including version.</li>
</ul>
<p>A client-only mod is not something to "add to the server so it matches". Mark it
client-side in your pack config instead.</p>

<h2>Read the rejection list properly</h2>
<p>The kick message names what disagreed. Two patterns worth knowing:</p>
<ul>
  <li><strong>Same mod, different version</strong> — the most common cause by a wide
      margin. Someone updated one side. Versions must match exactly, not merely
      be compatible.</li>
  <li><strong>Present on one side only</strong> — decide which group above it belongs to,
      then add or remove it accordingly.</li>
</ul>

<h2>After changing the pack</h2>
<p>Everyone must have the same pack version. The usual failure is one player who
did not re-download. Bump the pack version so the launcher forces an update
rather than relying on people to do it.</p>
<p>See <a href="/fix/mod-rejections.html">the full mod-rejection write-up</a>.</p>
""",
    },
]

NAV = ('<p class="eyebrow"><a href="/">Forge Server Tools</a> · '
       '<a href="/fix/">every failure mode</a> · '
       '<a href="/guides/">guides</a></p>')

CTA = """
<section>
  <h2>Doing this automatically</h2>
  <p>Forge Server Doctor performs the whole procedure above — reads the report,
  finds the real cause under the wrappers, skips the vanilla frames, and names
  the mod jar. 24 failure modes, each with its fix. The free edition covers the
  six most common startup failures.</p>
  <div class="btnrow">
    <a class="btn" href="https://github.com/Jaakoby/forge-server-doctor">Free edition on GitHub</a>
    <a class="btn ghost" href="/#tools">All 24 checks</a>
  </div>
</section>"""


def esc(t):
    return html.escape(t or "", quote=False)


def page(g, css):
    url = "%s/guides/%s.html" % (SITE, g["slug"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(g["query"])}</title>
<meta name="description" content="{esc(g["desc"])}">
<link rel="canonical" href="{url}">
<link rel="icon" href="/img/icon.png">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(g["query"])}">
<meta property="og:description" content="{esc(g["desc"])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/img/forge-server-doctor.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;900&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
{css}
</head>
<body>
<div class="wrap fixbody">
<header class="top">
  {NAV}
  <h1>{esc(g["query"])}</h1>
  <p class="deck">{esc(g["desc"])}</p>
</header>
<section>{g["body"]}</section>
{CTA}
<footer>
  <p>Forge Server Tools — diagnostic aids, not authorities. Verify any diagnosis before acting on it, and keep a backup of your world.</p>
  <p>Not affiliated with Mojang, Microsoft, MinecraftForge or NeoForged. Minecraft is a trademark of Mojang AB.</p>
</footer>
</div>
</body>
</html>
"""


def index(css):
    items = "\n".join(
        '<li><a href="/guides/%s.html">%s</a><span class="muted"> — %s</span></li>'
        % (g["slug"], esc(g["query"]), esc(g["desc"])) for g in GUIDES)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Guides for running a modded Minecraft server</title>
<meta name="description" content="How to find which mod crashed your server, read a crash report, size your heap, stop a restart loop, and fix mod-mismatch kicks.">
<link rel="canonical" href="{SITE}/guides/">
<link rel="icon" href="/img/icon.png">
<meta property="og:type" content="website">
<meta property="og:title" content="Guides for running a modded Minecraft server">
<meta property="og:description" content="Find the mod that crashed your server, read a crash report, size your heap, stop a restart loop.">
<meta property="og:url" content="{SITE}/guides/">
<meta property="og:image" content="{SITE}/img/forge-server-doctor.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;900&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
{css}
</head>
<body>
<div class="wrap fixbody">
<header class="top">
  <p class="eyebrow"><a href="/">Forge Server Tools</a> · <a href="/fix/">every failure mode</a></p>
  <h1>Guides</h1>
  <p class="deck">The questions you search before you have an error string to paste.</p>
</header>
<section><ul class="fixlist">
{items}
</ul></section>
<footer><p>Not affiliated with Mojang, Microsoft, MinecraftForge or NeoForged.</p></footer>
</div>
</body>
</html>
"""


def main():
    css = open(os.path.join(HERE, "_style.html"), encoding="utf-8").read()
    os.makedirs(OUT, exist_ok=True)
    for g in GUIDES:
        with open(os.path.join(OUT, "%s.html" % g["slug"]), "w", encoding="utf-8") as fh:
            fh.write(page(g, css))
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(index(css))
    print("%d guides + index" % len(GUIDES))
    return [g["slug"] for g in GUIDES]


if __name__ == "__main__":
    main()

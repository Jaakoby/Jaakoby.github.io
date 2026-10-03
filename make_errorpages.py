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


# Hand-written depth per failure mode. The generated pages were 190-360 words
# with as few as 59 unique words once boilerplate was stripped -- twenty-four
# near-identical template pages, which is the shape search engines classify as
# low-value, and Google duly reported "Crawled - currently not indexed".
#
# Each entry answers the three things a generated template cannot: how to be
# sure it really is this, what it gets mistaken for, and what to do when the
# obvious fix does not work. Written per rule, because padding every page with
# the same filler would make the problem worse, not better.
DEPTH = {
    "client-class-on-server": {
        "confirm": "Search the log for <code>DEDICATED_SERVER</code>. The class named just before it will be under <code>net.minecraft.client</code>, or a mod package containing <code>client</code>, <code>render</code>, <code>gui</code> or <code>screen</code>. If the named class is not client-related, this is not your failure.",
        "confused": "Looks almost identical to a <a href=\"/fix/own-class-missing.html\">stale or partial jar</a>, which also throws <code>NoClassDefFoundError</code>. The difference is which class is missing: a vanilla client class means this; a class from the mod's own package means a bad download.",
        "next": "If removing the mod is not acceptable, check whether it publishes a separate server build, and whether the pack marks it client-side. Report it upstream with the stack trace — the author's fix is usually a one-line <code>@OnlyIn(Dist.CLIENT)</code> guard, and they cannot fix what they have not seen.",
    },
    "client-only-mod": {
        "confirm": "Check the mod page: if it lists 'client' as its only environment, this is it. Shader loaders, minimaps, zoom, HUD tweaks, animation and sound mods are the usual ones.",
        "confused": "Players then get <a href=\"/fix/mod-rejections.html\">kicked for a mod mismatch</a>, which tempts people to put it back on the server. Do not — mark it client-side in the pack instead.",
        "next": "Audit the whole folder at once rather than one crash at a time. Most packs ship a client-only list, and server hosts frequently copy the client mods folder wholesale, which produces a queue of these.",
    },
    "missing-dependency": {
        "confirm": "The log states the dependency and the version range it wants. If what you have is inside that range, the dependency is not the problem.",
        "confused": "A library that is too NEW fails identically to one that is missing. <code>[4.2.0,4.3.0)</code> excludes 4.3.0, so installing the newest release can cause the very error you are trying to fix.",
        "next": "Install exactly what the range asks for. If two mods demand incompatible versions of the same library, one of them has to go — there is no configuration that resolves it.",
    },
    "duplicate-mods": {
        "confirm": "List the folder sorted by name and look for two files sharing a mod id with different versions.",
        "confused": "Forge loads anything ending in <code>.jar</code>, so <code>mod (1).jar</code> loads and <code>mod.jar.bak</code> does not. The copy with a number in brackets is the usual culprit.",
        "next": "Keep the newer jar unless a dependency pins the older one. Check <code>.disabled</code> and backup folders too — a lot of hosting panels move rather than delete.",
    },
    "mixin-failure": {
        "confirm": "The error names the mixin's OWNER and its TARGET. The owner is the mod to act on; the target is only where the patch landed.",
        "confused": "Easy to blame the target mod, which is usually innocent. A mixin frame appearing in some unrelated trace also does not mean a mixin is at fault.",
        "next": "Update the owning mod first — these break on a version bump of the target. If both are current, check the owner's config for a compatibility toggle; many ship one specifically for this. Load order rarely helps and is worth trying only after the rest.",
    },
    "world-lock": {
        "confirm": "Look for a running java process holding the world. On Linux <code>ps aux | grep java</code>; on Windows check Task Manager for javaw.",
        "confused": "A crashed server that did not clean up looks the same as a second server genuinely running. The process list is the only way to tell.",
        "next": "Kill the process, then start. Delete <code>session.lock</code> only once you are certain nothing holds it — two servers writing one world corrupts it for real, and that is not recoverable.",
    },
    "java-version": {
        "confirm": "<code>java -version</code> on the machine, and check what your start script actually invokes — they are often different.",
        "confused": "Having the right Java installed is not the same as using it. Panels and scripts frequently pin an older JDK while the system default is current.",
        "next": "Class file 52 = Java 8, 55 = 11, 60 = 16, 61 = 17, 65 = 21. Point the script at the right JDK by full path rather than relying on <code>JAVA_HOME</code>.",
    },
    "out-of-memory": {
        "confirm": "Confirm the heap the server actually got, not what you intended. The crash report's System Details lists it.",
        "confused": "An OS kill is not this. If the log simply stops with no exception and no crash report, the kernel killed the process — <a href=\"/guides/minecraft-server-wont-start-no-crash-report.html\">different problem, opposite fix</a>: lower <code>-Xmx</code>, not raise it.",
        "next": "If more heap only delays it, you have a leak. See <a href=\"/guides/how-much-ram-modded-minecraft-server.html\">how much RAM</a> for telling the two apart.",
    },
    "port-in-use": {
        "confirm": "<code>ss -ltnp | grep 25565</code> on Linux, or <code>netstat -ano | findstr 25565</code> on Windows, names the process holding it.",
        "confused": "Voice-chat mods bind their own port and produce the identical error with a different number. Read which port the message names before assuming it is 25565.",
        "next": "Either stop the other process or change <code>server-port</code>. If the holder is a crashed server, it may take a moment to release.",
    },
    "eula": {
        "confirm": "Open <code>eula.txt</code> beside the server jar. It will say <code>eula=false</code>.",
        "confused": "Some panels keep their own copy, so editing the file you found may not be the one the server reads. If it reverts, you edited the wrong one.",
        "next": "Set <code>eula=true</code> and start again. Nothing else causes this.",
    },
    "static-init": {
        "confirm": "The frame directly above the error names the class. Its mod is the one to look at, and the cause is usually a config value it read at load.",
        "confused": "Reads like a crash in the mod's logic, but it fires before any of that runs — the class never finished loading.",
        "next": "Back up, then delete that mod's config to regenerate defaults. If it still fails, the jar may be wrong for your Minecraft version.",
    },
    "registry-remap": {
        "confirm": "The prompt lists the missing entries and their namespaces, which tells you exactly which mod left.",
        "confused": "Accepting the loss looks like a fix because the world then loads. It is not reversible — those blocks and items are gone.",
        "next": "Put the mod back and <a href=\"/guides/removing-a-mod-from-an-existing-world.html\">remove it properly</a>. Back up the world first, every time.",
    },
    "loader-version": {
        "confirm": "Read <code>Forge: net.minecraftforge:…</code> in the crash report's System Details, not the jar filename — <code>forge-1.20.1-47.4.10-universal.jar</code> contains two version numbers and the first one is Minecraft's.",
        "confused": "Forge and NeoForge are not interchangeable from 1.20.2 onward, whatever a filename suggests.",
        "next": "Match the mod to the loader the log reports. If the mod has no build for your loader, there is no workaround.",
    },
    "watchdog": {
        "confirm": "The watchdog dumps the stack of the thread that was stuck. That trace is a real diagnosis, not a symptom — read it the way you would any crash.",
        "confused": "Treated as a performance problem, so people raise the limit. The limit is not what broke.",
        "next": "Fix the mod the trace names. Raising <code>max-tick-time</code> hides it; setting it to <code>-1</code> turns a crash into a server nobody can even disconnect from. See <a href=\"/guides/cant-keep-up-is-the-server-overloaded.html\">lag vs. a real stall</a>.",
    },
    "nosuchmethod": {
        "confirm": "The message names the method that no longer exists; the top frame names who called it. The caller is the mod with the stale expectation.",
        "confused": "Both mods load fine, so it looks fine until that code path runs — often hours in, which makes it read like a random crash.",
        "next": "Update the calling mod first. If it is already current, the library it calls is probably too new; match it to what the caller was built against.",
    },
    "config-crash": {
        "confirm": "The error names the file and usually the line.",
        "confused": "TOML is strict about quoting and trailing commas, so a file that looks fine often is not.",
        "next": "Back it up, delete it, let it regenerate, then reapply your changes a few at a time.",
    },
    "mod-rejections": {
        "confirm": "The kick message lists exactly what disagreed.",
        "confused": "Same mod, different version is by far the most common cause and reads like 'both have it, so it should work'. Versions must match exactly.",
        "next": "Bump the pack version so launchers force the update instead of trusting people to re-download. Full detail in <a href=\"/guides/players-kicked-mod-mismatch.html\">mod-mismatch kicks</a>.",
    },
    "datapack-recipe": {
        "confirm": "The error gives the JSON path. Open it.",
        "confused": "Usually assumed to be malformed JSON when it is actually a reference to an item that does not exist — which produces no error at all elsewhere.",
        "next": "Validate every referenced id against what your jars register. See <a href=\"/guides/kubejs-recipe-not-working.html\">ids that silently do nothing</a>.",
    },
    "own-class-missing": {
        "confirm": "The missing class is in the SAME package as the code asking for it. That means the jar is incomplete, not that a dependency is absent.",
        "confused": "Looks like a missing dependency. Compare the package names — a dependency failure names someone else's class.",
        "next": "Redownload the jar and compare its size against the source. Interrupted downloads are the usual cause, and hosting-panel uploads are a close second.",
    },
    "bad-resource-location": {
        "confirm": "The message quotes the offending string. Look for capitals, spaces, or a second colon.",
        "confused": "Blamed on a mod when it almost always comes from a config file or datapack somebody edited by hand.",
        "next": "Ids are lowercase <code>namespace:path</code>, with only <code>a-z 0-9 _ . - /</code> in the path. Grep your configs for the quoted string.",
    },
    "ticking-entity-mod-bug": {
        "confirm": "The crash report's <code>-- Entity being ticked --</code> section names the entity and gives exact coordinates.",
        "confused": "Looks random, because it only fires when that chunk loads. It will recur the moment someone goes back.",
        "next": "The thing is still in the world, so the server will die again on restart — this is the classic <a href=\"/guides/minecraft-server-keeps-restarting.html\">restart loop</a>. Remove it at those coordinates, or disable that mob in the mod's config.",
    },
    "mod-loading-wrapper": {
        "confirm": "This message is an envelope. Scroll to the LAST <code>Caused by:</code>.",
        "confused": "Searching the web for this exact line wastes an afternoon — it is the same text for dozens of unrelated causes.",
        "next": "Diagnose whatever the real cause turns out to be. <a href=\"/guides/how-to-read-a-minecraft-crash-report.html\">Reading a crash report</a> covers the order to do it in.",
    },
    "server-init-wrapper": {
        "confirm": "Also a wrapper. The real failure is below it.",
        "confused": "Reads like the server itself is broken when a single mod stopped startup.",
        "next": "Find the last <code>Caused by:</code> and work from there.",
    },
    "missing-mod-file": {
        "confirm": "The named file is in <code>mods/</code> but has no <code>mods.toml</code>, so it is not a mod.",
        "confused": "Libraries, resource packs and datapacks all end in <code>.jar</code> or get dropped in by mistake.",
        "next": "Move it where it belongs, or delete it if it was a bad download. If a mod requires it as a library, the mod page says where it goes.",
    },
}

NAV = ('<p class="eyebrow"><a href="/">Forge Server Tools</a> · '
       '<a href="/fix/">every failure mode</a> · '
       '<a href="/guides/">guides</a></p>')

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
    depth = DEPTH.get(rule.id, {})

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
  <h2>How to be sure it is this</h2>
  <p>{depth.get("confirm", "")}</p>
</section>

<section>
  <h2>What it gets mistaken for</h2>
  <p>{depth.get("confused", "")}</p>
</section>

<section>
  <h2>What to do next</h2>
  <p>{depth.get("next", "")}</p>
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
  <p class="eyebrow"><a href="/">Forge Server Tools</a> · <a href="/guides/">guides</a></p>
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
    thin = [r.id for r in fd.RULES if r.id not in DEPTH]
    if thin:
        raise SystemExit("no hand-written depth for: %s -- a generated page with "
                         "only the rule text is too thin to index" % thin)

    written = []
    for r in fd.RULES:
        p = os.path.join(OUT, "%s.html" % r.id)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(page(r, css, QUERY[r.id]))
        written.append(r)
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(index_page(written, css))

    print("%d pages + index (sitemap: run build_sitemap.py)" % len(written))


if __name__ == "__main__":
    main()

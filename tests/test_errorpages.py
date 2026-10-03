"""Tests for the failure-mode page generator.

readable() is the risky part: it runs over all 24 rules and a regression there
ships 24 broken pages at once, each one shown to someone whose server is down.
The first version produced
"org.spongepowered.asm.mixin.:injection.throwables.w" -- worse than printing
nothing -- and nothing would have caught it but reading the output.
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, "/mnt/e/ForgeServerDoctor")

import make_errorpages as mp  # noqa: E402
import forge_doctor as fd     # noqa: E402

REGEX_CHARS = set("\\^$*+?|{}[]()")


class TestReadable(unittest.TestCase):
    def test_no_rule_produces_leftover_regex_syntax(self):
        """The whole suite of real patterns, not a hand-picked one."""
        for rule in fd.RULES:
            for pat in rule.patterns:
                got = mp.readable(pat)
                self.assertFalse(REGEX_CHARS & set(got),
                                 "%s: %r -> %r" % (rule.id, pat, got))

    def test_every_rule_yields_at_least_one_searchable_string(self):
        """A page whose 'search your log for this' box is empty is useless."""
        for rule in fd.RULES:
            frags = [f for f in (mp.readable(p) for p in rule.patterns) if f]
            self.assertTrue(frags, "%s produced nothing searchable" % rule.id)

    def test_escaped_dots_survive_as_dots(self):
        self.assertEqual(mp.readable(r"java\.lang\.OutOfMemoryError:"),
                         "java.lang.OutOfMemoryError:")

    def test_named_groups_do_not_leak_their_names(self):
        got = mp.readable(r"Attempted to load class (?P<cls>\S+) for invalid dist")
        self.assertNotIn("cls", got)
        self.assertIn("Attempted to load class", got)
        self.assertIn("for invalid dist", got)

    def test_character_classes_are_dropped_not_sampled(self):
        """The first version took the first character of a class, turning
        `\\S+` into a stray 'S' glued to the end of the message."""
        self.assertEqual(mp.readable(r"Mixin apply failed \S+"), "Mixin apply failed")

    def test_optional_groups_are_removed_whole(self):
        got = mp.readable(r"org\.spongepowered\.asm\.mixin\.(?:injection\.)?throwables\.")
        self.assertNotIn(":", got)
        self.assertIn("org.spongepowered.asm.mixin.", got)

    def test_quantifier_braces_do_not_survive(self):
        self.assertNotIn("{", mp.readable(r"RuntimeDistCleaner.{0,200}invalid dist"))

    def test_an_unescaped_dot_is_a_wildcard_not_a_full_stop(self):
        """`.` means any character. Printing it as a literal dot produces a
        string that is not in the log, so pasting it into a search finds
        nothing -- the one job this function has."""
        self.assertEqual(mp.readable(r"RuntimeDistCleaner.{0,200}invalid dist"),
                         "RuntimeDistCleaner  ...  invalid dist")
        self.assertEqual(mp.readable(r"Exception ticking .+"), "Exception ticking")

    def test_short_noise_fragments_are_discarded(self):
        self.assertEqual(mp.readable(r"a\S+b"), "")


class TestHonestCallToAction(unittest.TestCase):
    def test_free_ids_match_what_the_free_build_actually_ships(self):
        """If build_free.py's list changes and this one does not, 18 pages
        start claiming the free tool detects things it cannot."""
        import re
        src = open("/mnt/e/ForgeServerDoctor/build_free.py", encoding="utf-8").read()
        block = re.search(r"FREE_IDS\s*=\s*\{(.*?)\}", src, re.S).group(1)
        actual = set(re.findall(r'"([a-z0-9-]+)"', block))
        self.assertEqual(mp.FREE_IDS, actual)

    def test_every_rule_has_a_search_query_written_for_it(self):
        self.assertEqual({r.id for r in fd.RULES} - set(mp.QUERY), set())


if __name__ == "__main__":
    unittest.main(verbosity=2)

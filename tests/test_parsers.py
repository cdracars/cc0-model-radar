import unittest

from cc0_model_radar.makerworld import parse_models, parse_model_page
from cc0_model_radar.models import MakerWorldModel
from cc0_model_radar.fetch import FetchError
from cc0_model_radar.models import Candidate, PrintablesMatch
from cc0_model_radar.printables import _fallback_results, _results, find_match, find_search_fallback
from cc0_model_radar.report import write_markdown
from cc0_model_radar.text import similarity


class ParserTests(unittest.TestCase):
    def test_makerworld_search_extracts_models(self):
        html = '''<a href="/en/models/1234-example-model">Example Model</a>'''
        models = parse_models(html, source="fixture")
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].model_id, "1234")

    def test_makerworld_page_verifies_cc0_and_creator(self):
        model = MakerWorldModel("1234", "", "", "https://makerworld.com/en/models/1234-example")
        html = '''<title>Example Model - Free 3D Print Model - MakerWorld</title>
        <p>Download this free 3D print file designed by NLD Design Shop.</p>
        <p>This user content is licensed under CC0.</p>
        <a href="https://creativecommons.org/2008/04/16/cc0-betadiscussion-draft-2/">CC0</a>'''
        parse_model_page(html, model)
        self.assertEqual(model.license_name, "CC0")
        self.assertEqual(model.creator, "NLD Design Shop")
        self.assertIn("creativecommons.org", model.license_url)

    def test_printables_results_extract_model_links(self):
        html = '''<a href="/model/9876-example-model">Example Model</a>'''
        self.assertEqual(_results(html), [("https://www.printables.com/model/9876-example-model", "Example Model")])

    def test_search_fallback_extracts_printables_links(self):
        html = '''<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.printables.com%2Fmodel%2F9876-example">Example Model</a>'''
        self.assertEqual(_fallback_results(html), [("https://www.printables.com/model/9876-example", "Example Model")])

    def test_similarity(self):
        self.assertGreaterEqual(similarity("Retroid Odin Small Caps", "Retroid/Odin Small Caps"), 0.7)



class StubFetcher:
    """Returns canned pages by URL host; raises FetchError for blocked hosts."""

    def __init__(self, pages):
        self.pages = pages
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        for host, page in self.pages.items():
            if host in url:
                if isinstance(page, Exception):
                    raise page
                return page
        raise AssertionError(f"unexpected URL {url}")


MODEL = MakerWorldModel("1", 'Cable "Clip"', "", "https://makerworld.com/en/models/1")
DDG_CHALLENGE = '<html><body><form id="challenge-form">Unfortunately, bots use DuckDuckGo too.</form></body></html>'
DDG_NO_RESULTS = '<html><body><div class="no-results">No results.</div></body></html>'
DDG_HIT = (
    '<a class="result__a" href="//duckduckgo.com/l/?uddg='
    'https%3A%2F%2Fwww.printables.com%2Fmodel%2F42-cable-clip">Cable Clip</a>'
)


class FallbackTests(unittest.TestCase):
    def test_challenge_page_is_unknown_not_absence(self):
        match = find_search_fallback(StubFetcher({"duckduckgo": DDG_CHALLENGE}), MODEL)
        self.assertEqual(match.status, "unknown")
        self.assertIn("challenge page", match.evidence)

    def test_unrecognized_page_is_unknown(self):
        match = find_search_fallback(StubFetcher({"duckduckgo": "<html><body>new layout</body></html>"}), MODEL)
        self.assertEqual(match.status, "unknown")

    def test_explicit_no_results_is_likely_not_found(self):
        match = find_search_fallback(StubFetcher({"duckduckgo": DDG_NO_RESULTS}), MODEL)
        self.assertEqual(match.status, "likely_not_found")

    def test_hit_is_possible_match(self):
        match = find_search_fallback(StubFetcher({"duckduckgo": DDG_HIT}), MODEL)
        self.assertEqual(match.status, "possible_match")
        self.assertEqual(match.url, "https://www.printables.com/model/42-cable-clip")

    def test_quotes_in_title_do_not_break_phrase_query(self):
        fetcher = StubFetcher({"duckduckgo": DDG_NO_RESULTS})
        find_search_fallback(fetcher, MODEL)
        self.assertIn("%22Cable%20Clip%22", fetcher.urls[0])

    def test_direct_403_uses_fallback(self):
        fetcher = StubFetcher({"printables.com/search": FetchError("403"), "duckduckgo": DDG_HIT})
        match = find_match(fetcher, MODEL)
        self.assertEqual(match.status, "possible_match")
        self.assertIn("Direct Printables lookup failed", match.evidence)

    def test_direct_empty_page_is_not_treated_as_absence(self):
        fetcher = StubFetcher({"printables.com/search": "<html>Just a moment...</html>", "duckduckgo": DDG_CHALLENGE})
        match = find_match(fetcher, MODEL)
        self.assertEqual(match.status, "unknown")
        self.assertIn("inconclusive", match.evidence)


class ReportTests(unittest.TestCase):
    def test_pipes_and_brackets_do_not_break_table(self):
        import tempfile, os
        model = MakerWorldModel("1", "Box | Lid [v2]", "A|B", "https://makerworld.com/en/models/1")
        match = PrintablesMatch(status="unknown", evidence="x | y")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "r.md")
            write_markdown([Candidate(model, match)], path)
            with open(path, encoding="utf-8") as handle:
                row = handle.read().splitlines()[-1]
        # Six columns means seven unescaped pipes.
        self.assertEqual(row.replace("\\|", "").count("|"), 7)


if __name__ == "__main__":
    unittest.main()


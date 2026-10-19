import unittest

from cc0_model_radar.makerworld import parse_models, parse_model_page
from cc0_model_radar.models import MakerWorldModel
from cc0_model_radar.printables import _results
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

    def test_similarity(self):
        self.assertGreaterEqual(similarity("Retroid Odin Small Caps", "Retroid/Odin Small Caps"), 0.7)


if __name__ == "__main__":
    unittest.main()


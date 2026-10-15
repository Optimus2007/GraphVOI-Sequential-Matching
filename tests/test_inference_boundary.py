import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest

from evaluate import invoke
from graphvoi.policy import decide
from kit import Simulator, generate


class BoundaryTests(unittest.TestCase):
    def test_inference_imports_only_allowed_kit_symbols(self):
        for name in ('core.py', 'models.py', 'answers.py', 'clarification.py', 'policy.py'):
            tree = ast.parse(Path('graphvoi', name).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == 'kit':
                    self.assertLessEqual({n.name for n in node.names}, {'HARD', 'SOFT', 'eligibility'})
                if isinstance(node, ast.Import):
                    self.assertNotIn('kit', {n.name for n in node.names})

    def test_inference_assets_exclude_member_ids_and_latent_fields(self):
        asset = json.loads(Path('assets/answer_model.json').read_text())
        for donor in asset['hard_donors']:
            self.assertEqual(set(donor), {'age', 'gender', 'zone', 'fields'})
            self.assertFalse(set(donor) & {'truth', 'bias', 'response_rate', 'seed', 'member_id'})

    def test_assets_match_training_hashes(self):
        summary = json.loads(Path('assets/training_summary.json').read_text())
        for name, expected in summary['asset_sha256'].items():
            self.assertEqual(hashlib.sha256(Path('assets', name).read_bytes()).hexdigest(), expected)

    def test_real_process_matches_inprocess_action(self):
        state = Simulator(generate(9104, 16)).observe()
        request = dict(schema_version='1.0.0', phase='ask', state=state, memory=None)
        actual, _ = invoke([sys.executable, 'policy.py', '--method', 'graphvoi'], request)
        self.assertEqual(actual, decide(request, method='graphvoi'))

    def test_docker_excludes_worlds_and_research(self):
        dockerfile = Path('Dockerfile').read_text()
        self.assertNotIn('COPY . ', dockerfile)
        self.assertNotIn('COPY data', dockerfile)
        self.assertNotIn('COPY research', dockerfile)
        self.assertIn('COPY assets/', dockerfile)
        self.assertIn('COPY vendor/', dockerfile)


if __name__ == '__main__':
    unittest.main()

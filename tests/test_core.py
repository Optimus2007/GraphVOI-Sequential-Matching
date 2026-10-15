import copy
import itertools
import json
import sys
import unittest

from evaluate import invoke, validate_response
from kit import HARD, Simulator, generate
from graphvoi.core import (allocate, legal_asks, normalize, optimal_matching,
                           pair_features, validate_pairs, weighted_edges)
from graphvoi.policy import decide


def fixture(n=4):
    world = generate(999, n)
    for m in world['members']:
        m['arrived_day'] = 0
        m['exit_day'] = 10000
        m['age'] = 30
        m['zone'] = 'zone_a'
        m['truth'].update(age_min=18, age_max=65,
                          who_to_meet=['woman', 'man', 'non_binary'],
                          relationship_structure='monogamous', partner_smoking='any',
                          partner_children='any', wants_children='unsure',
                          acceptable_zones=['zone_a'], schedule=['weekend_day'])
        m['fields'] = copy.deepcopy(m['truth'])
        m['field_status'] = {k: 'observed' for k in m['fields']}
        m['field_observed_day'] = {k: 0 for k in m['fields']}
    return Simulator(world)


class CoreTests(unittest.TestCase):
    def test_global_optimum_beats_greedy(self):
        edges = {('a', 'b'): .9, ('c', 'd'): .05, ('a', 'd'): .65, ('b', 'c'): .65}
        self.assertEqual(optimal_matching(edges), ([('a', 'd'), ('b', 'c')], 1.3))

    def test_odd_cycle_and_disconnected_components(self):
        edges = {('a', 'b'): 2, ('a', 'c'): 3, ('b', 'c'): 4, ('d', 'e'): 5}
        self.assertEqual(optimal_matching(edges), ([('b', 'c'), ('d', 'e')], 9))

    def test_small_graph_matches_exhaustive_optimum(self):
        import random
        r = random.Random(18)
        for n in range(2, 8):
            edges = {p: r.random() for p in itertools.combinations('abcdefg'[:n], 2)}
            def best(nodes):
                if not nodes:
                    return 0
                a, *rest = nodes
                return max([best(rest)] + [edges[tuple(sorted((a, b)))] +
                           best([c for c in rest if c != b]) for b in rest])
            self.assertAlmostEqual(optimal_matching(edges)[1], best(list('abcdefg'[:n])))

    def test_ties_ignore_input_insertion_order(self):
        e = {p: 1 for p in itertools.combinations('abcd', 2)}
        self.assertEqual(optimal_matching(e), optimal_matching(dict(reversed(list(e.items())))))

    def test_missing_and_declined_never_consent(self):
        s = fixture(2).observe()
        m = s['members'][0]
        m['fields']['who_to_meet'] = None
        m['field_status']['who_to_meet'] = 'not_asked'
        self.assertEqual(allocate(normalize(s)), [])
        m['field_status']['who_to_meet'] = 'declined'
        m['fields']['who_to_meet'] = ['woman', 'man', 'non_binary']
        clean = normalize(s)
        self.assertEqual(allocate(clean), [])
        self.assertFalse(any(a['member_id'] == m['member_id'] for a in legal_asks(clean)))

    def test_explicit_preferences_override_utility(self):
        s = fixture(2).observe()
        s['members'][0]['fields']['age_max'] = 22
        self.assertEqual(allocate(normalize(s), scorer=lambda *args: 100), [])

    def test_future_and_unobserved_fields_unusable(self):
        s = fixture(2).observe()
        s['members'][0]['field_observed_day']['age_min'] = 1
        self.assertEqual(allocate(normalize(s)), [])

    def test_no_repeated_or_unavailable_pairs(self):
        sim = fixture(2)
        sim.advance(allocate(normalize(sim.observe())))
        self.assertEqual(allocate(normalize(sim.observe())), [])
        for _ in range(40):
            sim.advance([])
        self.assertEqual(allocate(normalize(sim.observe())), [])

    def test_output_revalidation_rejects_overlap(self):
        s = fixture(3).observe()
        ids = [m['member_id'] for m in s['members']]
        with self.assertRaises(ValueError):
            validate_pairs(s, [(ids[0], ids[1]), (ids[0], ids[2])])

    def test_input_immutable_and_memory_round_trip(self):
        s = fixture().observe()
        original = copy.deepcopy(s)
        req = dict(schema_version='1.0.0', phase='match', state=s, memory={'pending': ['x']})
        response = decide(req)
        validate_response(response, 'match')
        self.assertEqual(response['memory'], req['memory'])
        self.assertEqual(original, s)
        self.assertEqual(response, decide(req))

    def test_features_exclude_ids_and_hidden_inputs(self):
        s = fixture(2).observe()
        a, b = s['members']
        before = pair_features(a, b, 0)
        a.update(member_id='other', truth={'foo': 'bar'}, bias=1e9)
        self.assertEqual(before, pair_features(a, b, 0))

    def test_complete_episodes_and_repeatability(self):
        def run():
            sim = Simulator(generate(9101, 80))
            memory, actions = None, []
            for _ in range(60):
                for phase in ('ask', 'match'):
                    r = decide(dict(schema_version='1.0.0', phase=phase,
                                    state=sim.observe(), memory=memory))
                    validate_response(r, phase)
                    memory = r['memory']
                    action = r['asks' if phase == 'ask' else 'pairs']
                    actions.append(action)
                    if phase == 'ask':
                        sim.resolve_asks(action)
                    else:
                        sim.advance(action)
            for _ in range(40):
                sim.advance([])
            return actions, sim.metrics()
        self.assertEqual(run(), run())

    def test_empty_and_sparse_pools(self):
        for n in (0, 1):
            s = Simulator(generate(1, n)).observe()
            for phase, key in [('ask', 'asks'), ('match', 'pairs')]:
                self.assertEqual(decide(dict(schema_version='1.0.0', phase=phase,
                                            state=s, memory=None))[key], [])


if __name__ == '__main__':
    unittest.main()

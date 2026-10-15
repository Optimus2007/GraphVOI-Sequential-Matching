"""Shared hard-bundle budget fill (v3): legal, capped, identical across selectors."""
import unittest
from unittest.mock import patch

from graphvoi.clarification import fill_hard_budget, select_asks
from graphvoi.core import ask_cost, legal_asks
from graphvoi.policy import decide
from tests.test_independent_audit import state, hide, ask, scorer, Answers


def request(s):
    return dict(schema_version='1.0.0', phase='ask', state=s, memory=None)


class BudgetFillTests(unittest.TestCase):
    def test_fill_spends_unused_units_on_hard_bundles_by_potential(self):
        s = state('abcdef')
        for i in 'abcdef':
            hide(s, i)
        f = scorer({('a', 'b'): 1, ('c', 'd'): 5, ('e', 'f'): 3})
        out = fill_hard_budget(s, f, [])
        self.assertEqual(sum(map(ask_cost, out)), 12)
        # Potential: c,d=5 > e,f=3 > a,b=1; ties broken by member ID.
        self.assertEqual(out, ask('c') + ask('d') + ask('e') + ask('f'))

    def test_fill_keeps_selected_prefix_and_never_duplicates_or_overspends(self):
        s = state('abcdef')
        for i in 'abcdef':
            hide(s, i)
        hide(s, 'a', 'relationship_goal')
        f = scorer({('a', 'b'): 1})
        chosen = ask('a', 'relationship_goal') + ask('b')
        out = fill_hard_budget(s, f, chosen)
        self.assertEqual(out[:2], chosen)
        keys = [(q['member_id'], q['field']) for q in out]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertLessEqual(sum(map(ask_cost, out)), 12)
        self.assertEqual(sum(map(ask_cost, out)), 1 + 3 + 6)  # 2 units cannot buy a bundle
        legal = {(q['member_id'], q['field']) for q in legal_asks(s)}
        self.assertTrue(set(keys) <= legal)

    def test_fill_never_asks_declined_or_complete_members_or_soft_fields(self):
        s = state('abcd')
        hide(s, 'a')
        hide(s, 'b')
        s['members'][1]['field_status']['age_min'] = 'declined'
        hide(s, 'c', 'lifestyle')
        out = fill_hard_budget(s, scorer({}), [])
        self.assertEqual(out, ask('a'))

    def test_fill_respects_remaining_daily_budget(self):
        s = state('abcd')
        for i in 'abcd':
            hide(s, i)
        s['ask_budget_remaining'] = 5
        self.assertEqual(len(fill_hard_budget(s, scorer({}), [])), 1)
        s['ask_budget_remaining'] = 2
        self.assertEqual(fill_hard_budget(s, scorer({}), []), [])

    def test_same_fill_for_every_selector_and_ablation_disables_it(self):
        s = state('abcdef')
        for i in 'abcdef':
            hide(s, i)
        calls = []

        def fake_select(st, sc, model, strategy, **kw):
            calls.append(strategy)
            return ask('a')
        with patch('graphvoi.clarification.select_asks', side_effect=fake_select), \
                patch('graphvoi.policy.pair_model', return_value=scorer({})):
            outs = {m: decide(request(s), method=m)['asks']
                    for m in ('graphvoi', 'degree_first', 'uncertainty_first', 'graphvoi_nofill')}
        self.assertEqual(calls, ['graphvoi', 'degree_first', 'uncertainty_first', 'graphvoi'])
        filled = outs['graphvoi']
        self.assertEqual(filled[0], ask('a')[0])
        self.assertEqual(sum(map(ask_cost, filled)), 12)
        self.assertEqual(outs['degree_first'], filled)
        self.assertEqual(outs['uncertainty_first'], filled)
        self.assertEqual(outs['graphvoi_nofill'], ask('a'))

    def test_voi_selection_itself_is_unchanged_by_fill(self):
        s = state('abcd')
        hide(s, 'b')
        f = scorer({('a', 'b'): 10, ('a', 'd'): 9})
        model = Answers({'b': [(.5, {'age_min': 18}), (.5, {'age_min': 40})]})
        self.assertEqual(select_asks(s, f, model), ask('b'))

    def test_expired_deadline_stops_evaluation_but_still_returns_legal_filled_asks(self):
        s = state('abcdef')
        for i in 'abcdef':
            hide(s, i)
        f = scorer({('a', 'b'): 2, ('c', 'd'): 1})
        model = Answers({i: [(1, {'age_min': 18})] for i in 'abcdef'})
        diagnostics = {}
        self.assertEqual(select_asks(s, f, model, diagnostics=diagnostics, deadline=0.0), [])
        self.assertTrue(diagnostics['deadline'])
        with patch('graphvoi.policy.ASK_DEADLINE_SECONDS', -1e9), \
                patch('graphvoi.policy.pair_model', return_value=f):
            response = decide(request(s), method='graphvoi')
        asks = response['asks']
        self.assertEqual(sum(map(ask_cost, asks)), 12)
        legal = {(q['member_id'], q['field']) for q in legal_asks(s)}
        self.assertTrue({(q['member_id'], q['field']) for q in asks} <= legal)
        self.assertEqual(response['memory']['orbit_deadline_count'], 1)

    def test_unexpired_deadline_does_not_change_selection(self):
        s = state('abcd')
        hide(s, 'b')
        f = scorer({('a', 'b'): 10, ('a', 'd'): 9})
        model = Answers({'b': [(.5, {'age_min': 18}), (.5, {'age_min': 40})]})
        self.assertEqual(select_asks(s, f, model, deadline=float('inf')), select_asks(s, f, model))


if __name__ == '__main__':
    unittest.main()

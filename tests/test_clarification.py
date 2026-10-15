import copy
import unittest

from graphvoi.answers import AnswerModel, apply_answer
from graphvoi.clarification import (MatchingContext, graphvoi_value, question_score, select_asks)
from graphvoi.core import legal_asks, normalize, weighted_edges
from graphvoi.models import fit_logistic, predict
from scripts.train_models import labelled_rows
from tests.test_core import fixture


class FixedAnswers:
    def __init__(self, values):
        self.values = values

    def outcomes(self, state, ask):
        return self.values[ask['member_id']]


def named_state(names):
    state = fixture(len(names)).observe()
    for m, name in zip(state['members'], names):
        m['member_id'] = name
    return state


def missing(state, ident, keys):
    m = next(m for m in state['members'] if m['member_id'] == ident)
    for key in keys:
        m['fields'][key] = None
        m['field_status'][key] = 'not_asked'
        m['field_observed_day'][key] = None


class ClarificationTests(unittest.TestCase):
    def test_allocation_value_over_shadowed_degree(self):
        state = named_state('abcdex')
        missing(state, 'c', ['age_min'])
        missing(state, 'x', ['age_min'])
        weights = {('a', 'b'): .62, ('d', 'e'): .3, ('c', 'd'): .6, ('b', 'x'): .1}
        scorer = lambda a, b, day: weights.get(tuple(sorted((a['member_id'], b['member_id']))), 0)
        model = FixedAnswers({'c': [(1, {'age_min': 18})], 'x': [(1, {'age_min': 18})]})
        qc = [{'member_id': 'c', 'field': 'constraints'}]
        qx = [{'member_id': 'x', 'field': 'constraints'}]
        self.assertAlmostEqual(graphvoi_value(state, qc, scorer, model), .3)
        self.assertAlmostEqual(graphvoi_value(state, qx, scorer, model), 0)
        state['ask_budget_remaining'] = 3
        self.assertEqual(select_asks(state, scorer, model), qc)

    def test_complementary_pair_zero_singleton_gain(self):
        state = named_state('ab')
        for ident in 'ab':
            missing(state, ident, ['age_min'])
        model = FixedAnswers({i: [(1, {'age_min': 18})] for i in 'ab'})
        asks = [{'member_id': i, 'field': 'constraints'} for i in 'ab']
        scorer = lambda *args: 1.0
        for q in asks:
            self.assertEqual(graphvoi_value(state, [q], scorer, model), 0)
        self.assertEqual(graphvoi_value(state, asks, scorer, model), 1)
        self.assertEqual(select_asks(state, scorer, model), asks)
        self.assertEqual(select_asks(state, scorer, model, paired=False), [])
        self.assertAlmostEqual(graphvoi_value(state, asks, scorer, model, penalty=.2), -.2)

    def test_answer_probability_expectation(self):
        state = named_state('ab')
        missing(state, 'a', ['age_min'])
        q = [{'member_id': 'a', 'field': 'constraints'}]
        model = FixedAnswers({'a': [(.25, {'age_min': 18}), (.75, {'age_min': 40})]})
        self.assertAlmostEqual(graphvoi_value(state, q, lambda *a: 2, model), .5)

    def test_hypothetical_never_fills_refusal_or_changes_observation(self):
        state = named_state('ab')
        missing(state, 'a', ['age_min'])
        m = state['members'][0]
        m['field_status']['age_min'] = 'declined'
        before = copy.deepcopy(state)
        after = apply_answer(state, {'member_id': 'a', 'field': 'constraints'},
                             {'age_min': 18, 'who_to_meet': ['non_binary']})
        self.assertIsNone(after['members'][0]['fields']['age_min'])
        self.assertEqual(after['members'][0]['fields']['who_to_meet'], m['fields']['who_to_meet'])
        self.assertEqual(state, before)

    def test_cached_edges_equal_full_recomputation(self):
        state = named_state('abcd')
        missing(state, 'a', ['age_min'])
        scorer = lambda a, b, day: .5
        context = MatchingContext(state, scorer)
        world = apply_answer(state, {'member_id': 'a', 'field': 'constraints'}, {'age_min': 18})
        self.assertEqual(context.updated(world), weighted_edges(world, scorer))

    def test_budget_and_daily_duplicate_exclusion(self):
        state = named_state('ab')
        for ident in 'ab':
            missing(state, ident, ['age_min'])
        model = FixedAnswers({i: [(1, {'age_min': 18})] for i in 'ab'})
        state['ask_budget_remaining'] = 5
        self.assertEqual(select_asks(state, lambda *a: 1, model), [])
        state['ask_log'] = [{'member_id': 'a', 'field': 'constraints', 'observed_day': 0}]
        self.assertFalse(any(q['member_id'] == 'a' for q in legal_asks(state)))

    def test_unsupported_constraints_do_not_invent_donors(self):
        state = named_state('a')
        missing(state, 'a', ['age_min'])
        model = AnswerModel(asset={'hard_donors': [], 'soft_counts': {}})
        self.assertEqual(model.outcomes(state, {'member_id': 'a', 'field': 'constraints'}), [(1, {})])

    def test_censored_response_and_undated_pairs_no_second_labels(self):
        intro = dict(introduction_id='i', user_a='a', user_b='b', assigned_day=0,
                     response_deadline_day=7)
        examples = [(intro, [1], [1], [1])]
        rows, count = labelled_rows(examples, {})
        self.assertEqual(rows['directional_acceptance'], [])
        self.assertEqual(count, 1)
        events = {'i': [dict(member_id=i, event='introduction_response', value='no', observed_day=7)
                        for i in 'ab']}
        rows, _ = labelled_rows(examples, events)
        self.assertEqual(rows['timely_seconds_given_date'], [])
        self.assertEqual(rows['mutual_acceptance'][0][1], 0)

    def test_sparse_fit_reports_support_and_finite_predictions(self):
        model = fit_logistic([([1, 0], 0)], 2)
        self.assertFalse(model['fitted_features'])
        self.assertGreater(predict(model, [1, 0]), 0)
        self.assertLess(predict(model, [1, 0]), 1)

    def test_dense_guard_is_explicit_and_deterministic(self):
        state = fixture(36).observe()
        diagnostics = {}
        asks = select_asks(state, lambda *a: 1, FixedAnswers({}), diagnostics=diagnostics)
        self.assertEqual(asks, [])
        self.assertIn('dense_feasible_graph', diagnostics['fallback'])

    def test_uncertainty_is_answer_entropy_not_missing_count(self):
        import math
        state = named_state('ab')
        q = [dict(member_id='a', field='constraints')]
        scorer = lambda *a: 1
        known = FixedAnswers({'a': [(1, {'age_min': 18, 'age_max': 65})]})
        uncertain = FixedAnswers({'a': [(.5, {'age_min': 18}), (.5, {'age_min': 22})]})
        self.assertEqual(question_score(state, q, scorer, known, 'uncertainty_first'), 0)
        self.assertAlmostEqual(question_score(state, q, scorer, uncertain, 'uncertainty_first'), math.log(2))


if __name__ == '__main__':
    unittest.main()

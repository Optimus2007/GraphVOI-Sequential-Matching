import copy
import unittest

from graphvoi.analysis import OpportunityTracker, calibration, paired_intervals
from scripts.run_experiments import DisclosureSimulator
from scripts.summarize_results import stage_labels
from tests.test_core import fixture


class AnalysisTests(unittest.TestCase):
    def test_opportunities_distinguish_feasible_unserved(self):
        sim = fixture(3)
        state = sim.observe()
        ids = [m['member_id'] for m in state['members']]
        tracker = OpportunityTracker()
        tracker.observe(state, [], [[ids[0], ids[1]]])
        rows = {r['member_id']: r for r in tracker.results()['members']}
        self.assertEqual(rows[ids[2]]['classification'], 'feasible_but_never_introduced')
        self.assertEqual(rows[ids[2]]['eligible_opportunities'], 2)
        self.assertEqual(rows[ids[0]]['wait_days'], 0)
        self.assertIsNone(rows[ids[2]]['wait_days'])

    def test_disclosure_wrapper_preserves_truth_and_logged_refusal(self):
        world = fixture(2).world
        first = world['members'][0]
        first['fields']['age_min'] = None
        first['field_status']['age_min'] = 'not_asked'
        first['field_observed_day']['age_min'] = None
        before = copy.deepcopy(first['truth'])
        sim = DisclosureSimulator(world)
        sim.rate = 1
        result = sim.resolve_asks([dict(member_id=first['member_id'], field='constraints')])
        member = sim.observe()['members'][0]
        self.assertEqual(sim.members[first['member_id']]['truth'], before)
        self.assertIsNone(member['fields']['age_min'])
        self.assertEqual(member['field_status']['age_min'], 'declined')
        self.assertEqual(result, sim.ask_log)
        self.assertNotIn('rate', sim.observe())

    def test_calibration_values_and_empty_bins(self):
        result = calibration([dict(p=.25, y=0), dict(p=.75, y=1)])
        self.assertAlmostEqual(result['brier'], .0625)
        self.assertEqual(sum(b['count'] for b in result['reliability']), 2)
        self.assertIsNone(calibration([])['brier'])

    def test_paired_not_unpaired_intervals(self):
        rows = []
        for method, delta in [('uncertainty_first', 0), ('graphvoi', 1)]:
            for seed in range(3):
                rows.append(dict(valid=True, method=method, variant='development', seed=seed,
                    msmi_per_100_arrived_members=seed + delta,
                    mutual_acceptances_per_100=seed + delta, coverage=.5, ask_cost=12))
        ci = paired_intervals(rows, replicates=100)['graphvoi']['msmi_per_100_arrived_members']
        self.assertEqual(ci['ci95'], [1, 1])
        self.assertFalse(ci['reliable_sample_size'])

    def test_report_stages_do_not_invent_undated_second_labels(self):
        intro = dict(introduction_id='i', assigned_day=0, response_deadline_day=7)
        prediction = dict(mutual_acceptance=.4, date_given_mutual=.7, timely_seconds_given_date=.1)
        events = [dict(introduction_id='i', event='introduction_response', value='yes', observed_day=2)
                  for _ in range(2)]
        events.append(dict(introduction_id='i', event='date_happened', value=False,
                           observed_day=10, occurred_day=10))
        trace = dict(predictions=[dict(introduction=intro, prediction=prediction)], feedback=events)
        rows = stage_labels(trace)
        self.assertEqual(rows['date_given_mutual'][0]['y'], 0)
        self.assertEqual(rows['timely_seconds_given_date'], [])

    def test_shared_seed_bootstrap_retains_scenario_covariance(self):
        rows = []
        for method in ('uncertainty_first', 'graphvoi'):
            for variant in ('a', 'b'):
                for seed in (0, 1):
                    value = 0 if method == 'uncertainty_first' else 2 * (seed if variant == 'a' else 1 - seed)
                    rows.append(dict(valid=True, method=method, variant=variant, seed=seed,
                        msmi_per_100_arrived_members=value, mutual_acceptances_per_100=value,
                        coverage=.5, ask_cost=12))
        result = paired_intervals(rows, replicates=100)['graphvoi']['msmi_per_100_arrived_members']
        self.assertEqual(result['ci95'], [1, 1])
        self.assertIn('clusters', result['bootstrap'])

    def test_report_late_seconds_do_not_qualify_as_msmi(self):
        intro = dict(introduction_id='i', assigned_day=0, response_deadline_day=7)
        prediction = dict(mutual_acceptance=.4, date_given_mutual=.7, timely_seconds_given_date=.1)
        events = [dict(introduction_id='i', event='introduction_response', value='yes', observed_day=2)
                  for _ in range(2)]
        events.append(dict(introduction_id='i', event='date_happened', value=True,
                           observed_day=10, occurred_day=10))
        events.extend(dict(introduction_id='i', event='second_meeting_intention', value='yes',
                           observed_day=day, occurred_day=day) for day in (12, 14))
        rows = stage_labels(dict(predictions=[dict(introduction=intro, prediction=prediction)], feedback=events))
        self.assertEqual(rows['timely_seconds_given_date'][0]['y'], 0)


if __name__ == '__main__':
    unittest.main()

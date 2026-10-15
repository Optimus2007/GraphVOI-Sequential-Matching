"""Regression requirements for the independently reproduced audit defects."""
import copy
import unittest
import random
import itertools
from unittest.mock import patch
from kit import HARD, SOFT, OPTIONS
from graphvoi.answers import AnswerModel
from graphvoi.analysis import paired_intervals
from graphvoi.clarification import select_asks, joint_value_reference, counterfactuals, compress_worlds
from graphvoi.clarification import candidate_actions, action_key
from graphvoi.core import weighted_edges, ask_cost, optimal_matching
from graphvoi.policy import decide
from scripts.run_pilot import aggregate
from tests.test_independent_audit import state, hide, ask, scorer, Answers


class CorrectnessFixTests(unittest.TestCase):
    def test_joint_soft_questions_unlock_alternating_allocation(self):
        s=state('abcd');hide(s,'a','relationship_goal');hide(s,'c','relationship_goal')
        s['ask_budget_remaining']=2
        for m in s['members']:
            m['gender']='woman' if m['member_id'] in 'ac' else 'man'
            m['fields']['who_to_meet']=['man'] if m['gender']=='woman' else ['woman']
        def f(a,b,day):
            pair=tuple(sorted((a['member_id'],b['member_id'])))
            members={m['member_id']:m for m in (a,b)}
            if pair==('a','b'):return 7 if members['a']['fields']['relationship_goal'] is not None else 0
            if pair==('c','d'):return 7 if members['c']['fields']['relationship_goal'] is not None else 0
            return {('a','d'):6,('b','c'):6}.get(pair,0)
        model=Answers({i:[(1,{'relationship_goal':'long_term'})] for i in 'ac'})
        qa=ask('a','relationship_goal');qc=ask('c','relationship_goal')
        self.assertEqual(joint_value_reference(s,qa,f,model),0)
        self.assertEqual(joint_value_reference(s,qc,f,model),0)
        self.assertEqual(joint_value_reference(s,qa+qc,f,model),2)
        self.assertEqual(select_asks(s,f,model),qa+qc)

    def test_random_small_graphs_against_uncached_exhaustive_conditional_oracle(self):
        rng=random.Random(7718)
        def matching_value(edges,nodes):
            if not nodes:return 0
            a,*rest=nodes
            return max([matching_value(edges,rest)]+[
                edges.get(tuple(sorted((a,b))),0)+matching_value(edges,[i for i in rest if i!=b]) for b in rest])
        for _ in range(30):
            s=state('abcd');s['ask_budget_remaining']=6
            for i in rng.sample('abcd',rng.randrange(1,5)):hide(s,i)
            f=scorer({p:rng.randrange(1,10) for p in itertools.combinations('abcd',2)})
            model=Answers({i:[(.5,{'age_min':18}),(.5,{'age_min':40})] for i in 'abcd'})
            def expected(qs):
                return sum(p*matching_value(weighted_edges(w,f),list('abcd')) for p,w in counterfactuals(s,qs,model))
            selected=[];budget=6;actions=candidate_actions(s,f,paired=True)
            while budget:
                ranked=[];seen=set(action_key(selected));baseline=expected(selected)
                residual={}
                for action in actions:
                    rest=[q for q in action if (q['member_id'],q['field']) not in seen]
                    if rest and sum(map(ask_cost,rest))<=budget:residual[action_key(rest)]=rest
                for key,rest in residual.items():
                    gain=expected(selected+rest)-baseline
                    if gain>1e-12:ranked.append((-gain/sum(map(ask_cost,rest)),key,rest))
                if not ranked:break
                rest=min(ranked)[2];selected+=rest;budget-=sum(map(ask_cost,rest))
            self.assertEqual(select_asks(s,f,model),selected)

    def test_main_selectors_share_model_beliefs_and_candidate_settings(self):
        request=dict(schema_version='1.0.0',phase='ask',state=state('ab'),memory=None)
        calls=[]
        def record(*args,**kwargs): calls.append((args,kwargs)); return []
        with patch('graphvoi.clarification.select_asks',side_effect=record):
            for method in ('graphvoi','degree_first','uncertainty_first'):decide(request,method=method)
        self.assertEqual([c[0][3] for c in calls],['graphvoi','degree_first','uncertainty_first'])
        self.assertTrue(all(c[0][1] is calls[0][0][1] and c[0][2] is calls[0][0][2] for c in calls))
        self.assertTrue(all(c[1]['paired'] is True for c in calls))

    def test_pilot_checkpoint_does_not_infer_from_partial_or_failed_matrix(self):
        base=dict(valid=True,variant='a',seed=1,msmi_per_100_arrived_members=0,
            mutual_acceptances_per_100=0,coverage=.5,ask_cost=3,inference_seconds=1,
            mutual_acceptances=0,dates=0,unserved_members=100,first_introduction_wait_days=[0],
            phase_runtime={p:dict(maximum=.1) for p in ('ask','match')})
        methods=('uncertainty_first','graphvoi')
        row=dict(base,method='uncertainty_first')
        partial=aggregate([row],methods=methods,seeds=[1],variants=['a'])
        self.assertFalse(partial['complete']);self.assertIsNone(partial['paired_intervals'])
        bad=dict(valid=False,method='graphvoi',variant='a',seed=1,error='timeout')
        result=aggregate([row,bad],methods=methods,seeds=[1],variants=['a'])
        self.assertTrue(result['complete']);self.assertFalse(result['summaries']['graphvoi']['eligible'])
        ci=result['paired_intervals']['uncertainty_first']['graphvoi']
        self.assertEqual(ci['validation']['invalid_counts']['graphvoi'],1)
        self.assertIsNone(ci['coverage']['delta'])

    def test_randomized_cached_uncached_equivalence(self):
        rng=random.Random(4481); base=state('a')
        donors=[]
        for age in (25,30,40):
            fields=copy.deepcopy(base['members'][0]['fields']); fields.update(age_min=age-5,age_max=age+8)
            donors.append(dict(age=age,gender='woman',zone='zone_a',fields=fields))
        asset=dict(hard_donors=donors,soft_counts={k:{v:i+1 for i,v in enumerate(OPTIONS[k])} for k in SOFT})
        model=AnswerModel(asset=asset)
        for _ in range(400):
            s=copy.deepcopy(base); m=s['members'][0]
            s.update(day=rng.randrange(60),scenario=rng.choice(['sparse','drift','development']),memory=rng.choice([None,{},['unrelated']]))
            m.update(age=rng.randrange(21,47),gender=rng.choice(['woman','man','non_binary']),zone=rng.choice(['zone_a','zone_b']))
            for k in rng.sample(HARD+SOFT,rng.randrange(1,10)):
                m['fields'][k]=None;m['field_status'][k]=rng.choice(['not_asked','declined','observed']);m['field_observed_day'][k]=None
            q=ask('a',rng.choice(['constraints']+SOFT))[0]
            model.samples=rng.choice([1,2,4]); model.perturbation=rng.choice(['none','biased','refusal','subgroup_refusal','temporal_drift','overconfident','underconfident'])
            actual=model.outcomes(s,q); expected=model.outcomes_uncached(s,q)
            self.assertEqual(actual,expected)
            self.assertAlmostEqual(sum(p for p,_ in actual),1,places=14)
            # A changed counterfactual observation/status must be keyed independently.
            from graphvoi.answers import apply_answer
            changed=apply_answer(s,q,expected[0][1])
            self.assertEqual(model.outcomes(changed,q),model.outcomes_uncached(changed,q))

    def test_cache_return_values_and_assets_cannot_be_poisoned(self):
        s=state('a');hide(s,'a','relationship_goal')
        asset=dict(hard_donors=[],soft_counts={'relationship_goal':{'long_term':1,'exploring':1}})
        model=AnswerModel(asset=asset);original=model.outcomes(s,ask('a','relationship_goal')[0])
        original[0][1]['relationship_goal']='poison'
        asset['soft_counts']['relationship_goal']['long_term']=999
        model.asset['soft_counts']['relationship_goal']['long_term']=999
        self.assertEqual(model.outcomes(s,ask('a','relationship_goal')[0]),model.outcomes_uncached(s,ask('a','relationship_goal')[0]))

    def test_cache_dependencies_with_contrasting_donors(self):
        base=state('a'); donors=[]
        for index,(gender,zone,smoking) in enumerate([
                ('woman','zone_a','no'),('man','zone_b','yes'),
                ('non_binary','zone_c','occasionally')]):
            fields=copy.deepcopy(base['members'][0]['fields'])
            fields.update(smoking=smoking,age_min=20+index,age_max=40+index)
            donors.append(dict(age=30,gender=gender,zone=zone,fields=fields))
        for key in HARD:hide(base,'a',key)
        model=AnswerModel(asset=dict(hard_donors=donors,soft_counts={}),samples=3)
        original=model.outcomes(base,ask('a')[0])
        for name,value in [('age',45),('gender','man'),('zone','zone_b')]:
            changed=copy.deepcopy(base);changed['members'][0][name]=value
            fresh=model.outcomes_uncached(changed,ask('a')[0])
            self.assertNotEqual(original,fresh)
            self.assertEqual(model.outcomes(changed,ask('a')[0]),fresh)
        changed=copy.deepcopy(base);changed['members'][0]['field_status']['smoking']='declined'
        fresh=model.outcomes_uncached(changed,ask('a')[0])
        self.assertNotEqual(original,fresh)
        self.assertTrue(all('smoking' not in answer for _,answer in fresh))
        self.assertEqual(model.outcomes(changed,ask('a')[0]),fresh)
        changed['members'][0]['fields']['smoking']='yes'
        changed['members'][0]['field_status']['smoking']='observed'
        self.assertEqual(model.outcomes(changed,ask('a')[0]),model.outcomes_uncached(changed,ask('a')[0]))
        model.samples=1
        self.assertEqual(model.outcomes(base,ask('a')[0]),model.outcomes_uncached(base,ask('a')[0]))
        model.perturbation='temporal_drift';base['day']=59
        self.assertEqual(model.outcomes(base,ask('a')[0]),model.outcomes_uncached(base,ask('a')[0]))

    def test_memory_and_invocation_independence(self):
        s=state('ab'); hide(s,'a')
        outputs=[]
        for memory in (None,{},['old'],{'some':'unrelated'}):
            outputs.append(decide(dict(schema_version='1.0.0',phase='ask',state=s,memory=memory),method='graphvoi')['asks'])
        self.assertTrue(all(q==outputs[0] for q in outputs))

    def test_joint_reference_and_conditional_matches_exhaustive_small_batch(self):
        s=state('abde');hide(s,'b');hide(s,'d');hide(s,'e');s['ask_budget_remaining']=6
        f=scorer({('a','b'):10,('a','d'):9,('b','e'):11})
        model=Answers({i:[(1,{'age_min':18})] for i in 'bde'})
        singles=[ask(i)[0] for i in 'bde']
        values=[(joint_value_reference(s,list(qs),f,model),qs)
                for n in range(3) for qs in itertools.combinations(singles,n)]
        chosen=select_asks(s,f,model,world_limit=64,evaluation_limit=10000)
        self.assertEqual(joint_value_reference(s,chosen,f,model),max(v for v,_ in values))
        self.assertEqual(len({(q['member_id'],q['field']) for q in chosen}),len(chosen))
        # Duplicate input asks to the reference cost and apply once.
        self.assertEqual(joint_value_reference(s,ask('b')*2,f,model,penalty=1),7)

    def test_probabilistic_redundancy_recomputes_joint_expectation(self):
        s=state('abd');hide(s,'b');hide(s,'d');s['ask_budget_remaining']=6
        f=scorer({('a','b'):10,('a','d'):9})
        model=Answers({'b':[(.5,{'age_min':18}),(.5,{'age_min':40})], 'd':[(1,{'age_min':18})]})
        self.assertAlmostEqual(joint_value_reference(s,ask('b'),f,model),5)
        self.assertAlmostEqual(joint_value_reference(s,ask('d'),f,model),9)
        self.assertAlmostEqual(joint_value_reference(s,ask('b')+ask('d'),f,model),9.5)
        self.assertEqual(select_asks(s,f,model),ask('d')+ask('b'))

    def test_overlap_pair_residual_cost_and_complementarity(self):
        s=state('abc');[hide(s,i) for i in 'abc'];s['ask_budget_remaining']=9
        f=scorer({('a','b'):10,('b','c'):11});model=Answers({i:[(1,{'age_min':18})] for i in 'abc'})
        chosen=select_asks(s,f,model)
        self.assertEqual(chosen,ask('b')+ask('c')) # A has zero conditional gain after BC.
        self.assertEqual(sum(3 for _ in chosen),6)

    def test_distribution_cap_and_work_limit_are_deterministic(self):
        s=state('ab');[hide(s,i) for i in 'ab']
        model=Answers({i:[(.25,{'age_min':18}),(.75,{'age_min':40})] for i in 'ab'})
        worlds=counterfactuals(s,ask('a')+ask('b'),model)
        self.assertEqual(compress_worlds(worlds,8),worlds)
        reduced=compress_worlds(worlds,2)
        self.assertEqual(sum(p for p,_ in reduced),1)
        d={};q=select_asks(s,scorer({('a','b'):1}),model,diagnostics=d,evaluation_limit=2)
        self.assertEqual(q,[]);self.assertLessEqual(d['outcome_evaluations'],2)

    def test_world_quadrature_bias_is_explicit_against_exact_reference(self):
        s=state('abcd');hide(s,'a');hide(s,'b')
        f=scorer({('a','d'):10,('b','c'):10})
        model=Answers({i:[(.25,{'age_min':v}) for v in (18,19,20,40)] for i in 'ab'})
        worlds=counterfactuals(s,ask('a')+ask('b'),model)
        self.assertEqual(len(worlds),16)
        exact=joint_value_reference(s,ask('a')+ask('b'),f,model)
        self.assertEqual(exact,15) # Each independent endpoint is feasible with p=.75.
        compressed=compress_worlds(worlds,8)
        approximate=sum(p*optimal_matching(weighted_edges(w,f))[1] for p,w in compressed)
        self.assertEqual(approximate,17.5) # Systematic midpoints miss every B failure.
        self.assertEqual(approximate-exact,2.5) # Document approximation; do not claim exact batch VOI.

    def test_statistical_incomplete_invalid_duplicate_and_unequal_runs(self):
        rows=[dict(valid=True,method=m,variant=v,seed=i,msmi_per_100_arrived_members=0,
            mutual_acceptances_per_100=0,coverage=.5,ask_cost=3)
            for m in ('uncertainty_first','graphvoi') for v in ('a','b') for i in (1,2)]
        for bad,status in ((rows[:-1],'incomplete'),(rows+[copy.deepcopy(rows[0])],'duplicate')):
            result=paired_intervals(bad,replicates=20)['graphvoi']
            self.assertEqual(result['validation']['status'],status)
            self.assertIsNone(result['coverage']['ci95'])
        # Missing both policies is discoverable only from the declared design.
        result=paired_intervals(rows,replicates=20,expected_pairs={(v,i) for v in ('a','b') for i in (1,2,3)})['graphvoi']
        self.assertEqual(result['validation']['status'],'incomplete')
        self.assertEqual(len(result['validation']['missing_pairs']['graphvoi']),2)

    def test_zero_identical_and_extremely_imbalanced_scenarios(self):
        rows=[]
        for method in ('uncertainty_first','graphvoi'):
            for variant,seeds in [('a',range(100)),('b',[0])]:
                for seed in seeds:
                    rows.append(dict(valid=True,method=method,variant=variant,seed=seed,
                        msmi_per_100_arrived_members=2 if method=='graphvoi' and variant=='b' else 0,
                        mutual_acceptances_per_100=0,coverage=.5,ask_cost=3))
        result=paired_intervals(rows,replicates=40)['graphvoi']
        self.assertEqual(result['msmi_per_100_arrived_members']['delta'],1) # Equal families, not 2/101.
        self.assertEqual(result['coverage']['ci95'],[0,0])
        self.assertEqual(result['msmi_per_100_arrived_members']['ci95'],[1,1])
        self.assertFalse(result['coverage']['reliable_sample_size'])

    def test_cache_changes_age_dependency(self):
        s=state('a'); hide(s,'a')
        fields=copy.deepcopy(s['members'][0]['fields']); fields['age_min']=25
        asset=dict(hard_donors=[dict(age=30,gender='woman',zone='zone_a',fields=fields)],soft_counts={})
        model=AnswerModel(asset=asset); model.outcomes(s,ask('a')[0])
        s['members'][0]['age']=50
        self.assertEqual(model.outcomes(s,ask('a')[0]),AnswerModel(asset=asset).outcomes(s,ask('a')[0]))

    def test_redundant_batch_does_not_spend_again(self):
        s=state('abd'); hide(s,'b'); hide(s,'d'); s['ask_budget_remaining']=6
        model=Answers({i:[(1,{'age_min':18})] for i in 'bd'})
        self.assertEqual(select_asks(s,scorer({('a','b'):10,('a','d'):9}),model),ask('b'))

    def test_invalid_episode_blocks_comparison(self):
        rows=[dict(valid=True,method=m,variant='development',seed=i,
            msmi_per_100_arrived_members=0,mutual_acceptances_per_100=0,coverage=.5,ask_cost=3)
            for m in ('uncertainty_first','graphvoi') for i in (1,2)]
        rows[-1]=dict(valid=False,method='graphvoi',variant='development',seed=2,error='timeout')
        self.assertIsNone(paired_intervals(rows,replicates=10)['graphvoi']['msmi_per_100_arrived_members']['delta'])

    def test_general_runner_does_not_score_an_incomplete_prefix(self):
        from scripts.run_experiments import complete_summaries
        rows=[dict(valid=True,method='graphvoi',variant='development',seed=1)]
        result=complete_summaries(rows,['graphvoi'],{('development',1),('development',2)})
        self.assertFalse(result['graphvoi']['eligible'])
        self.assertIsNone(result['graphvoi']['primary_score'])
        self.assertEqual(result['graphvoi']['recorded_count'],1)
        rows.append(dict(valid=False,method='graphvoi',variant='development',seed=2))
        result=complete_summaries(rows,['graphvoi'],{('development',1),('development',2)})
        self.assertEqual(result['graphvoi']['invalid_count'],1)
        self.assertEqual(result['graphvoi']['reason'],'invalid')

"""Independent hand-computable public graphs; no simulator-generated fixtures."""
import copy
import math
import unittest

from kit import HARD, SOFT, OPTIONS
from graphvoi.answers import AnswerModel, apply_answer
from graphvoi.clarification import graphvoi_value, question_score, select_asks
from graphvoi.core import allocate
from graphvoi.analysis import paired_intervals


def state(names):
    fields = dict(age_min=18, age_max=65, who_to_meet=['woman', 'man', 'non_binary'],
                  relationship_structure='monogamous', smoking='no', partner_smoking='any',
                  has_children=False, partner_children='any', wants_children='unsure',
                  acceptable_zones=['zone_a'], schedule=['weekend_day'])
    fields.update({k: OPTIONS[k][0] for k in SOFT})
    return dict(schema_version='1.0.0', synthetic=True, day=0, ask_budget_remaining=12,
                introductions=[], feedback=[], ask_log=[], members=[dict(
                    member_id=i, pool_id='manual', synthetic=True, age=30, gender='woman',
                    zone='zone_a', arrived_day=0, available=True, source='synthetic_questionnaire',
                    fields=copy.deepcopy(fields), field_status={k:'observed' for k in HARD+SOFT},
                    field_observed_day={k:0 for k in HARD+SOFT}) for i in names])


def hide(s, ident, key='age_min'):
    m = next(m for m in s['members'] if m['member_id'] == ident)
    m['fields'][key] = None
    m['field_status'][key] = 'not_asked'
    m['field_observed_day'][key] = None


def ask(i, field='constraints'):
    return [dict(member_id=i, field=field)]


def scorer(edges):
    return lambda a,b,day: edges.get(tuple(sorted((a['member_id'], b['member_id']))), 0)


class Answers:
    def __init__(self, values): self.values = values
    def outcomes(self, s, q): return self.values[q['member_id']]


class IndependentAuditTests(unittest.TestCase):
    def test_A_uncertain_question_has_zero_allocation_value(self):
        s = state('abcd'); hide(s, 'a', 'relationship_goal'); hide(s, 'c')
        f = scorer({('a','b'): .8, ('c','d'): .4})
        model = Answers({'a':[(.5,{'relationship_goal':'long_term'}),(.5,{'relationship_goal':'exploring'})],
                         'c':[(1,{'age_min':18})]})
        qa, qc = ask('a','relationship_goal'), ask('c')
        self.assertAlmostEqual(question_score(s,qa,f,model,'uncertainty_first'), math.log(2))
        self.assertEqual(graphvoi_value(s,qa,f,model), 0)
        self.assertAlmostEqual(graphvoi_value(s,qc,f,model), .4)
        self.assertEqual(select_asks(s,f,model,'uncertainty_first'),qa)
        self.assertEqual(select_asks(s,f,model,'graphvoi'),qc)

    def test_B_degree_and_graphvoi_choose_different_questions(self):
        s = state('abcdefxy'); hide(s,'x'); hide(s,'y'); s['ask_budget_remaining']=3
        f = scorer({('a','b'):1,('c','d'):1,('a','x'):.1,('c','x'):.1,('e','y'):.5})
        model=Answers({i:[(1,{'age_min':18})] for i in 'xy'})
        self.assertEqual(question_score(s,ask('x'),f,model,'degree_first'),2)
        self.assertEqual(question_score(s,ask('y'),f,model,'degree_first'),1)
        self.assertEqual(graphvoi_value(s,ask('x'),f,model),0)
        self.assertAlmostEqual(graphvoi_value(s,ask('y'),f,model),.5)
        self.assertEqual(select_asks(s,f,model,'degree_first'),ask('x'))
        self.assertEqual(select_asks(s,f,model,'graphvoi'),ask('y'))

    def test_C_complementary_questions_weight_joint_probabilities(self):
        s=state('ab'); hide(s,'a'); hide(s,'b'); f=scorer({('a','b'):.8})
        model=Answers({i:[(.5,{'age_min':18}),(.5,{'age_min':40})] for i in 'ab'})
        self.assertEqual(graphvoi_value(s,ask('a'),f,model),0)
        self.assertEqual(graphvoi_value(s,ask('b'),f,model),0)
        self.assertAlmostEqual(graphvoi_value(s,ask('a')+ask('b'),f,model),.2)
        self.assertEqual(select_asks(s,f,model),ask('a')+ask('b'))
        self.assertAlmostEqual(graphvoi_value(s,ask('a')+ask('b'),f,model,penalty=.05),-.1)

    def test_D_known_violation_cannot_be_unlocked(self):
        s=state('ab'); hide(s,'a'); s['members'][1]['fields']['who_to_meet']=['man']
        f=scorer({('a','b'):100}); model=Answers({'a':[(1,{'age_min':18})]})
        self.assertEqual(graphvoi_value(s,ask('a'),f,model),0)
        self.assertEqual(select_asks(s,f,model),[])

    def test_E_new_match_displaces_old_allocation(self):
        s=state('abcd'); hide(s,'a','relationship_goal')
        def f(a,b,day):
            p=tuple(sorted((a['member_id'],b['member_id'])))
            if p==('a','c'):
                actor=a if a['member_id']=='a' else b
                return 1 if actor['fields']['relationship_goal'] is None else 10
            return {('a','b'):6,('c','d'):2,('b','d'):1}.get(p,0)
        q=ask('a','relationship_goal'); model=Answers({'a':[(1,{'relationship_goal':'long_term'})]})
        self.assertEqual(allocate(s,f),[['a','b'],['c','d']])
        after=apply_answer(s,q[0],{'relationship_goal':'long_term'})
        self.assertEqual(allocate(after,f),[['a','c'],['b','d']])
        self.assertEqual(graphvoi_value(s,q,f,model),3) # 11 - 8, not the new edge's 10.

    def test_F_every_question_zero_value_returns_no_asks(self):
        s=state('ab'); hide(s,'a','relationship_goal'); hide(s,'b','relationship_goal')
        model=Answers({i:[(.5,{'relationship_goal':'long_term'}),(.5,{'relationship_goal':'exploring'})] for i in 'ab'})
        f=scorer({('a','b'):.5})
        for i in 'ab': self.assertEqual(graphvoi_value(s,ask(i,'relationship_goal'),f,model),0)
        self.assertEqual(select_asks(s,f,model),[])

    def test_static_batch_redundancy_now_resolved(self):
        s=state('abd'); hide(s,'b'); hide(s,'d'); s['ask_budget_remaining']=6
        f=scorer({('a','b'):10,('a','d'):9})
        model=Answers({i:[(1,{'age_min':18})] for i in 'bd'})
        self.assertEqual(select_asks(s,f,model),ask('b'))
        self.assertEqual(graphvoi_value(s,ask('b')+ask('d'),f,model),10)

    def test_cache_demographic_dependency_now_resolved(self):
        s=state('a'); hide(s,'a')
        fields=copy.deepcopy(s['members'][0]['fields']); fields['age_min']=25
        asset=dict(hard_donors=[dict(age=30,gender='woman',zone='zone_a',fields=fields)],soft_counts={})
        model=AnswerModel(asset=asset); model.outcomes(s,ask('a')[0])
        s['members'][0]['age']=50
        self.assertEqual(model.outcomes(s,ask('a')[0]),model.outcomes_uncached(s,ask('a')[0]))
        self.assertEqual(model.outcomes(s,ask('a')[0])[0][1]['age_min'],45)

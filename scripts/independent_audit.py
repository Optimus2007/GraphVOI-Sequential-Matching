"""Read-only evidence checks, replaying saved actions through the official engine.

Replay validates stored evidence; it is not a new policy-performance experiment.
"""
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kit import Simulator, generate
from evaluate import summarise
from official_policy import decide as official_decide
from graphvoi.models import PairModel
from graphvoi.core import normalize
from graphvoi.clarification import candidate_actions, counterfactuals
from graphvoi.answers import AnswerModel
from scripts.run_experiments import DisclosureSimulator


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    inventory=[]
    for p in sorted(Path('results').rglob('*.json')):
        d=json.loads(p.read_text())
        if not isinstance(d,dict):
            inventory.append(dict(path=str(p),sha256=sha(p),root_type=type(d).__name__,items=len(d)))
            continue
        rows=d.get('episodes',d.get('full_episodes',[]))
        inventory.append(dict(path=str(p),sha256=sha(p),complete=d.get('complete'),
            episodes=len(rows),valid=sum(bool(r.get('valid')) for r in rows),
            trace='actions' in d, keys=sorted(d)))
    frozen=json.loads(Path('docs/STARTER_SNAPSHOT.json').read_text())
    changed=[]; unchanged=0
    mapping={'policy.py':'official_policy.py','Dockerfile':'Dockerfile.starter',
             'requirements.txt':'requirements.starter.txt',
             '.github/workflows/verify.yml':'.github/workflows/verify.yml.starter'}
    for row in frozen['files']:
        p=Path(mapping.get(row['path'],row['path']))
        if not p.exists(): changed.append(row['path']+': missing'); continue
        b=p.read_bytes(); digest=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
        if digest != row['git_blob_sha1']: changed.append(row['path'])
        else: unchanged+=1
    vendor=json.loads(Path('vendor/PROVENANCE.json').read_text())
    vendor_ok=all(sha(Path('vendor/networkx',p))==v for p,v in vendor['sha256'].items())
    pair=PairModel(); beliefs=AnswerModel(); dependencies={}; collisions=[]
    original=beliefs.outcomes
    def audited_outcomes(s,q):
        m=next(m for m in s['members'] if m['member_id']==q['member_id'])
        key=(s['day'],q['member_id'],q['field'],json.dumps(m['fields'],sort_keys=True))
        meta=(m['age'],m['gender'],m['zone'],json.dumps(m['field_status'],sort_keys=True))
        if key in beliefs.cache and dependencies.get(key)!=meta:
            actual=original(s,q)
            fresh=AnswerModel(asset=beliefs.asset).outcomes(s,q)
            collisions.append(dict(day=s['day'],member_id=q['member_id'],
                                   field=q['field'],answers_differ=actual!=fresh))
        dependencies[key]=meta
        return original(s,q)
    beliefs.outcomes=audited_outcomes
    replay=[]; model_errors=[]
    source=json.loads(Path('results/paired_smoke.json').read_text())
    for method in source['summaries']:
        assert source['summaries'][method]==summarise([r for r in source['episodes'] if r['method']==method])
    # Preserve runner order, including cross-method answer-cache reuse.
    paths=[Path('results/paired_smoke_traces')/f"{r['variant']}_{r['seed']}_{r['method']}.json" for r in source['episodes']]
    paths+=sorted(Path('results/robustness_smoke_traces').glob('*.json'))
    for p in paths:
        t=json.loads(p.read_text()); row=t['metrics']; actual=row.get('actual_disclosure','none')
        world=generate(row['seed'],200,'evaluation',row['variant'])
        if actual!='none':
            class ChangedDisclosure(DisclosureSimulator):
                subgroup='non_binary' if actual=='subgroup' else None
                drift=actual=='drift'
            sim=ChangedDisclosure(world)
        else: sim=Simulator(world)
        baseline_equal=True; digest=hashlib.sha256()
        for a in t['actions']:
            assert sim.day==a['day']
            s=sim.observe(); action=a['action']; phase=a['phase']
            digest.update(json.dumps([phase,sim.day,action],sort_keys=True).encode())
            if row['method'] in ('greedy','no_asks','random'):
                expected=official_decide(dict(state=s,phase=phase,memory=None),row['method'])
                baseline_equal &= expected['asks' if phase=='ask' else 'pairs']==action
            if '--skip-cache-probe' not in sys.argv and p.parent.name=='paired_smoke_traces' and phase=='ask' and row['method'] in ('uncertainty_first','degree_first','graphvoi','graphvoi_no_pairs','graphvoi_wait'):
                clean=normalize(s)
                for candidate in candidate_actions(clean,pair,paired=row['method']!='graphvoi_no_pairs'):
                    if row['method']=='uncertainty_first':
                        for q in candidate: beliefs.outcomes(clean,q)
                    else: counterfactuals(clean,candidate,beliefs)
            if phase=='ask': sim.resolve_asks(action)
            else:
                members={m['member_id']:m for m in s['members']}
                records={tuple(sorted((r['introduction']['user_a'],r['introduction']['user_b']))):r
                         for r in t['predictions'] if r['introduction']['assigned_day']==s['day']}
                assert set(records)=={tuple(sorted(q)) for q in action}
                for q in action:
                    r=records[tuple(sorted(q))]
                    expected=pair.stages(members[q[0]],members[q[1]],s['day'])
                    assert all(abs(expected[k]-r['prediction'][k])<1e-12 for k in expected),(p,q)
                sim.advance(action)
        for _ in range(40): sim.advance([])
        metrics=sim.metrics()
        keys=('assignments','mutual_acceptances','dates','mutual_second_meeting_intention','missing_feedback','ask_cost')
        assert all(metrics[k]==row[k] for k in keys),(p,metrics,row)
        assert digest.hexdigest()==row['action_sha256']
        assert 100*metrics['mutual_second_meeting_intention']/200==row['msmi_per_100_arrived_members']
        first={}
        for intro in sim.introductions:
            for i in (intro['user_a'],intro['user_b']):first.setdefault(i,intro['assigned_day'])
        arrived={m['member_id']:m['arrived_day'] for m in sim.observe()['members']}
        assert len(first)/200==row['coverage']
        assert sorted(first[i]-arrived[i] for i in first)==row['first_introduction_wait_days']
        labels=t['calibration_labels']
        records={r['introduction']['introduction_id']:r for r in t['predictions']}
        for label in labels:
            record=records[label['introduction_id']]; intro=record['introduction']
            ident=intro['user_a'] if label['direction']=='a_accepts_b' else intro['user_b']
            es=[e for e in sim.receive_feedback() if e['introduction_id']==label['introduction_id']
                and e['event']=='introduction_response' and e['member_id']==ident]
            assert len(es)==1 and label['y']==int(es[0]['value']=='yes' and es[0]['observed_day']<=intro['response_deadline_day'])
            assert label['p']==record['prediction'][label['direction']]
        if labels:
            brier=sum((r['p']-r['y'])**2 for r in labels)/len(labels)
            loss=sum(-math.log(r['p'] if r['y'] else 1-r['p']) for r in labels)/len(labels)
        else:brier=loss=None
        for record in t['predictions']:
            assert set(record['prediction'])=={'a_accepts_b','b_accepts_a','mutual_acceptance','date_given_mutual','timely_seconds_given_date'}
        replay.append(dict(path=str(p),valid=True,baseline_actions_equal=baseline_equal,
                           labels=len(labels),brier=brier,log_loss=loss))
        assert baseline_equal,p
    result=dict(inventory=inventory,upstream_unchanged_files=unchanged,
                upstream_changed_or_missing=changed,vendor_files=len(vendor['sha256']),vendor_hashes_ok=vendor_ok,
                replayed_episodes=len(replay),replays=replay,cache_dependency_collisions=collisions,
                saved_summaries_recomputed=True,saved_predictions_and_labels_recomputed=True,
                cache_probe_executed='--skip-cache-probe' not in sys.argv,
                caveat='Replay is evidence verification, not another independent performance sample.')
    if '--skip-cache-probe' in sys.argv:
        original_probe=json.loads(Path('results/independent_evidence.json').read_text())
        result['previous_full_cache_probe_collisions']=original_probe['cache_dependency_collisions']
        result['previous_full_cache_probe_executed']=True
    Path('results/independent_evidence.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('inventory','replays')}))


if __name__=='__main__':main()

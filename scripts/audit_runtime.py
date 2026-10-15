"""Fresh process determinism, protocol size and measured local peak RSS."""
import copy
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from kit import Simulator, generate
from tests.test_independent_audit import state, hide
from evaluate import validate_response


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='results/independent_runtime.json')
    args=parser.parse_args()
    sim=Simulator(generate(61002,200,'audit_runtime'))
    for _ in range(20):sim.advance([])
    normal=sim.observe()
    dense=state([f'm{i:03}' for i in range(200)])
    blocked=state('ab'); hide(blocked,'a'); blocked['members'][0]['field_status']['age_min']='declined'
    cases=[('empty',state('')),('single',state('a')),('declined',blocked),
           ('normal_day20',normal),('dense_200',dense)]
    rows=[]
    for name,s in cases:
        for phase in ('ask','match'):
            results=[]
            for hashseed in (1,77):
                req=dict(schema_version='1.0.0',phase=phase,state=s,memory={'roundtrip':['x',False,3]})
                env=dict(os.environ,PYTHONHASHSEED=str(hashseed),PYTHONDONTWRITEBYTECODE='1')
                start=time.perf_counter()
                wrapper="import runpy,resource,sys; runpy.run_path('policy.py',run_name='__main__'); print(str(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)+' maximum resident set size',file=sys.stderr)"
                p=subprocess.run([sys.executable,'-c',wrapper],input=json.dumps(req),
                                 text=True,capture_output=True,env=env,timeout=10)
                elapsed=time.perf_counter()-start
                assert p.returncode==0,(name,p.stderr)
                r=validate_response(json.loads(p.stdout),phase)
                assert len(p.stdout.encode())<=1048576
                peak=re.search(r'(\d+)\s+maximum resident set size',p.stderr)
                results.append(r)
                rows.append(dict(case=name,phase=phase,hashseed=hashseed,seconds=elapsed,
                    peak_rss_bytes=int(peak[1]) if peak else None,response_bytes=len(p.stdout.encode()),
                    action_sha256=hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()))
            assert results[0]==results[1],name
    request=dict(schema_version='1.0.0',phase='match',state=normal,memory='x'*750000)
    p=subprocess.run([sys.executable,'policy.py'],input=json.dumps(request),text=True,capture_output=True,timeout=10)
    assert p.returncode==0 and json.loads(p.stdout)['memory']==request['memory']
    corrupt=dict(request,schema_version='bad',memory=None)
    p=subprocess.run([sys.executable,'policy.py'],input=json.dumps(corrupt),text=True,capture_output=True,timeout=10)
    assert p.returncode!=0 and not p.stdout
    out=dict(profiles=rows,hashseed_repeatability=True,large_memory_roundtrip_bytes=750000,
             unsupported_schema_rejected=True,container_resources_enforced=False,
             note='macOS resource.getrusage peak RSS bytes in policy process; measured invocations only, not Docker certification. /usr/bin/time -l was blocked by sysctl restrictions.')
    Path(args.output).write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(dict(invocations=len(rows)+2,max_seconds=max(r['seconds'] for r in rows),
                         max_rss_bytes=max(r['peak_rss_bytes'] or 0 for r in rows))))


if __name__=='__main__':main()

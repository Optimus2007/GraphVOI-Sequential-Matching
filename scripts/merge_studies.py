"""Merge parts of one pre-registered study that ran on different machines.

Each part must have identical policy/runner code and model assets. Cells that
appear in more than one part must have identical action hashes (the policy is
deterministic); the first listed part supplies them. The merged matrix must be
exactly the declared design. Traces are linked into one folder for the export.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate import VARIANTS
from graphvoi.analysis import paired_intervals
from scripts.compare_studies import same_code
from scripts.run_pilot import aggregate


def main():
    p = argparse.ArgumentParser()
    p.add_argument('parts', nargs='+', help='raw study JSON files, highest priority first')
    p.add_argument('--seeds', required=True, help='lo-hi of the declared design')
    p.add_argument('--output', required=True)
    args = p.parse_args()
    lo, hi = map(int, args.seeds.split('-'))
    seeds = list(range(lo, hi + 1))
    parts = [json.loads(Path(f).read_text()) for f in args.parts]
    for other in parts[1:]:
        same_code(parts[0], other)
    methods = tuple(parts[0]['expected_design']['methods'])
    cells, source, overlap, mismatches = {}, {}, 0, []
    for path, part in zip(args.parts, parts):
        if tuple(part['expected_design']['methods']) != methods:
            raise SystemExit(f'{path}: different method list')
        for r in part['episodes']:
            key = (r['method'], r['variant'], r['seed'])
            if key in cells:
                overlap += 1
                if r.get('action_sha256') != cells[key].get('action_sha256'):
                    mismatches.append(key)
                continue
            cells[key] = r
            source[key] = path
    if mismatches:
        raise SystemExit(f'Determinism check failed for {len(mismatches)} cells, e.g. {mismatches[:3]}')
    expected = {(m, v, s) for m in methods for v in VARIANTS for s in seeds}
    missing, extra = expected - set(cells), set(cells) - expected
    if missing or extra:
        raise SystemExit(f'Matrix mismatch: {len(missing)} missing, {len(extra)} unexpected')
    order = lambda r: (VARIANTS.index(r['variant']), r['seed'], methods.index(r['method']))
    rows = sorted(cells.values(), key=order)
    result = aggregate(rows, methods, seeds, VARIANTS)
    if result['paired_intervals'] is not None and 'graphvoi_nofill' in methods:
        result['paired_intervals']['graphvoi_nofill'] = paired_intervals(
            rows, reference='graphvoi_nofill', expected_methods=methods,
            expected_pairs={(v, s) for v in VARIANTS for s in seeds})
    keep = ('purpose', 'mode', 'startup_included', 'python_version', 'code_sha256', 'asset_sha256',
            'decision_days', 'follow_up_days', 'members_per_episode', 'acquisition')
    result.update({k: parts[0].get(k) for k in keep})
    result['merged_from'] = [dict(file=Path(f).name, episodes_used=sum(1 for v in source.values() if v == f),
                                  python_version=part.get('python_version'), workers=part.get('workers'),
                                  elapsed_seconds=part.get('elapsed_seconds'))
                             for f, part in zip(args.parts, parts)]
    result['cross_machine_overlap'] = dict(cells=overlap, identical_action_hashes=overlap)
    out = Path(args.output)
    out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    traces = out.parent / (out.stem + '_traces')
    traces.mkdir(exist_ok=True)
    for (m, v, s), f in source.items():
        src = Path(f).parent / (Path(f).stem + '_traces') / f'{v}_{s}_{m}.json'
        dst = traces / src.name
        if src.exists() and not dst.exists():
            dst.symlink_to(src.resolve())
    print(json.dumps(dict(output=str(out), episodes=len(rows), overlap_checked=overlap,
                          invalid=sum(not r.get('valid') for r in rows), sources=result['merged_from']), indent=1))


if __name__ == '__main__':
    main()

"""Deterministic local source archive; explicit allowlist keeps research/secrets local."""
import gzip
import hashlib
import json
from pathlib import Path
import tarfile


def main():
    root = Path(__file__).resolve().parents[1]
    required = ['docs/REPORT.md', 'results/paired_smoke.json', 'results/analysis_summary.json',
                'results/robustness_smoke.json', 'results/graphvoi_protocol_final.json']
    for name in required:
        if not (root / name).exists():
            raise ValueError(f'Missing reviewed packaging input: {name}')
    for name in ('paired_smoke.json', 'robustness_smoke.json'):
        if not json.loads((root / 'results' / name).read_text()).get('complete'):
            raise ValueError(f'Incomplete results: {name}')
    protocol = json.loads((root / 'results/graphvoi_protocol_final.json').read_text())
    if len(protocol['episodes']) != 6 or not protocol['summary']['eligible']:
        raise ValueError('Official subprocess verification must pass all six scenarios')
    top = ['.dockerignore', '.gitignore', 'policy.py', 'official_policy.py', 'kit.py',
           'evaluate.py', 'verify_data.py', 'build_public_data.py', 'organise.py',
           'test_kit.py', 'test_release.py', 'test_runner.py', 'Dockerfile',
           'Dockerfile.starter', 'requirements.txt', 'requirements.starter.txt',
           'README.md', 'PROBLEM_STATEMENT.md', 'CHANGELOG.md', 'LICENSE',
           'DATA_LICENSE.md', 'data_manifest.json', 'data_checksums.json']
    files = {root / name for name in top}
    for folder in ('graphvoi', 'scripts', 'tests', 'assets', 'vendor', 'docs', 'data', 'examples', '.github'):
        files.update(p for p in (root / folder).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and p.suffix != '.pyc' and p.name != '.DS_Store')
    for name in ('paired_smoke.json', 'paired_smoke_traces', 'robustness_smoke.json',
                 'robustness_smoke_traces', 'graphvoi_protocol_final.json',
                 'phase1_all_scenarios.json', 'audit_greedy.json', 'analysis_summary.json',
                 'calibration.png', 'calibration.svg', 'profile_final.json', 'dense_pool_check.json'):
        p = root / 'results' / name
        if p.is_dir():
            files.update(q for q in p.rglob('*') if q.is_file())
        elif p.exists():
            files.add(p)
    output = root / 'output'
    output.mkdir(exist_ok=True)
    archive = output / 'GraphVOI_Orbit_Round2_candidate.tar.gz'
    with archive.open('wb') as raw, gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w') as tar:
            for p in sorted(files):
                relative = p.relative_to(root).as_posix()
                if p.is_symlink() or 'research' in p.parts:
                    raise ValueError(f'Unexpected package input: {relative}')
                info = tar.gettarinfo(str(p), arcname='GraphVOI/' + relative)
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = ''
                with p.open('rb') as stream:
                    tar.addfile(info, stream)
    sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(archive.suffix + '.sha256').write_text(f'{sha}  {archive.name}\n')
    print(json.dumps(dict(archive=str(archive), sha256=sha, files=len(files),
                         note='Local candidate only; Docker validation, large paired study and publication remain outstanding.')))


if __name__ == '__main__':
    main()

"""Optional scientific plot; matplotlib is analysis-only, never an inference dependency."""
import argparse
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', default='results/analysis_summary.json')
    p.add_argument('--output', default='results/calibration')
    args = p.parse_args()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    data = json.loads(Path(args.input).read_text())
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), constrained_layout=True)
    for ax, direction in zip(axes, ('a_accepts_b', 'b_accepts_a')):
        ax.plot([0, 1], [0, 1], color='#999999', linestyle='--', linewidth=1)
        for method in ('uncertainty_first', 'degree_first', 'graphvoi'):
            if method not in data['calibration']:
                continue
            result = data['calibration'][method]['directions'][direction]
            bins = [b for b in result['reliability'] if b['count']]
            ax.plot([b['predicted'] for b in bins], [b['observed'] for b in bins],
                    marker='o', label=f"{method} (n={result['count']})")
        ax.set(xlim=(0, 1), ylim=(0, 1), xlabel='Predicted recorded Yes probability',
               ylabel='Observed Yes fraction', title=direction.replace('_', ' '))
        ax.legend(fontsize=7)
    fig.suptitle('Held-out public smoke calibration; not evidence of a policy win', fontsize=10)
    base = Path(args.output)
    base.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(base.with_suffix('.png'), dpi=180)
    fig.savefig(base.with_suffix('.svg'))


if __name__ == '__main__':
    main()

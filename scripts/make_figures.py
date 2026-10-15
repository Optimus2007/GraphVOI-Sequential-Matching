"""Report figures from the committed results/<study>/summary.json files.

Needs matplotlib (requirements-analysis.txt). Each method keeps one colour in
every figure; missing studies are skipped with a message, never faked.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path('docs/figures')
COLOR = {'graphvoi': '#2a78d6', 'degree_first': '#eb6834', 'uncertainty_first': '#1baf7a',
         'greedy': '#eda100', 'graphvoi_nofill': '#e87ba4', 'random': '#008300',
         'no_asks': '#4a3aa7', 'learned_maxweight': '#e34948'}
LABEL = {'graphvoi': 'GraphVOI', 'degree_first': 'Degree-first', 'uncertainty_first': 'Uncertainty-first',
         'greedy': 'Official greedy', 'graphvoi_nofill': 'GraphVOI, no fill', 'random': 'Official random',
         'no_asks': 'Official no-asks', 'learned_maxweight': 'Learned + max-weight',
         'learned_greedy': 'Learned + greedy', 'graphvoi_wait': 'GraphVOI + wait',
         'graphvoi_no_pairs': 'GraphVOI, no pairs'}
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e4e3df'

plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
                     'font.size': 9, 'mathtext.fontset': 'stix', 'axes.edgecolor': MUTED,
                     'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': .6,
                     'legend.frameon': False, 'savefig.bbox': 'tight'})


def load(name):
    path = Path('results') / name / 'summary.json'
    if not path.exists():
        print('skip, missing', path)
        return None
    return json.loads(path.read_text())


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ('pdf', 'png'):
        fig.savefig(OUT / f'{name}.{ext}', dpi=200)
    plt.close(fig)
    print('wrote', OUT / name)


def spend(pilot, confirm):
    panels = [(s, t, ms) for s, t, ms in
              ((pilot, 'v2 pilot (seeds 62001 to 62010)', ('greedy', 'uncertainty_first', 'degree_first', 'graphvoi')),
               (confirm, 'v3 confirmatory (seeds 71001 to 71100)', ('greedy', 'graphvoi_nofill', 'graphvoi')))
              if s and s.get('daily_ask_units')]
    if not panels:
        return
    fig, axes = plt.subplots(1, len(panels), figsize=(3.4 * len(panels), 2.2), sharey=True, squeeze=False)
    for ax, (s, title, methods) in zip(axes[0], panels):
        for m in methods:
            y = s['daily_ask_units'].get(m)
            if y:
                ax.plot(range(60), y, color=COLOR[m], lw=2, label=LABEL[m])
        ax.axhline(12, color=MUTED, lw=.8, ls=':')
        ax.text(59, 12.3, 'daily cap', ha='right', va='bottom', color=MUTED, fontsize=7)
        ax.set_title(title, fontsize=9, color=INK)
        ax.set_xlabel('decision day')
        ax.set_ylim(0, 14)
        ax.legend(fontsize=7, loc='center right')
    axes[0][0].set_ylabel('ask units spent (mean)')
    save(fig, 'daily_ask_spend')


def forest(confirm):
    if not confirm or not confirm.get('paired_intervals'):
        return
    rows = []
    for ref in ('degree_first', 'uncertainty_first', 'greedy', 'random', 'no_asks', 'graphvoi_nofill'):
        r = confirm['paired_intervals'].get(ref, {}).get('graphvoi', {})
        if r.get('msmi_per_100_arrived_members', {}).get('status') == 'complete':
            rows.append((ref, r['msmi_per_100_arrived_members'], r['mutual_acceptances']))
    if not rows:
        return
    fig, axes = plt.subplots(1, 2, figsize=(7, .32 * len(rows) + .9), sharey=True)
    for ax, k, title in ((axes[0], 1, 'MSMI per 100 arrived (primary)'),
                         (axes[1], 2, 'Mutual acceptances per episode (H1b)')):
        for i, row in enumerate(rows):
            r = row[k]
            y = len(rows) - 1 - i
            if r.get('ci97_5_bonferroni2'):
                ax.plot(r['ci97_5_bonferroni2'], [y, y], color=GRID, lw=6, solid_capstyle='round')
            ax.plot(r['ci95'], [y, y], color=COLOR['graphvoi'], lw=2)
            ax.plot([r['delta']], [y], 'o', ms=6, color=COLOR['graphvoi'], mec='white', mew=1.5)
        ax.axvline(0, color=INK, lw=.8)
        ax.set_title(title, fontsize=9)
        ax.set_xlabel('GraphVOI minus comparator')
        ax.grid(axis='y', visible=False)
    axes[0].set_yticks(range(len(rows)), [LABEL[r[0]] for r in rows][::-1])
    axes[0].text(0.02, -0.28, 'Line: 95% paired interval. Wide grey band: Bonferroni 97.5% (primary rule).',
                 transform=axes[0].transAxes, fontsize=7, color=MUTED)
    save(fig, 'paired_differences')


def calibration(confirm):
    if not confirm or not confirm.get('calibration'):
        return
    c = confirm['calibration'].get('graphvoi')
    fig, ax = plt.subplots(figsize=(3.2, 3))
    ax.plot([0, 1], [0, 1], color=MUTED, lw=.8, ls=':')
    for key, label, color, marker in (('a_accepts_b', 'A accepts B', COLOR['graphvoi'], 'o'),
                                      ('b_accepts_a', 'B accepts A', COLOR['degree_first'], 's')):
        # Bins with fewer than 30 labels are too noisy to plot.
        bins = [b for b in c[key]['reliability'] if b['count'] >= 30]
        ax.plot([b['predicted'] for b in bins], [b['observed'] for b in bins], marker=marker, ms=6,
                color=color, lw=2, mec='white', mew=1, label=f"{label} (Brier {c[key]['brier']:.3f})")
    ax.set_xlim(.2, .6)
    ax.set_ylim(.2, .6)
    ax.set_xlabel('predicted probability')
    ax.set_ylabel('observed recorded Yes rate')
    ax.legend(fontsize=7, loc='upper left')
    ax.set_title('Directional calibration, GraphVOI episodes', fontsize=9)
    save(fig, 'calibration')


def waiting(confirm):
    if not confirm or not confirm.get('opportunity'):
        return
    methods = [m for m in ('greedy', 'graphvoi_nofill', 'degree_first', 'uncertainty_first', 'graphvoi')
               if m in confirm['opportunity']]
    groups = [('gender', g) for g in ('woman', 'man', 'non_binary')] + \
             [('age_band', a) for a in ('21-29', '30-39', '40+')]
    fig, ax = plt.subplots(figsize=(7, 2.2))
    width = .8 / len(methods)
    for j, m in enumerate(methods):
        ys = [confirm['opportunity'][m][d][g]['servable_km_served_within_14_days'] for d, g in groups]
        ax.bar([i + (j - (len(methods) - 1) / 2) * width for i in range(len(groups))], ys,
               width=width - .02, color=COLOR[m], label=LABEL[m], edgecolor='white', linewidth=1)
    ax.set_xticks(range(len(groups)), [g.replace('_', '-') for _, g in groups])
    ax.set_ylabel('share served within 14 days')
    ax.set_title('Servable members first introduced within 14 days of arrival (Kaplan-Meier)', fontsize=9)
    ax.legend(fontsize=7, ncol=len(methods), loc='upper center', bbox_to_anchor=(.5, -.12))
    ax.grid(axis='x', visible=False)
    save(fig, 'waiting_by_group')


def calibration_waiting(confirm):
    """Organisers' third question in one figure: calibration (left), waiting (right)."""
    if not confirm or not confirm.get('calibration') or not confirm.get('opportunity'):
        return
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(7.2, 2.5), gridspec_kw={'width_ratios': [1, 2.3]})
    c = confirm['calibration']['graphvoi']
    ax.plot([0, 1], [0, 1], color=MUTED, lw=.8, ls=':')
    for key, label, color, marker in (('a_accepts_b', 'A accepts B', COLOR['graphvoi'], 'o'),
                                      ('b_accepts_a', 'B accepts A', COLOR['degree_first'], 's')):
        # Bins with fewer than 30 labels are too noisy to plot.
        bins = [b for b in c[key]['reliability'] if b['count'] >= 30]
        ax.plot([b['predicted'] for b in bins], [b['observed'] for b in bins], marker=marker, ms=5,
                color=color, lw=2, mec='white', mew=1, label=label)
    ax.set_xlim(.25, .55)
    ax.set_ylim(.25, .55)
    ax.set_xlabel('predicted')
    ax.set_ylabel('observed Yes rate')
    ax.set_title('Directional calibration', fontsize=9)
    ax.legend(fontsize=7, loc='upper left')
    methods = [m for m in ('greedy', 'graphvoi_nofill', 'degree_first', 'uncertainty_first', 'graphvoi')
               if m in confirm['opportunity']]
    groups = [('gender', g) for g in ('woman', 'man', 'non_binary')] + \
             [('age_band', a) for a in ('21-29', '30-39', '40+')]
    width = .8 / len(methods)
    for j, m in enumerate(methods):
        ys = [confirm['opportunity'][m][d][g]['servable_km_served_within_14_days'] for d, g in groups]
        bx.bar([i + (j - (len(methods) - 1) / 2) * width for i in range(len(groups))], ys,
               width=width - .02, color=COLOR[m], label=LABEL[m], edgecolor='white', linewidth=1)
    bx.set_xticks(range(len(groups)), [g.replace('_', '-') for _, g in groups])
    bx.set_ylabel('introduced within 14 days')
    bx.set_title('Who waits: servable members, Kaplan-Meier', fontsize=9)
    bx.set_ylim(0, .68)
    bx.legend(fontsize=6.5, ncol=3, loc='upper center', frameon=False)
    bx.grid(axis='x', visible=False)
    fig.tight_layout()
    save(fig, 'calibration_waiting')


def main():
    pilot, confirm = load('pilot_v2'), load('confirmatory')
    spend(pilot, confirm)
    forest(confirm)
    calibration(confirm)
    waiting(confirm)
    calibration_waiting(confirm)


if __name__ == '__main__':
    main()

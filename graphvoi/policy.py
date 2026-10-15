"""Public-observation-only policy; no simulator access or persistent writes."""
from functools import lru_cache
import time
from .core import allocate, available_members, first_asks, normalize

METHODS = ('safe_core', 'learned_greedy', 'learned_maxweight', 'uncertainty_first',
           'degree_first', 'graphvoi', 'graphvoi_no_pairs', 'graphvoi_wait', 'graphvoi_nofill')
# Seconds after decide() starts; leaves margin for startup within the 10 s limit.
ASK_DEADLINE_SECONDS = 6.0


@lru_cache(maxsize=1)
def pair_model():
    from .models import PairModel
    return PairModel()


@lru_cache(maxsize=8)
def answer_model(perturbation):
    from .answers import AnswerModel
    return AnswerModel(perturbation=perturbation)


def decide(request, scorer=None, solver='optimal', wait_threshold=0.0,
           method='safe_core', perturbation='none', fill=True):
    started = time.perf_counter()
    if request.get('schema_version') != '1.0.0':
        raise ValueError('Unsupported request schema')
    state = normalize(request['state'])
    if method not in METHODS:
        raise ValueError('Unknown method')
    if request['phase'] not in ('ask', 'match'):
        raise ValueError('Unknown phase')
    if not available_members(state):
        return {'asks' if request['phase'] == 'ask' else 'pairs': [],
                'memory': request.get('memory') if request.get('memory') is not None else {}}
    if scorer is None and method != 'safe_core':
        scorer = pair_model()
    if method == 'learned_greedy':
        solver = 'greedy'
    if method == 'graphvoi_nofill':
        # Ablation: VOI-ranked asks only, unused units left unspent (v2 behaviour).
        fill = False
    if method == 'graphvoi_wait':
        # Prespecified conservative prior threshold, no test-set tuning.
        wait_threshold = .025
    memory = request.get('memory')
    if memory is None:
        memory = {}
    if request['phase'] == 'ask':
        if method in ('safe_core', 'learned_greedy', 'learned_maxweight'):
            asks = first_asks(state)
        else:
            from .clarification import fill_hard_budget, select_asks
            strategy = method if method in ('uncertainty_first', 'degree_first') else 'graphvoi'
            diagnostics = {}
            beliefs = answer_model(perturbation)
            beliefs.clear_cache() # Match real stateless invocation/episode isolation.
            asks = select_asks(state, scorer, beliefs, strategy,
                               paired=method != 'graphvoi_no_pairs', diagnostics=diagnostics,
                               deadline=started + ASK_DEADLINE_SECONDS)
            if fill and 'fallback' not in diagnostics:
                # Shared by all selectors; only the ranked prefix differs.
                asks = fill_hard_budget(state, scorer, asks)
            if 'fallback' in diagnostics:
                memory = dict(memory) if isinstance(memory, dict) else {'previous_memory': memory}
                memory['orbit_fallback_count'] = memory.get('orbit_fallback_count', 0) + 1
                memory['orbit_last_fallback'] = diagnostics['fallback']
            if diagnostics.get('deadline'):
                memory = dict(memory) if isinstance(memory, dict) else {'previous_memory': memory}
                memory['orbit_deadline_count'] = memory.get('orbit_deadline_count', 0) + 1
        return {'asks': asks, 'memory': memory}
    if request['phase'] != 'match':
        raise ValueError('Unknown phase')
    kwargs = dict(solver=solver, wait_threshold=wait_threshold)
    if scorer is not None:
        kwargs['scorer'] = scorer
    return {'pairs': allocate(state, **kwargs), 'memory': memory}

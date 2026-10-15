"""Safe public-state graph construction and exact reciprocal allocation."""
import copy
import itertools
import math

import networkx as nx
from kit import HARD, SOFT, eligibility


def normalize(state):
    """Copy public inputs; refuse contradictory/declined observations conservatively."""
    if state.get('schema_version') != '1.0.0' or state.get('synthetic') is not True:
        raise ValueError('Unsupported observation contract')
    out = copy.deepcopy(state)
    seen = set()
    for m in out['members']:
        if m['member_id'] in seen:
            raise ValueError('Duplicate member ID')
        seen.add(m['member_id'])
        for key in HARD + SOFT:
            status = m['field_status'].get(key)
            day = m['field_observed_day'].get(key)
            if status != 'observed' or day is None or day > state['day']:
                m['fields'][key] = None
    return out


def available_members(state):
    occupied = set()
    # Availability is the official engine's operational truth. Also protect the
    # mandatory seven-day response window against contradictory inputs.
    for intro in state['introductions']:
        if state['day'] <= intro['response_deadline_day']:
            occupied.update((intro['user_a'], intro['user_b']))
    return sorted((m for m in state['members'] if m['available']
                   and m['arrived_day'] <= state['day']
                   and m['member_id'] not in occupied), key=lambda m: m['member_id'])


def past_pairs(state):
    return {tuple(sorted((i['user_a'], i['user_b']))) for i in state['introductions']}


def public_pairs(state, unresolved=False):
    past = past_pairs(state)
    for a, b in itertools.combinations(available_members(state), 2):
        key = (a['member_id'], b['member_id'])
        if key in past:
            continue
        status = eligibility(a, b)['status']
        if status == 'feasible' or unresolved and status == 'needs_clarification':
            yield a, b, status


def pair_features(actor, other, day):
    """Directed features; IDs, latent state, seeds and future events are excluded."""
    values = [1.0, (actor['age'] - 33) / 13, (other['age'] - 33) / 13,
              abs(actor['age'] - other['age']) / 25,
              min(60, max(0, day - actor['arrived_day'])) / 60,
              min(60, max(0, day - other['arrived_day'])) / 60]
    for key in SOFT:
        a, b = actor['fields'].get(key), other['fields'].get(key)
        values.extend([float(a is not None and b is not None and a == b),
                       float(a is None), float(b is None)])
    # Actor/partner categorical observations preserve directional distinctions.
    for m in (actor, other):
        values.extend(float(m['gender'] == g) for g in ('woman', 'man', 'non_binary'))
        values.extend(float(m['fields'].get('emotional_availability') == v)
                      for v in ('ready', 'taking_time'))
    return values


def initial_utility(a, b, day):
    """Untrained bounded similarity prior, explicitly not a calibrated probability."""
    known = [(a['fields'].get(k), b['fields'].get(k)) for k in SOFT]
    evidence = sum(1 if x == y else -0.5 for x, y in known
                   if x is not None and y is not None)
    return 0.5 + evidence / (3 * len(SOFT))


def weighted_edges(state, scorer=initial_utility):
    edges = {}
    for a, b, _ in public_pairs(state):
        score = float(scorer(a, b, state['day']))
        if not math.isfinite(score):
            raise ValueError('Non-finite utility')
        if score > 0:
            edges[(a['member_id'], b['member_id'])] = score
    return edges


def optimal_matching(edges):
    """Exact weighted blossom. Sorted insertion makes solver ties deterministic.

    Do not perturb primary utilities to break ties: tiny perturbations can change
    the mathematical optimum. Canonical node/edge order fixes reproducible ties.
    """
    graph = nx.Graph()
    graph.add_nodes_from(sorted({i for pair in edges for i in pair}))
    for (a, b), weight in sorted(edges.items()):
        if a == b or not math.isfinite(weight) or weight < 0:
            raise ValueError('Invalid weighted edge')
        graph.add_edge(a, b, weight=weight)
    pairs = sorted(tuple(sorted(p)) for p in
                   nx.max_weight_matching(graph, maxcardinality=False, weight='weight'))
    return pairs, math.fsum(edges[p] for p in pairs)


def greedy_matching(edges):
    used, pairs = set(), []
    for pair, _ in sorted(edges.items(), key=lambda item: (-item[1], item[0])):
        if not used.intersection(pair):
            pairs.append(pair)
            used.update(pair)
    return sorted(pairs)


def validate_pairs(state, pairs):
    allowed = {m['member_id']: m for m in available_members(state)}
    used, past = set(), past_pairs(state)
    out = []
    for pair in pairs:
        a, b = pair
        if (a == b or a not in allowed or b not in allowed or used.intersection(pair)
                or tuple(sorted(pair)) in past
                or eligibility(allowed[a], allowed[b])['status'] != 'feasible'):
            raise ValueError('Unsafe allocation')
        used.update(pair)
        out.append(list(sorted(pair)))
    return sorted(out)


def allocate(state, scorer=initial_utility, solver='optimal', wait_threshold=0.0):
    edges = weighted_edges(state, scorer)
    # The threshold decreases toward zero at the official decision horizon.
    threshold = wait_threshold * max(0.0, (59 - state['day']) / 59)
    edges = {p: v for p, v in edges.items() if v >= threshold}
    pairs = (optimal_matching(edges)[0] if solver == 'optimal' else greedy_matching(edges))
    return validate_pairs(state, pairs)


def legal_asks(state):
    """Never reask a refusal or request a fully observed field."""
    asked_today = {(q['member_id'], q['field']) for q in state['ask_log']
                   if q['observed_day'] == state['day']}
    out = []
    for m in available_members(state):
        ident = m['member_id']
        hard_unknown = any(m['fields'][k] is None for k in HARD)
        hard_declined = any(m['field_status'][k] == 'declined' for k in HARD)
        if hard_unknown and not hard_declined and (ident, 'constraints') not in asked_today:
            out.append({'member_id': ident, 'field': 'constraints'})
        # A hard refusal permanently blocks all introductions in this release.
        if hard_declined:
            continue
        for key in SOFT:
            if (m['fields'][key] is None and m['field_status'][key] == 'not_asked'
                    and (ident, key) not in asked_today):
                out.append({'member_id': ident, 'field': key})
    return out


def ask_cost(ask):
    return 3 if ask['field'] == 'constraints' else 1


def first_asks(state):
    budget, out = state['ask_budget_remaining'], []
    for ask in legal_asks(state):
        if ask['field'] == 'constraints' and ask_cost(ask) <= budget:
            out.append(ask)
            budget -= ask_cost(ask)
    return out

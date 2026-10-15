"""Small JSON logistic models. Targets are recorded events, not latent preferences."""
import json
import math
from pathlib import Path

from .core import pair_features

ASSETS = Path(__file__).resolve().parents[1] / 'assets'


def sigmoid(z):
    return 1 / (1 + math.exp(-max(-35, min(35, z))))


def predict(model, features):
    return sigmoid(sum(w * x for w, x in zip(model['weights'], features)))


def symmetric_features(a, b, day):
    x, y = pair_features(a, b, day), pair_features(b, a, day)
    return [(u + v) / 2 for u, v in zip(x, y)]


def fit_logistic(rows, dimensions, iterations=100, penalty=0.05):
    positives = sum(y for _, y in rows)
    prior = (positives + 1) / (len(rows) + 2)
    weights = [math.log(prior / (1 - prior))] + [0.0] * (dimensions - 1)
    # Empirical intercept with explicit support flags, not invented training.
    sufficient = len(rows) >= 50 and positives >= 5 and len(rows) - positives >= 5
    if sufficient:
        for _ in range(iterations):
            gradient = [0.0] * dimensions
            for features, y in rows:
                error = sigmoid(sum(w * x for w, x in zip(weights, features))) - y
                for j, value in enumerate(features):
                    gradient[j] += error * value
            for j in range(dimensions):
                weights[j] -= 0.4 * (gradient[j] / len(rows) +
                                    (penalty * weights[j] if j else 0.0))
    return dict(weights=weights, count=len(rows), positives=positives,
                fitted_features=sufficient, target='specified_by_asset_stage')


class PairModel:
    def __init__(self, asset=None):
        self.asset = asset or json.loads((ASSETS / 'pair_model.json').read_text())

    def stages(self, a, b, day):
        models = self.asset['models']
        x = symmetric_features(a, b, day)
        return dict(a_accepts_b=predict(models['directional_acceptance'], pair_features(a, b, day)),
                    b_accepts_a=predict(models['directional_acceptance'], pair_features(b, a, day)),
                    mutual_acceptance=predict(models['mutual_acceptance'], x),
                    date_given_mutual=predict(models['date_given_mutual'], x),
                    timely_seconds_given_date=predict(models['timely_seconds_given_date'], x))

    def __call__(self, a, b, day):
        p = self.stages(a, b, day)
        # Joint acceptance is learned directly; no directional independence claim.
        return p['mutual_acceptance'] * p['date_given_mutual'] * p['timely_seconds_given_date']

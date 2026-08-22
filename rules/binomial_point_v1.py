"""Estimator binomial-point-v1: point estimate with a Wilson score interval.

This module is content-addressed by every metric definition that declares it, so
it MUST contain the computation those definitions claim. Before rc3 it computed
only the point estimate while the interval lived in the verifier's own library,
which meant Section 8.7's requirement to recompute under the declared estimator
could not be satisfied by executing the declared estimator.

Determinism, stated normatively because an independent implementation cannot
guess it: z is the fixed constant below, not a quantile computed at runtime, and
the association order of the arithmetic is the order written here. Conformance is
agreement within a absolute tolerance of 1e-9, not bit equality, because bit
equality across languages and libmath implementations is not achievable and
demanding it would make an independent implementation impossible. The tolerance is
absolute rather than relative because these values are probabilities bounded in
[0, 1], where an absolute bound is the meaningful one and where a relative bound
degenerates as the estimate approaches zero.
"""
RULE_ID = "binomial-point-v1"
INTERVAL_METHOD = "Wilson"
LEVEL = 0.95
TOLERANCE = 1e-9

# Two-sided normal quantiles, fixed as constants rather than computed, so that
# no implementation depends on a particular quantile routine.
Z = {0.95: 1.959963984540054, 0.99: 2.5758293035489004}


def estimate(n, d):
    return None if d == 0 else n / d


def interval(n, d, level=LEVEL):
    """Wilson score interval. Association order below is normative."""
    if d == 0:
        return None
    z = Z[level]
    p = n / d
    denom = 1 + z * z / d
    center = (p + z * z / (2 * d)) / denom
    half = (z / denom) * ((p * (1 - p) / d + z * z / (4 * d * d)) ** 0.5)
    return {"lower": max(0.0, center - half), "upper": min(1.0, center + half),
            "level": level, "method": INTERVAL_METHOD}

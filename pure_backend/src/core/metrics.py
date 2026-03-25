"""Provide lightweight in-process metrics counters for operational visibility."""

from collections import Counter

_COUNTERS: Counter[str] = Counter()


def increment(metric: str, amount: int = 1) -> None:
    _COUNTERS[metric] += amount


def snapshot() -> dict[str, int]:
    return dict(_COUNTERS)

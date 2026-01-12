from functools import partial
from typing import Any, Callable, Dict, Generic, TypeVar

import pytest

K = TypeVar("K")
V = TypeVar("V")

class PartialDict(Generic[K, V], Dict[K, V]):
    """
    An assertion helper for testing that all keys in the given `PartialDict`
    are present, and have equal values, in a dict that it is compared against.
    May be compared using either the <= operator (for direct use in
    assertions) or the == operator (when part of a more complex object
    hierarchy).

    >>> PartialDict({'a': 1}) <= {'a': 1, 'b': 2}
    True

    >>> PartialDict({'a': 1}) <= {'a': 2, 'b': 2}
    False

    >>> PartialDict({'a': 1}) <= {'b': 2}
    False

    >>> [42, PartialDict({'a': 1})] == [42, {'a': 1, 'b': 2}]
    True

    >>> [42, PartialDict({'a': 1})] == [42, {'b': 2}]
    False
    """
    def __le__(self, other: object) -> bool:
        if isinstance(other, dict):
            return self.items() <= other.items()
        return NotImplemented

    def __eq__(self, other: object):
        return self.__le__(other)

    @staticmethod
    def assertrepr_compare(
        config: pytest.Config, op: str, left: object, right: object
    ) -> list[str]:
        from _pytest._io.saferepr import saferepr, saferepr_unlimited
        from _pytest.assertion.util import assertrepr_compare

        verbose = config.get_verbosity(pytest.Config.VERBOSITY_ASSERTIONS)
        if verbose > 1:
            repr_: Callable[[Any], str] = saferepr_unlimited
        else:
            maxsize = (80 - 15 - len(op) - 2) // 2
            repr_ = partial(saferepr, maxsize=maxsize)

        summary = f"{repr_(left)} {op} {repr_(right)}"

        def subdict(sup: dict, sub: PartialDict) -> dict:
            return {k: v for k, v in sup.items() if k in sub}

        if isinstance(left, PartialDict):
            assert op == "<="
            assert isinstance(right, dict)
            res = assertrepr_compare(config, "==", left, subdict(right, left))
        else:
            assert op == ">="
            assert isinstance(right, PartialDict)
            assert isinstance(left, dict)
            res = assertrepr_compare(config, "==", subdict(left, right), right)

        assert res
        return [summary, *res[1:]]


def pytest_assertrepr_compare(
    config: pytest.Config, op: str, left: object, right: object
) -> list[str] | None:
    if isinstance(left, PartialDict) or isinstance(right, PartialDict):
        return PartialDict.assertrepr_compare(config, op, left, right)
    return None

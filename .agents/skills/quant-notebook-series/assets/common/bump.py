"""Bump-and-reval utilities. Quotes are always restored (try/finally)."""
from __future__ import annotations

from typing import Callable


def bump_and_reval(quote, reval: Callable[[], float], bump: float,
                   scheme: str = "central", relative: bool = False) -> float:
    """First derivative of `reval()` with respect to a SimpleQuote.

    `reval` must read live market objects (instrument priced off Handles) so the
    bump propagates. scheme: 'forward' or 'central'. relative=True scales the bump
    by the quote's current value.
    """
    x0 = quote.value()
    h = bump * x0 if relative else bump
    try:
        if scheme == "forward":
            base = reval()
            quote.setValue(x0 + h)
            up = reval()
            return (up - base) / h
        if scheme == "central":
            quote.setValue(x0 + h)
            up = reval()
            quote.setValue(x0 - h)
            dn = reval()
            return (up - dn) / (2 * h)
        raise ValueError(f"unknown scheme: {scheme}")
    finally:
        quote.setValue(x0)


def bump_and_reval_second(quote, reval: Callable[[], float], bump: float,
                          relative: bool = False) -> float:
    """Second derivative (gamma-type) by central differences."""
    x0 = quote.value()
    h = bump * x0 if relative else bump
    try:
        base = reval()
        quote.setValue(x0 + h)
        up = reval()
        quote.setValue(x0 - h)
        dn = reval()
        return (up - 2 * base + dn) / (h * h)
    finally:
        quote.setValue(x0)

"""Tests for book maturity utility helpers."""
from __future__ import annotations

import pytest

from api.app.modules.book.application.utils.maturity import derive_maturity_from_score
from api.app.modules.book.domain import BookMaturity


@pytest.mark.parametrize(
    "score,expected",
    [
        (0, BookMaturity.SEED),
        (29, BookMaturity.SEED),
        (30, BookMaturity.GROWING),
        (59, BookMaturity.GROWING),
        (60, BookMaturity.STABLE),
        (89, BookMaturity.STABLE),
        (90, BookMaturity.LEGACY),
        (105, BookMaturity.LEGACY),
    ],
)
def test_derive_maturity_from_score(score: int, expected: BookMaturity) -> None:
    assert derive_maturity_from_score(score) == expected

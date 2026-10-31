from datetime import date

from app.services.quiz import pick_item


def test_same_day_always_picks_same_item():
    day = date(2026, 11, 1)
    assert pick_item([1, 2, 3, 4], set(), day) == pick_item([4, 3, 2, 1], set(), day)


def test_skips_recent_items():
    day = date(2026, 11, 1)
    assert pick_item([1, 2, 3], {1, 2}, day) == 3


def test_reuses_items_when_all_are_recent():
    day = date(2026, 11, 1)
    assert pick_item([1, 2], {1, 2}, day) in {1, 2}

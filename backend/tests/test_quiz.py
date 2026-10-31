from app.services.quiz import fallback_quiz_text, is_correct, pick_random


def test_random_pick_avoids_previous_item():
    for _ in range(50):
        assert pick_random([1, 2, 3], exclude=2) in {1, 3}


def test_random_pick_works_with_single_item():
    assert pick_random([7], exclude=7) == 7


def test_correct_within_tolerance():
    assert is_correct(1050, 1000, 0.10)
    assert is_correct(900, 1000, 0.10)
    assert not is_correct(1200, 1000, 0.10)


def test_fallback_text_hides_price():
    text = fallback_quiz_text({"name_ko": "생수 500ml 1병", "unit": "500ml 1병"})
    assert "생수" in text.question and "₩" not in text.question

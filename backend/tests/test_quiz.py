from app.services.quiz import QuizText, fallback_quiz_text, grade, is_valid_text, make_question, pick_random


def test_random_pick_avoids_previous_item():
    for _ in range(50):
        assert pick_random([1, 2, 3], exclude=2) in {1, 3}


def test_random_pick_works_with_single_item():
    assert pick_random([7], exclude=7) == 7


def test_question_matches_exact_template():
    assert make_question("soju", "소주 360ml, 1병") == "Guess how much soju (소주 360ml, 1병) normally costs in Seoul?"


def test_grade_right_near_wrong_in_both_directions():
    assert grade(1050, 1000, 0.10, 0.25) == "right"
    assert grade(950, 1000, 0.10, 0.25) == "right"
    assert grade(1200, 1000, 0.10, 0.25) == "near"
    assert grade(800, 1000, 0.10, 0.25) == "near"
    assert grade(1400, 1000, 0.10, 0.25) == "wrong"
    assert grade(600, 1000, 0.10, 0.25) == "wrong"


def test_fallback_has_empty_tip_and_no_price():
    text = fallback_quiz_text({"name_ko": "생수 500ml 1병", "unit": "500ml 1병"})
    question = make_question(text.name_en, "생수 500ml 1병")
    assert text.tip == ""
    assert "생수" in question and "₩" not in question


def test_rejects_llm_text_that_breaks_the_format():
    assert is_valid_text(QuizText(name_en="instant ramyeon", tip="Buy multipacks at a large supermarket."))
    assert not is_valid_text(QuizText(name_en="instant ramyeon", tip="Buy 5 packs at once."))
    assert not is_valid_text(QuizText(name_en="라면", tip="Buy multipacks at a large supermarket."))
    assert not is_valid_text(QuizText(name_en="one two three four five", tip="Buy multipacks."))
    assert not is_valid_text(QuizText(name_en="instant ramyeon", tip=" ".join(["word"] * 21)))

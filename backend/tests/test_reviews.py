import pytest
from pydantic import ValidationError

from app.routers.reviews import PasswordBody, ReviewCreate, ReviewUpdate
from app.services.reviews import AttemptLimiter, clean_search_term, hash_password, verify_password


def test_password_hash_roundtrip():
    h = hash_password("1234")
    assert h != "1234"
    assert verify_password("1234", h)
    assert not verify_password("4321", h)
    assert not verify_password("1234", "not-a-bcrypt-hash")


def test_clean_search_term_strips_filter_syntax():
    assert clean_search_term("bibimbap") == "bibimbap"
    assert clean_search_term("김밥),id.eq.(1") == "김밥  id eq  1"
    assert clean_search_term("*%") == ""
    assert clean_search_term(None) == ""


def test_limiter_blocks_after_max_failures_and_resets():
    limiter = AttemptLimiter(max_failures=2, window_seconds=60)
    assert not limiter.is_blocked("ip", 1)
    limiter.record_failure("ip", 1)
    limiter.record_failure("ip", 1)
    assert limiter.is_blocked("ip", 1)
    assert not limiter.is_blocked("ip", 2)  # 다른 리뷰는 영향 없음
    limiter.reset("ip", 1)
    assert not limiter.is_blocked("ip", 1)


def test_review_create_requires_exactly_one_store():
    base = {"password": "1234", "title": "t", "body": "b"}
    with pytest.raises(ValidationError):
        ReviewCreate(**base)
    with pytest.raises(ValidationError):
        ReviewCreate(**base, store_id=1, store={"name": "가게", "category": "cafe"})
    assert ReviewCreate(**base, store_id=1).store_id == 1


def test_review_create_defaults_blank_nickname():
    r = ReviewCreate(password="1234", title="t", body="b", store_id=1, nickname="  ")
    assert r.nickname == "Anonymous"
    assert ReviewCreate(password="1234", title="t", body="b", store_id=1).nickname == "Anonymous"


def test_review_rejects_bad_values():
    with pytest.raises(ValidationError):
        ReviewCreate(password="12", title="t", body="b", store_id=1)  # 비밀번호 너무 짧음
    with pytest.raises(ValidationError):
        ReviewCreate(password="1234", title="t", body="b", store_id=1, rating=6)
    with pytest.raises(ValidationError):
        ReviewUpdate(password="1234", price_feeling="very cheap")


def test_password_limit_is_bytes_not_chars():
    # 한글 24자 = 72바이트는 통과, 25자 = 75바이트는 거절 (bcrypt 72바이트 한도)
    ReviewCreate(password="가" * 24, title="t", body="b", store_id=1)
    with pytest.raises(ValidationError):
        ReviewCreate(password="가" * 25, title="t", body="b", store_id=1)
    with pytest.raises(ValidationError):
        PasswordBody(password="a" * 73)
    assert verify_password("가" * 25, hash_password("1234")) is False  # 500 대신 False

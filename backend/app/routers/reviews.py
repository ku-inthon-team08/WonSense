from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import AfterValidator, BaseModel, Field, field_validator, model_validator
from supabase import Client

from app.db.supabase import get_supabase
from app.routers.stores import StoreCreate, find_or_create_store
from app.services.reviews import (
    REVIEW_COLUMNS,
    clean_search_term,
    hash_password,
    password_limiter,
    verify_password,
)

router = APIRouter(prefix="/api/reviews", tags=["reviews"])

PriceFeeling = Literal["cheap", "fair", "expensive"]

# bcrypt는 72바이트까지만 받으므로(5.0부터는 넘으면 ValueError) UTF-8 바이트 기준으로 막는다.
# max_length는 글자 수라서 한글(3바이트)이면 25자부터 72바이트를 넘는다.
PASSWORD_MAX_BYTES = 72


def _password_bytes_limit(v: str) -> str:
    if len(v.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise ValueError(f"비밀번호는 UTF-8 기준 {PASSWORD_MAX_BYTES}바이트 이하여야 합니다")
    return v


Password = Annotated[str, Field(min_length=4), AfterValidator(_password_bytes_limit)]


class StoreRef(BaseModel):
    """가게 태그: 기존 가게 id 또는 새 가게 정보 중 하나만 보낸다."""

    store_id: int | None = None
    store: StoreCreate | None = None

    @model_validator(mode="after")
    def one_store(self):
        if self.store_id is not None and self.store is not None:
            raise ValueError("store_id와 store 중 하나만 보내야 합니다")
        return self


class ReviewCreate(StoreRef):
    # validate_default: 닉네임을 아예 안 보내도 default_nickname이 돌아 'Anonymous'가 된다
    nickname: str | None = Field(None, max_length=30, validate_default=True)
    password: Password
    title: str = Field(min_length=1, max_length=100)
    body: str = Field(min_length=1, max_length=5000)
    paid_price: int | None = Field(None, ge=0)
    price_feeling: PriceFeeling | None = None
    rating: int | None = Field(None, ge=1, le=5)

    @field_validator("nickname")
    @classmethod
    def default_nickname(cls, v: str | None) -> str:
        return (v or "").strip() or "Anonymous"

    @model_validator(mode="after")
    def requires_store(self):
        if self.store_id is None and self.store is None:
            raise ValueError("store_id 또는 store가 필요합니다")
        return self


class ReviewUpdate(StoreRef):
    """보낸 필드만 바꾼다. 비밀번호 자체는 바꿀 수 없다."""

    password: Password
    nickname: str | None = Field(None, max_length=30)
    title: str | None = Field(None, min_length=1, max_length=100)
    body: str | None = Field(None, min_length=1, max_length=5000)
    paid_price: int | None = Field(None, ge=0)
    price_feeling: PriceFeeling | None = None
    rating: int | None = Field(None, ge=1, le=5)


class PasswordBody(BaseModel):
    password: Password


def _client_id(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _resolve_store_id(supabase: Client, ref: StoreRef) -> int | None:
    if ref.store is not None:
        return find_or_create_store(supabase, ref.store)["id"]
    if ref.store_id is not None:
        found = supabase.table("stores").select("id").eq("id", ref.store_id).execute().data
        if not found:
            raise HTTPException(status_code=404, detail="가게를 찾을 수 없습니다")
        return ref.store_id
    return None


def _get_review(supabase: Client, review_id: int) -> dict:
    rows = supabase.table("reviews").select(REVIEW_COLUMNS).eq("id", review_id).execute().data
    if not rows:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다")
    return rows[0]


def _check_password(supabase: Client, request: Request, review_id: int, password: str) -> None:
    client = _client_id(request)
    if password_limiter.is_blocked(client, review_id):
        raise HTTPException(status_code=429, detail="비밀번호를 너무 많이 틀렸습니다. 잠시 후 다시 시도하세요")
    rows = supabase.table("reviews").select("password_hash").eq("id", review_id).execute().data
    if not rows:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다")
    if not verify_password(password, rows[0]["password_hash"]):
        password_limiter.record_failure(client, review_id)
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다")
    password_limiter.reset(client, review_id)


@router.get("")
def list_reviews(
    q: str = Query("", description="제목·본문·가게 이름 검색어"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    supabase: Client = Depends(get_supabase),
) -> dict:
    query = supabase.table("reviews").select(REVIEW_COLUMNS, count="exact")

    term = clean_search_term(q)
    if term:
        conditions = [f"title.ilike.*{term}*", f"body.ilike.*{term}*"]
        store_ids = [
            s["id"]
            for s in supabase.table("stores").select("id").ilike("name", f"%{term}%").limit(100).execute().data
        ]
        if store_ids:
            conditions.append(f"store_id.in.({','.join(map(str, store_ids))})")
        query = query.or_(",".join(conditions))

    start = (page - 1) * size
    res = query.order("created_at", desc=True).range(start, start + size - 1).execute()
    return {"items": res.data, "total": res.count or 0, "page": page, "size": size}


@router.get("/{review_id}")
def get_review(review_id: int, supabase: Client = Depends(get_supabase)) -> dict:
    return _get_review(supabase, review_id)


@router.post("", status_code=201)
def create_review(review: ReviewCreate, supabase: Client = Depends(get_supabase)) -> dict:
    store_id = _resolve_store_id(supabase, review)
    data = review.model_dump(exclude={"password", "store", "store_id"})
    inserted = (
        supabase.table("reviews")
        .insert({**data, "store_id": store_id, "password_hash": hash_password(review.password)})
        .execute()
        .data[0]
    )
    return _get_review(supabase, inserted["id"])


@router.post("/{review_id}/verify")
def verify_review_password(
    review_id: int,
    body: PasswordBody,
    request: Request,
    supabase: Client = Depends(get_supabase),
) -> dict:
    """수정 화면에 들어가기 전에 비밀번호만 확인한다."""
    _check_password(supabase, request, review_id, body.password)
    return {"ok": True}


@router.patch("/{review_id}")
def update_review(
    review_id: int,
    review: ReviewUpdate,
    request: Request,
    supabase: Client = Depends(get_supabase),
) -> dict:
    _check_password(supabase, request, review_id, review.password)

    changes = review.model_dump(exclude_unset=True, exclude={"password", "store", "store_id"})
    for required in ("title", "body"):  # null로 비울 수 없는 컬럼
        if changes.get(required, "") is None:
            changes.pop(required)
    if "nickname" in changes:
        changes["nickname"] = (changes["nickname"] or "").strip() or "Anonymous"
    store_id = _resolve_store_id(supabase, review)
    if store_id is not None:
        changes["store_id"] = store_id

    if changes:
        supabase.table("reviews").update(changes).eq("id", review_id).execute()
    return _get_review(supabase, review_id)


@router.delete("/{review_id}", status_code=204)
def delete_review(
    review_id: int,
    body: PasswordBody,
    request: Request,
    supabase: Client = Depends(get_supabase),
) -> Response:
    _check_password(supabase, request, review_id, body.password)
    supabase.table("reviews").delete().eq("id", review_id).execute()
    return Response(status_code=204)

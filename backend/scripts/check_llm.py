"""LLM 연결 점검: 지금 .env 설정(LLM_BASE_URL / LLM_API_KEY / LLM_MODEL)으로 실제 호출이 되는지 본다.

    python -m scripts.check_llm                 # 텍스트 호출만
    python -m scripts.check_llm menu.jpg        # 사진 판독까지 (바가지 판독기와 같은 경로)

사진 판독은 모델이 이미지 입력을 지원해야 한다. 텍스트는 되는데 사진에서 실패하면 그 모델은 비전을 지원하지 않는 것이다.
"""
import base64
import mimetypes
import sys
from pathlib import Path

from app.core.claude import get_claude, get_llm_model
from app.core.config import get_settings


def main() -> None:
    s = get_settings()
    client, model = get_claude(), get_llm_model()
    print(f"endpoint: {s.llm_base_url or 'Claude API (기본)'}")
    print(f"model:    {model}")

    res = client.messages.create(model=model, max_tokens=50, messages=[{"role": "user", "content": "Reply with: pong"}])
    print("text:    ", "".join(b.text for b in res.content if b.type == "text").strip())

    if len(sys.argv) > 1:
        from app.routers.items import get_items  # noqa: PLC0415 - DB가 필요할 때만 불러온다
        from app.db.supabase import get_supabase  # noqa: PLC0415
        from app.services.scan import extract_lines  # noqa: PLC0415

        path = sys.argv[1]
        media_type = mimetypes.guess_type(path)[0] or "image/jpeg"
        image = base64.b64encode(Path(path).read_bytes()).decode()
        lines = extract_lines(client, image, media_type, get_items(get_supabase()), model)
        print(f"image:    {len(lines)}개 품목")
        for line in lines:
            print(f"  - {line.name} ({line.name_en}) ₩{line.price:,} item_id={line.item_id}")


if __name__ == "__main__":
    main()

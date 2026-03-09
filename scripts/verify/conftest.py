"""
공통 설정 — HostOS에서 Docker 노출 포트로 접근
"""
import io
import pytest
from PIL import Image, ImageDraw

API_URL = "http://localhost:3000"
AI_URL  = "http://localhost:8000"
ES_URL  = "http://localhost:9200"
KB_URL  = "http://localhost:5601"


@pytest.fixture(scope="session")
def sample_image_bytes() -> bytes:
    """OCR 테스트용 영양성분표 샘플 이미지 (PNG bytes)"""
    img = Image.new("RGB", (420, 320), color="white")
    draw = ImageDraw.Draw(img)
    lines = [
        "Nutrition Facts",
        "Product: Greek Yogurt",
        "Serving Size 150g",
        "",
        "Calories 100",
        "Total Fat 0g",
        "Protein 17g",
        "Total Carbohydrate 6g",
        "Sodium 65mg",
    ]
    y = 20
    for line in lines:
        draw.text((20, y), line, fill="black")
        y += 30
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

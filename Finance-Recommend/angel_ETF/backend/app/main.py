from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.routes.comparison import router as comparison_router

app = FastAPI(title="angel_ETF", version="0.1.0", description="고정 CSV 자료를 이용한 조건 기반 ETF 비교")
app.include_router(comparison_router, prefix="/api")

INDEX_PATH = Path(__file__).resolve().parents[2] / "frontend" / "index.html"


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(INDEX_PATH, media_type="text/html; charset=utf-8")

from fastapi import APIRouter

from app.api.schemas.comparison import RecommendationRequest
from app.api.schemas.result import RecommendationResponse
from app.services.recommendation_service import recommend_etfs

router = APIRouter()


@router.post("/recommendations", response_model=RecommendationResponse, summary="조건 기반 ETF 추천")
def create_recommendations(request: RecommendationRequest) -> RecommendationResponse:
    """고정 CSV 자료에서 조건에 맞는 ETF를 점수순으로 반환합니다."""
    return RecommendationResponse(**recommend_etfs(request))

from typing import Any

from pydantic import BaseModel, ConfigDict


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conditions: dict[str, Any]
    total_count: int
    passed_count: int
    excluded_count: int
    exclusion_reason_counts: dict[str, int]
    exclusions: list[dict[str, Any]]
    most_filtered_conditions: list[str]
    recommendations: list[dict[str, Any]]
    message: str
    disclaimer: str

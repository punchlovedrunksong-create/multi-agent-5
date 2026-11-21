from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.core.config import DEFAULT_RESULT_COUNT, MAX_RESULT_COUNT


Industry = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    budget_krw: Annotated[int, Field(gt=0)]
    industries: list[Industry] = Field(default_factory=list, max_length=50)
    result_count: Annotated[int, Field(ge=1, le=MAX_RESULT_COUNT)] = DEFAULT_RESULT_COUNT
    risk_profile: Literal["안정형", "중립형", "공격형"] = "중립형"

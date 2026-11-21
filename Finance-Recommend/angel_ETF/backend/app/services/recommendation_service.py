import csv
import math
from collections import Counter
from pathlib import Path
from typing import Any

from app.api.schemas.comparison import RecommendationRequest
from app.core.config import (
    DEFAULT_RESULT_COUNT,
    DISCLAIMER,
    ETF_CSV_PATH,
    METRIC_LABELS,
    RISK_PROFILE_WEIGHTS,
)

METRICS = ("return", "volatility", "max_drawdown")
METRIC_DIRECTIONS = {"return": 1, "volatility": -1, "max_drawdown": -1}


def _preference_value(metric: str, value: float) -> float:
    # 최대 낙폭은 손실률(대개 음수)이므로 절댓값이 작을수록 안전 점수가 높습니다.
    if metric == "max_drawdown":
        return -abs(value)
    return METRIC_DIRECTIONS[metric] * value


def load_etfs(path: Path = ETF_CSV_PATH) -> list[dict[str, Any]]:
    """고정 CSV fixture를 ETF 레코드 목록으로 읽습니다."""
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _optional_number(value: Any) -> float | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _normalise_etf(raw: dict[str, Any]) -> dict[str, Any]:
    price = _optional_number(raw.get("price_krw"))
    market_cap = _optional_number(raw.get("market_cap_krw"))
    industry_raw = raw.get("industry")
    industry = str(industry_raw).strip() if industry_raw is not None else ""
    return {
        "etf_code": str(raw.get("etf_code", "")).strip(),
        "etf_name": str(raw.get("etf_name", "")).strip(),
        "price_krw": int(price) if price is not None and price.is_integer() else price,
        "industry": industry or None,
        # 시가총액 미제공은 0으로 취급해 확인된 시가총액보다 우선하지 않게 합니다.
        "market_cap_krw": market_cap if market_cap is not None else 0.0,
        **{metric: _optional_number(raw.get(metric)) for metric in METRICS},
    }


def _percentile_scores(candidates: list[dict[str, Any]], metric: str) -> dict[str, float]:
    """최선 100, 최악 0의 후보군 내 min-max 순위 점수(동점은 평균 순위)."""
    available = [candidate for candidate in candidates if candidate[metric] is not None]
    if not available:
        return {}
    ordered = sorted(
        available,
        key=lambda candidate: _preference_value(metric, candidate[metric]),
        reverse=True,
    )
    count = len(ordered)
    scores: dict[str, float] = {}
    index = 0
    while index < count:
        end = index + 1
        key_value = _preference_value(metric, ordered[index][metric])
        while end < count and _preference_value(metric, ordered[end][metric]) == key_value:
            end += 1
        average_rank = ((index + 1) + end) / 2
        score = 100.0 if count == 1 else 100.0 * (count - average_rank) / (count - 1)
        for candidate in ordered[index:end]:
            scores[candidate["etf_code"]] = score
        index = end
    return scores


def recommend_etfs(
    request: RecommendationRequest,
    etfs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """조건 필터링, 상대 점수 산출, 정렬 및 추천 근거 생성을 수행합니다."""
    raw_etfs = load_etfs() if etfs is None else etfs
    all_candidates = [_normalise_etf(raw) for raw in raw_etfs]
    exclusion_counts: Counter[str] = Counter()
    exclusions: list[dict[str, str]] = []
    eligible: list[dict[str, Any]] = []
    selected_industries = set(request.industries)

    def exclude(candidate: dict[str, Any], reason: str) -> None:
        exclusion_counts[reason] += 1
        exclusions.append({"etf_code": candidate["etf_code"], "etf_name": candidate["etf_name"], "reason": reason})

    for candidate in all_candidates:
        price = candidate["price_krw"]
        if price is None:
            exclude(candidate, "데이터 부족")
            continue
        if price > request.budget_krw:
            exclude(candidate, "예산 초과")
            continue

        industry = candidate["industry"]
        if selected_industries:
            if industry is None:
                exclude(candidate, "데이터 부족")
                continue
            if industry not in selected_industries:
                exclude(candidate, "산업 불일치")
                continue
        else:
            industry = industry or "기타"
        candidate["industry"] = industry

        if all(candidate[metric] is None for metric in METRICS):
            exclude(candidate, "데이터 부족")
            continue
        eligible.append(candidate)

    metric_scores = {metric: _percentile_scores(eligible, metric) for metric in METRICS}
    weights = RISK_PROFILE_WEIGHTS[request.risk_profile]
    for candidate in eligible:
        available_metrics = [metric for metric in METRICS if candidate[metric] is not None]
        available_weight = sum(weights[metric] for metric in available_metrics)
        components: dict[str, dict[str, float | None]] = {}
        for metric in METRICS:
            score = metric_scores[metric].get(candidate["etf_code"])
            contribution = score * weights[metric] / available_weight if score is not None else None
            components[metric] = {
                "value": candidate[metric],
                "score": round(score, 2) if score is not None else None,
                "weight": round(weights[metric] / available_weight, 4) if score is not None else None,
                "contribution": round(contribution, 2) if contribution is not None else None,
            }
        candidate["score_components"] = components
        candidate["total_score"] = round(sum(
            (metric_scores[metric].get(candidate["etf_code"], 0.0) or 0.0)
            * weights[metric] / available_weight
            for metric in available_metrics
        ), 2)
        candidate["passed_conditions"] = ["가격 정보 확인", "1주 가격이 예산 이하"]
        if selected_industries:
            candidate["passed_conditions"].append("선택 산업 중 하나 이상 일치")
        else:
            candidate["passed_conditions"].append("산업 조건 미선택(전체 산업)")
        candidate["special_treatments"] = []
        missing_labels = [METRIC_LABELS[m] for m in METRICS if candidate[m] is None]
        if missing_labels:
            candidate["special_treatments"].append("일부 지표 결측: " + ", ".join(missing_labels))
        if candidate["industry"] == "기타":
            candidate["special_treatments"].append("산업 정보 없음 → 기타 처리")

    # 동점은 시가총액 내림차순, 다시 동점이면 종목코드 오름차순으로 정렬합니다.
    eligible.sort(key=lambda item: (-item["total_score"], -item["market_cap_krw"], item["etf_code"]))
    tie_groups: dict[float, list[dict[str, Any]]] = {}
    for candidate in eligible:
        tie_groups.setdefault(candidate["total_score"], []).append(candidate)
    for tied in tie_groups.values():
        if len(tied) < 2:
            continue
        for index, candidate in enumerate(tied):
            previous = tied[index - 1] if index else None
            following = tied[index + 1] if index + 1 < len(tied) else None
            if any(
                other is not None and other["market_cap_krw"] == candidate["market_cap_krw"]
                for other in (previous, following)
            ):
                reason = "동점 처리: 종목코드"
            else:
                reason = "동점 처리: 시가총액"
            candidate["special_treatments"].append(reason)

    reason_counts = dict(sorted(exclusion_counts.items()))
    most_filtered = []
    if not eligible and reason_counts:
        most_count = max(reason_counts.values())
        most_filtered = [reason for reason, count in reason_counts.items() if count == most_count]

    result_count = request.result_count or DEFAULT_RESULT_COUNT
    recommendations = []
    for rank, candidate in enumerate(eligible[:result_count], start=1):
        recommendations.append({
            "rank": rank,
            "etf_code": candidate["etf_code"],
            "etf_name": candidate["etf_name"],
            "price_krw": candidate["price_krw"],
            "industry": candidate["industry"],
            "market_cap_krw": candidate["market_cap_krw"],
            "total_score": candidate["total_score"],
            "score_components": candidate["score_components"],
            "passed_conditions": candidate["passed_conditions"],
            "special_treatments": candidate["special_treatments"],
        })

    return {
        "conditions": {
            "budget_krw": request.budget_krw,
            "industries": request.industries,
            "result_count": result_count,
            "risk_profile": request.risk_profile,
        },
        "total_count": len(all_candidates),
        "passed_count": len(eligible),
        "excluded_count": len(all_candidates) - len(eligible),
        "exclusion_reason_counts": reason_counts,
        "exclusions": exclusions,
        "most_filtered_conditions": most_filtered,
        "recommendations": recommendations,
        "message": "조건에 맞는 종목 없음" if not recommendations else "조건에 맞는 ETF 추천 결과입니다.",
        "disclaimer": DISCLAIMER,
    }

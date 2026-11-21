from fastapi.testclient import TestClient

from app.main import app
from app.api.schemas.comparison import RecommendationRequest
from app.services.recommendation_service import recommend_etfs

client = TestClient(app)


def request(**overrides):
    data = {"budget_krw": 100_000}
    data.update(overrides)
    return RecommendationRequest(**data)


def etf(code, **overrides):
    data = {
        "etf_code": code,
        "etf_name": code,
        "price_krw": 10_000,
        "industry": "반도체",
        "market_cap_krw": 1_000,
        "return": 10,
        "volatility": 10,
        "max_drawdown": -10,
    }
    data.update(overrides)
    return data


def test_normal_request_returns_ranked_evidence_and_defaults():
    response = client.post("/api/recommendations", json={"budget_krw": 100_000})
    assert response.status_code == 200
    data = response.json()
    assert data["conditions"]["result_count"] == 5
    assert data["conditions"]["risk_profile"] == "중립형"
    assert len(data["recommendations"]) <= 5
    assert [item["total_score"] for item in data["recommendations"]] == sorted(
        [item["total_score"] for item in data["recommendations"]], reverse=True
    )
    assert data["recommendations"][0]["passed_conditions"]
    assert data["recommendations"][0]["score_components"]["return"]["score"] is not None
    assert "미래 수익을 보장하지 않습니다" in data["disclaimer"]


def test_price_equal_to_budget_is_eligible():
    result = recommend_etfs(request(budget_krw=10_000), [etf("A", price_krw=10_000)])
    assert result["passed_count"] == 1
    assert result["recommendations"][0]["price_krw"] == 10_000


def test_missing_price_industry_and_all_metrics_are_excluded_as_data_shortage():
    records = [
        etf("NO_PRICE", price_krw=None),
        etf("NO_INDUSTRY", industry=None),
        etf("NO_METRICS", **{"return": None, "volatility": None, "max_drawdown": None}),
    ]
    result = recommend_etfs(request(industries=["반도체"]), records)
    assert result["passed_count"] == 0
    assert result["excluded_count"] == 3
    assert result["exclusion_reason_counts"]["데이터 부족"] == 3
    assert {item["etf_code"] for item in result["exclusions"]} == {"NO_PRICE", "NO_INDUSTRY", "NO_METRICS"}
    assert {item["reason"] for item in result["exclusions"]} == {"데이터 부족"}


def test_partial_metrics_reweight_available_metrics_and_mark_missing():
    records = [
        etf("RETURN_ONLY", **{"return": 10, "volatility": None, "max_drawdown": None}),
        etf("VOL_ONLY", **{"return": None, "volatility": 20, "max_drawdown": None}),
    ]
    result = recommend_etfs(request(risk_profile="안정형"), records)
    candidate = next(item for item in result["recommendations"] if item["etf_code"] == "RETURN_ONLY")
    assert candidate["score_components"]["return"]["weight"] == 1.0
    assert candidate["score_components"]["volatility"]["score"] is None
    assert any("일부 지표 결측" in tag for tag in candidate["special_treatments"])


def test_smaller_max_drawdown_loss_magnitude_gets_safer_score():
    records = [
        etf("SMALLER_LOSS", **{"max_drawdown": -10}),
        etf("LARGER_LOSS", **{"max_drawdown": -20}),
    ]
    result = recommend_etfs(request(), records)
    assert result["recommendations"][0]["etf_code"] == "SMALLER_LOSS"
    assert result["recommendations"][0]["score_components"]["max_drawdown"]["score"] == 100


def test_total_score_ties_use_market_cap_then_code_and_explain_tie_break():
    records = [
        etf("000003", market_cap_krw=500),
        etf("000002", market_cap_krw=1_000),
        etf("000001", market_cap_krw=1_000),
    ]
    result = recommend_etfs(request(), records)
    items = result["recommendations"]
    assert [item["etf_code"] for item in items] == ["000001", "000002", "000003"]
    assert any("종목코드" in tag for tag in items[0]["special_treatments"])
    assert any("시가총액" in tag for tag in items[2]["special_treatments"])


def test_industry_unselected_multiselect_or_and_unknown_industry_rules():
    records = [
        etf("SEMICON", industry="반도체"),
        etf("BATTERY", industry="2차전지"),
        etf("OTHER", industry=None),
        etf("FOREIGN", industry="해외주식"),
    ]
    all_result = recommend_etfs(request(), records)
    assert {item["industry"] for item in all_result["recommendations"]} == {"반도체", "2차전지", "기타", "해외주식"}
    other = next(item for item in all_result["recommendations"] if item["etf_code"] == "OTHER")
    assert "산업 정보 없음 → 기타 처리" in other["special_treatments"]
    selected = recommend_etfs(request(industries=["2차전지", "반도체"]), records)
    assert {item["etf_code"] for item in selected["recommendations"]} == {"SEMICON", "BATTERY"}
    assert selected["exclusion_reason_counts"]["데이터 부족"] == 1
    assert selected["exclusion_reason_counts"]["산업 불일치"] == 1


def test_non_positive_budget_is_rejected_by_api_validation():
    for budget in (0, -1):
        response = client.post("/api/recommendations", json={"budget_krw": budget})
        assert response.status_code == 422


def test_empty_result_reports_most_filtered_condition():
    records = [etf("A", price_krw=200_000), etf("B", industry="해외주식"), etf("C", industry="해외주식")]
    result = recommend_etfs(request(industries=["반도체"]), records)
    assert result["recommendations"] == []
    assert result["message"] == "조건에 맞는 종목 없음"
    assert result["most_filtered_conditions"] == ["산업 불일치"]
    assert result["exclusion_reason_counts"] == {"산업 불일치": 2, "예산 초과": 1}


def test_result_count_must_be_between_one_and_twenty():
    for count in (0, 21):
        response = client.post("/api/recommendations", json={"budget_krw": 100_000, "result_count": count})
        assert response.status_code == 422


def test_result_count_twenty_returns_at_most_twenty_recommendations():
    records = [etf(f"{index:06d}", market_cap_krw=index) for index in range(25)]
    result = recommend_etfs(request(result_count=20), records)
    assert result["passed_count"] == 25
    assert len(result["recommendations"]) == 20


def test_home_page_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "조건 기반 ETF 추천" in response.text
    assert "추천" in response.text

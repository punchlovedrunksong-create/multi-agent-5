# 조건 기반 ETF 추천 API 명세

## 1. API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 조건 기반 ETF 추천 |
| 기능 설명 | 투자 조건을 검증하고 고정 CSV ETF 자료를 필터링·점수화·정렬해 근거와 함께 반환 |
| Method | `POST` |
| Endpoint | `/api/recommendations` |
| 성공 상태 코드 | `200 OK` |
| 실패 상태 코드 | `422 Unprocessable Entity`, `500 Internal Server Error` |

## 2. Request Body

| 필드명 | 타입 | 필수 여부 | 설명 | 기본값/예시 |
| --- | --- | --- | --- | --- |
| `budget_krw` | 양의 정수 | 필수 | 1주 가격이 예산 이하인 후보를 선택 | `100000` |
| `industries` | 문자열 배열 | 선택 | 선택한 여러 산업 중 하나라도 일치하면 통과; 빈 배열은 전체 산업 | `[]` |
| `result_count` | 정수 1~20 | 선택 | 반환할 추천 결과 수 | `5` |
| `risk_profile` | `안정형\|중립형\|공격형` | 선택 | 정량 지표 가중치 선택 | `중립형` |

```json
{
  "budget_krw": 100000,
  "industries": ["반도체", "2차전지"],
  "result_count": 5,
  "risk_profile": "중립형"
}
```

## 3. Response Body

응답에는 입력 조건, 전체/통과/제외 수, 이유별 제외 수와 ETF별 제외 내역(`exclusions`), 0개일 때 최다 제외 조건, 순위와 점수·근거, 고지 문구가 포함됩니다. ETF별 `score_components`는 각 지표의 원값(`value`), 후보군 내 점수(`score`), 해당 ETF의 결측을 반영해 다시 정규화한 비중(`weight`), 총점 기여(`contribution`)를 반환합니다.

점수는 적격 후보군 내 최선 100/최악 0의 순위 점수이며 동점은 평균 순위를 적용합니다. 수익률은 높을수록, 변동성 및 최대 낙폭의 손실 크기(|낙폭|)는 낮을수록 안전/선호 점수가 높습니다. 해당 ETF에 일부 지표가 비어 있으면 보유 지표의 비중 합을 100%로 재정규화합니다. 세 지표가 모두 없는 ETF는 `데이터 부족`으로 제외합니다. 총점 정렬 동점은 시가총액 내림차순, 종목코드 오름차순으로 해소합니다.

응답 예시(값은 fixture 결과 일부):

```json
{
  "conditions": {
    "budget_krw": 100000,
    "industries": ["반도체"],
    "result_count": 5,
    "risk_profile": "중립형"
  },
  "total_count": 9,
  "passed_count": 2,
  "excluded_count": 7,
  "exclusion_reason_counts": {"데이터 부족": 3, "산업 불일치": 3, "예산 초과": 1},
  "exclusions": [
    {"etf_code": "123456", "etf_name": "가격정보없음", "reason": "데이터 부족"}
  ],
  "most_filtered_conditions": [],
  "recommendations": [
    {
      "rank": 1,
      "etf_code": "091160",
      "etf_name": "KODEX 반도체",
      "price_krw": 40000,
      "industry": "반도체",
      "market_cap_krw": 30000000000,
      "total_score": 100.0,
      "score_components": {
        "return": {"value": 18.0, "score": 100.0, "weight": 0.5, "contribution": 50.0},
        "volatility": {"value": null, "score": null, "weight": null, "contribution": null},
        "max_drawdown": {"value": -10.0, "score": 100.0, "weight": 0.5, "contribution": 50.0}
      },
      "passed_conditions": ["가격 정보 확인", "1주 가격이 예산 이하", "선택 산업 중 하나 이상 일치"],
      "special_treatments": ["일부 지표 결측: 변동성"]
    }
  ],
  "message": "조건에 맞는 ETF 추천 결과입니다.",
  "disclaimer": "이 결과는 조건에 따른 비교 정보이며, 과거 성과가 미래 수익을 보장하지 않습니다."
}
```

## 4. 예외 응답

| 상황 | 상태 코드 | 응답 |
| --- | --- | --- |
| 예산 누락·0 이하·정수가 아님 | `422` | FastAPI/Pydantic `detail` 검증 오류 |
| 결과 개수 1 미만 또는 20 초과 | `422` | 필드 검증 오류 |
| 지원하지 않는 투자 성향, 추가 필드 전송 | `422` | 필드/추가 필드 검증 오류 |
| CSV 파일을 읽을 수 없거나 서버 처리 중 예기치 않은 오류 | `500` | 내부 정보를 감춘 기본 오류 응답 |

## 5. 관련 파일

| 역할 | 파일 경로 |
| --- | --- |
| 앱/정적 화면 | `backend/app/main.py`, `frontend/index.html` |
| Router | `backend/app/api/routes/comparison.py` |
| Request/Response schema | `backend/app/api/schemas/comparison.py`, `backend/app/api/schemas/result.py` |
| 설정 | `backend/app/core/config.py` |
| 추천 Service | `backend/app/services/recommendation_service.py` |
| 고정 자료 | `database/fixtures/etf_sample.csv` |
| 자동 테스트 | `backend/tests/unit/test_recommendation.py` |

## 6. Swagger 테스트

| 항목 | 내용 |
| --- | --- |
| 실행 명령 | `cd angel_ETF/backend && uvicorn app.main:app --reload` |
| Swagger URL | `http://127.0.0.1:8000/docs` |
| 테스트 입력 | 위 JSON 예시 |
| 기대 결과 | `200`, 추천 목록·점수 기여·통과 조건·요약·고지 반환 |
| 입력 오류 예시 | `{"budget_krw": 0}` |
| 입력 오류 기대 | `422` |

# angel_ETF 프로젝트 구조 설계서

작성: Builder / 2026-11-21

## 1. 기준과 범위

| 항목 | 내용 |
| --- | --- |
| 기준 문서 | 저장소의 `docs/requirements-definition.md`, `docs/function-breakdown.md`, `docs/mvp-plan.md` |
| 기존 상태 | 저장소 최상위에 기획 문서와 `scripts/test_krx_api.py`가 있고, `.env`에는 실제 KRX 인증 설정이 존재함. 비밀값은 읽거나 복사하지 않음. |
| 초기 요청 범위 | `angel_ETF/`를 애플리케이션 프로젝트 루트로 만들고 폴더와 빈 파일 생성 |
| 현재 구현 상태 | 사용자가 지정한 조건 기반 ETF 추천만 FastAPI·pytest·HTML로 구현. 나머지 KRX 연동·DB·익명 세션·운영 기능 파일은 빈 스캐폴드 상태 |
| 기술 선택 | 현재 조건 추천 기능은 Python/FastAPI/pytest와 단일 HTML을 사용. DB 제품/드라이버와 실 KRX 데이터 매핑은 미정 |
| 사전 API 확인 | `scripts/test_krx_api.py`의 KRX 연결 성공 기록은 MVP 계획서 T-KRX-01을 참조. 이번 추천 API는 고정 CSV만 읽고 KRX를 호출하거나 응답을 적재하지 않음. |

이번 구현에서 `backend`는 FastAPI 추천 API를 실행하며, `frontend/index.html`은 입력과 결과 화면을 제공한다. DB 제품을 선택하지 않아 저장소 관련 파일은 아직 구현되지 않았다.

## 2. 기능과 모듈

| F-ID / R-ID | 모듈·파일 | 책임 | 의존성 | T-ID |
| --- | --- | --- | --- | --- |
| F-01 / R-01 | `frontend/index.html`, `backend/app/api/routes/comparison.py`, `backend/app/api/schemas/comparison.py` | 투자 조건 입력 화면과 비교 요청 계약 | 화면 → 비교 API | T-01, T-07 |
| F-02 / R-02, R-07 | `backend/app/services/krx_client.py`, `backend/app/jobs/collect_krx.py`, `backend/app/repositories/collection_repository.py` | KRX 요청, 수집 상태·건수·오류 기록 | Backend 비밀 설정, KRX API | T-KRX-01, 03, 05 |
| F-03 / R-02 | `backend/app/services/market_data_service.py`, `backend/app/models/etf.py`, `backend/app/models/market_data.py`, `database/migrations/` | 원천 응답 검증·정규화·적재 경계 | KRX 응답, 저장소 | T-KRX-02, T-FIX-06 |
| F-04 / R-03 | `backend/app/services/recommendation_service.py` | 예산·선택 산업 필터, 제외 이유 집계 | CSV 자료, 비교 조건 | T-02~03, T-06, T-08 |
| F-05 / R-04~05 | `backend/app/services/metric_service.py`, `backend/app/models/metrics.py` | 확인된 원천자료로 수익률·변동성·최대 낙폭 계산 | 관측 시계열, 확정 산식 | T-FIX-06 |
| F-06 / R-04 | `backend/app/services/recommendation_service.py`, `backend/app/core/config.py` | 성향별 정량 가중치 적용, 결측 재분배, 순위·설명 근거 산출 | 후보 필터·CSV 지표 | T-04~05 |
| F-07 / R-06 | `backend/app/services/result_service.py`, `backend/app/repositories/result_repository.py`, `backend/app/api/routes/results.py` | 익명 세션에 결과 스냅샷 연결, 재조회·만료 응답 | 비교 결과, 세션 접근 정책 | T-FIX-09 |
| F-08 / R-05 | `frontend/index.html` | 추천 목록, 점수 기여, 조건 근거, 특별 처리와 고지 표시 | 추천 API 응답 | T-01, T-10~11 |
| F-09 / R-01~07 | `backend/app/api/schemas/common.py`, `backend/app/api/routes/health.py`, `frontend/src/components/` | 입력 오류·진행·부분/빈 결과·API 오류·만료 표시 | 각 모듈 상태와 오류 계약 | T-FIX-02, 08; T-KRX-03, 05 |
| F-10 / R-02, R-07 | `backend/app/api/routes/ops.py`, `backend/app/repositories/collection_repository.py` | 최소 수집 상태·마지막 성공·오류 조회 경계 | 운영자 접근 정책, 수집 이력 | T-KRX-03, 05 |
| F-11 / R-02, R-06 | `backend/app/core/config.py`, `angel_ETF/.env.example` | Backend 전용 비밀 설정 경계와 민감 정보 취급 | 로컬 `.env` 및 실행 환경 비밀 설정 | T-FIX-12, T-KRX-03 |
| F-12 / R-06, R-07 | `backend/app/jobs/expire_results.py`, `backend/app/repositories/result_repository.py` | 생성 후 7×24시간이 지난 조건·결과 정리 | 결과 저장소, 정리 실행 방식 | T-FIX-09 |

뉴스 수집, 생성형 AI/Agent, 벡터 저장소, 로그인, 계정 동기화, 주문, 실시간 알림은 MVP에서 제외했으므로 폴더와 파일을 만들지 않았다.

## 3. 폴더와 파일 구조

아래 구조 중 추천 기능 관련 파일은 구현되어 있다. KRX 수집·영속 저장·세션 이력 등 현재 기능 범위 밖의 모듈은 빈 파일로 유지한다.

```text
angel_ETF/
├── .gitignore
├── .env.example
├── README.md
├── docs/
│   ├── project-structure.md
│   ├── recommendation-api.md
│   └── test-results.md
├── backend/
│   ├── README.md
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── comparison.py
│   │   │   │   ├── results.py
│   │   │   │   ├── health.py
│   │   │   │   └── ops.py
│   │   │   └── schemas/
│   │   │       ├── comparison.py
│   │   │       ├── result.py
│   │   │       └── common.py
│   │   ├── jobs/
│   │   │   ├── collect_krx.py
│   │   │   └── expire_results.py
│   │   ├── models/
│   │   │   ├── etf.py
│   │   │   ├── market_data.py
│   │   │   ├── metrics.py
│   │   │   ├── recommendation.py
│   │   │   └── collection_run.py
│   │   ├── repositories/
│   │   │   ├── etf_repository.py
│   │   │   ├── result_repository.py
│   │   │   └── collection_repository.py
│   │   ├── services/
│   │   │   ├── krx_client.py
│   │   │   ├── market_data_service.py
│   │   │   ├── candidate_service.py
│   │   │   ├── metric_service.py
│   │   │   ├── recommendation_service.py
│   │   │   └── result_service.py
│   └── tests/
│       ├── fixtures/
│       ├── integration/
│       └── unit/
│           └── test_recommendation.py
├── database/
│   ├── fixtures/
│   │   └── etf_sample.csv
│   └── migrations/
└── frontend/
    ├── index.html
    ├── README.md
    ├── public/
    └── src/
        ├── components/
        ├── pages/
        ├── services/
        ├── styles/
        └── utils/
```

`backend/app/tests/`는 생성하지 않았다. 테스트 파일은 `backend/tests/` 한 곳에 모아 `unit`, `integration`, `fixtures`로 나눈다.

| 경로 | 역할 |
| --- | --- |
| `backend/app/api/routes/` | 비교 요청, 저장 결과 재조회, 상태 확인, 최소 운영 상태 조회의 경계 |
| `backend/app/api/schemas/` | 입력 검증 및 API 요청·응답 데이터 계약 |
| `backend/app/services/` | 이번에는 추천 흐름만 구현; KRX 연동·정규화·지표 산출·결과 보관 모듈은 빈 placeholder |
| `backend/app/repositories/` | ETF 자료, 결과 스냅샷, 수집 이력의 저장/조회 추상화 |
| `backend/app/models/` | 원천 시장자료와 산출 지표·추천·작업 이력의 논리 모델 |
| `backend/app/jobs/` | KRX 수집과 7일 만료 데이터 정리 작업 진입점 |
| `backend/tests/unit/` | 고정 자료 기반 규칙 단위 테스트 위치 |
| `backend/tests/integration/` | 저장소·API·실 KRX 연동 검증 위치 |
| `frontend/index.html` | 조건 입력, 추천 요청, 요약·추천/제외 목록과 고지 표시를 한 페이지에서 처리 |
| `frontend/src/` | 추후 프런트엔드 자산 분리를 위한 빈 스캐폴드 |
| `database/` | DB 제품 확정 후 마이그레이션과 비밀정보 없는 fixture 위치 |

## 4. 데이터와 API 계약

조건 추천 API의 HTTP 경로·메서드·JSON 형식은 `POST /api/recommendations`로 정했다. 아직 구현하지 않은 수집·저장·세션 API와 DB 물리 타입은 후속 설계 대상이다.

| 호출자 → 수신자 | 입력 필드·타입 | 출력 필드·타입 | 실패 코드·응답 | 계약 문서 |
| --- | --- | --- | --- | --- |
| 화면 → 비교 API | `budget_krw:int>0`, `industries:string[]`, `result_count:int(1..20)`, `risk_profile:안정형/중립형/공격형` | 입력 조건·전체/통과/제외 수·ETF별 제외 사유·추천 점수/근거 | 잘못된 입력 422, 예상하지 못한 처리 오류 500 | `docs/recommendation-api.md` |
| 수집 작업 → KRX 클라이언트 | 인증 설정, 기준일 등 승인된 KRX 요청 파라미터 | 원천 응답, HTTP/수집 메타데이터 | 인증/한도/네트워크/필드 변경/빈 응답을 분리하고 비밀정보는 응답·일반 로그에 미포함 | 기능 분해표 F-02; MVP T-KRX-01~03 |
| KRX 클라이언트 → 정규화/저장 | API 원천 ETF 일별 자료와 수집 시각 | ETF 코드·기준 가격·가격 기준일·출처·수집 시각·품질 상태 | 필수 필드/날짜/가격 오류, 중복 및 미지원 필드는 정상 추천 자료로 저장하지 않음 | 기능 분해표 F-03; MVP T-KRX-02 |
| 비교 서비스 내부 | 조건, 유효 ETF 자료, 기간별 지표와 품질 상태 | 적격 후보, 지표 가용성, 최대 5개 순위·이유 | 점수 필수 지표 결측 또는 관측 기간 미지원 시 확정 점수/순위 중단 또는 확인 불가로 표시 | 기능 분해표 F-04~F-06 |
| 결과 API → 저장소/화면 | 결과 ID와 익명 세션 증명 | 당시 조건·후보·점수 근거·데이터 버전·생성/만료 시각 | 다른 세션·만료·저장 실패는 상세 데이터 없이 구별 안내 | 기능 분해표 F-07~F-09; T-FIX-09 |

이미 호출해 본 KRX ETF 일별매매정보의 19개 응답 필드와 검증 이력은 `docs/mvp-plan.md` T-KRX-01에 기록되어 있다. 그 호출은 응답 필드 확인이며, 과거 수익률·변동성·최대 낙폭의 산식/관측 구간, 분류 필드 매핑, DB 스키마 확정을 의미하지 않는다. 실제 API 필드를 임의로 모델 필드에 매핑하지 않는다.

## 5. 상태와 오류 흐름

1. 입력 화면은 조건을 제출하기 전에 필수값과 허용값 검증 결과를 표시한다.
2. 비교 요청은 저장된 유효 기준일 자료만 사용한다. 수집 실패 자료는 기존 정상 자료를 덮어쓰지 않는다.
3. 비교 단계는 성공, 부분 자료/지표 확인 불가, 정상 후보 없음, API/저장 장애를 서로 다른 결과 상태로 전달한다.
4. 결과 저장 성공 시 익명 브라우저 세션과 스냅샷을 연결하고 생성 시각부터 7×24시간 내 재조회한다. 세션 토큰·쿠키 속성, 세션 만료 및 다른 세션 접근 차단 세부 계약은 구현 전 보안 설계에서 결정한다.
5. 만료 정리 작업은 보관 기간이 지난 스냅샷과 후보를 함께 삭제하고 결과를 운영 이력에 남긴다.
6. 인증키는 Backend 설정에서만 사용한다. 키, 전체 민감 조건, 스택 추적을 프런트엔드·응답·일반 로그에 기록하지 않는다.

| 상태 | 사용자/운영 처리 |
| --- | --- |
| 잘못된 입력 | 해당 입력 수정 안내; 비교와 저장 중단 |
| KRX 인증/호출/네트워크 실패 | API 장애로 표시; 마지막 성공 기준일과 가능한 재시도 안내; 키 비노출 |
| 정상 응답이나 후보 0개 | 정상 빈 결과로 표시; 조건 수정 안내 |
| 자료 노후/부분 누락/산식 불가 | 확인 불가 항목과 영향, 기준일 표시; 최신·완전 자료처럼 표시하지 않음 |
| 익명 세션 불일치/결과 만료 | 상세 내용은 반환하지 않고 접근 불가 또는 만료 안내 |
| 저장/만료 정리 오류 | 결과 보관/삭제가 완료된 것처럼 표시하지 않고 상태를 운영 기록에 남김 |

## 6. 실행과 검증

| 항목 | 현재 구조에서의 기준 |
| --- | --- |
| 필수 의존성 | `backend/requirements.txt`: FastAPI, Uvicorn, pytest, httpx. 버전 고정은 하지 않음. |
| 환경 변수 | 이번 고정 CSV 추천 기능은 환경 변수를 사용하지 않음. `.env.example`은 초기 구조의 빈 placeholder이며 실제 KRX 연결 시 안전한 예시 이름/가짜 값으로 작성 필요. |
| 비밀 파일 제외 | 현재 저장소 최상위 `.gitignore`가 `.env`를 제외함. 별도 저장소/배포로 옮길 때 `angel_ETF` 범위의 제외 규칙을 다시 확인해야 함. |
| 실행 명령 | `cd angel_ETF/backend && uvicorn app.main:app --reload`; 새 환경은 프로젝트 README의 설치 절차 참조 |
| 고정 자료 테스트 | `backend/tests/unit/test_recommendation.py`에서 이번 기능의 자동 테스트 12개 실행; 상세 결과는 `docs/test-results.md` 참조 |
| 실제 KRX 테스트 | T-KRX-01은 MVP 계획서에 사전 API 확인 통과로 기록됨. T-KRX-02~05는 미실행이며, 현재 구조는 재호출·정규화·적재·화면 통합을 수행하지 않음. |
| 애플리케이션 검증 | pytest 12개 통과, Uvicorn 로컬 GET/POST 각각 200. 실제 KRX는 호출하지 않음. |

## 확인 필요 사항과 단계 판정

| 미정 사항 | 담당·확인 방법·시점 | 영향·진행 가능 범위 |
| --- | --- | --- |
| DB 제품, 마이그레이션 도구, 물리 스키마 | 프로젝트 담당; 저장소 구현 전 선택 | 논리 모델 경계만 제시; DB 파일/스키마는 미작성 |
| API 응답 필드와 과거 시계열·수익률/변동성/최대 낙폭 계산 가능성 | 데이터 담당; KRX 필드 기능 확인에서 응답 샘플·자료 범위 대조 | 현재 KRX 호출 필드를 임의 매핑하지 않으며 산출 지표/추천 점수 구현 보류 |
| KRX 자료 이용 범위·호출 한도·수집 주기·보관 권한 | 프로젝트/데이터 담당; 구현·시연 전 KRX 조건 확인 | 연결 코드와 데이터 적재 정책 확정 전 필수 |
| 익명 세션 쿠키/토큰 보호·세션 수명·삭제 정책 | Backend/보안 담당; 결과 저장 구현 전 보안 설계 | 저장 결과 접근 통제에 영향 |
| 데이터 신선도 기준·운영자 권한·오류 응답 규격 | 프로젝트 담당; 수집/운영 기능 구현 전 결정 | 상태 표시와 운영 API에 영향 |

- 판정: **보완 필요**
- 근거: 조건 추천 입력·필터·점수·정렬·근거·단일 HTML 시연을 고정 CSV 기준으로 구현하고 테스트했다. KRX 데이터 사용, DB 영속화, 익명 세션 재조회와 7일 만료 등 MVP 전체 완료 항목은 아직 구현되지 않았다.
- 실행 검증: 이번 기능의 pytest 12개 통과, 로컬 Uvicorn GET/POST 확인. 실제 KRX 연동 테스트는 이번 범위에서 미실행.
- 다음 권장 작업: 실제 KRX 필드와 정량 지표를 매핑한 뒤 승인된 데이터 연동을 진행하고, 이후 DB·익명 세션 저장을 구현한다.

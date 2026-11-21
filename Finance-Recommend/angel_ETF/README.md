# angel ETF

조건을 입력하면 연습용 ETF CSV 자료를 필터링하고 성향별 정량 점수와 추천 근거를 보여주는 MVP입니다. 실제 KRX API 연결, 로그인/결과 저장, 뉴스와 AI Agent는 포함하지 않습니다.

## 실행

```bash
cd angel_ETF/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

브라우저에서 `http://127.0.0.1:8000/`을 열어 예산을 입력하고 **추천**을 누릅니다. API 요청/응답은 `http://127.0.0.1:8000/docs`의 `POST /api/recommendations`에서 확인할 수 있습니다.

## Vercel 배포

GitHub의 `punchlovedrunksong-create/multi-agent-5` 저장소를 Vercel에 가져온 뒤 프로젝트 Root Directory를 `Finance-Recommend/angel_ETF`로 지정합니다. FastAPI를 자동 감지하도록 Framework Preset은 FastAPI로 두고 배포합니다. 현재 MVP는 고정 CSV를 사용하므로 KRX API 키 환경 변수는 필요하지 않습니다.

## 입력 기본값과 제한

- 예산: 0원보다 큰 금액, 10원 단위(10원 미만 내림), 필수; 천 단위 쉼표 표시
- 산업: 1개 이상 필수, 여러 개 선택 가능
- 결과 개수: 기본 5개, 1~20개
- 투자 성향: 안정형/중립형/공격형, 기본 중립형

## 테스트

```bash
cd angel_ETF/backend
python -m pytest -q tests/unit/test_recommendation.py
```

테스트 자료는 `database/fixtures/etf_sample.csv`입니다. 실제 ETF 종목/수치 또는 투자 적합성 판단으로 사용하지 마세요.

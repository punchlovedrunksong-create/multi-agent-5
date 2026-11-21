from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ETF_CSV_PATH = PROJECT_ROOT / "database" / "fixtures" / "etf_sample.csv"

DEFAULT_RESULT_COUNT = 5
MAX_RESULT_COUNT = 20
RISK_PROFILE_WEIGHTS: dict[str, dict[str, float]] = {
    "안정형": {"return": 0.20, "volatility": 0.35, "max_drawdown": 0.45},
    "중립형": {"return": 0.35, "volatility": 0.30, "max_drawdown": 0.35},
    "공격형": {"return": 0.55, "volatility": 0.20, "max_drawdown": 0.25},
}
METRIC_LABELS = {
    "return": "수익률",
    "volatility": "변동성",
    "max_drawdown": "최대 낙폭",
}
DISCLAIMER = "이 결과는 조건에 따른 비교 정보이며, 과거 성과가 미래 수익을 보장하지 않습니다."

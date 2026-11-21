import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("KRX_API_KEY")
url = os.getenv("KRX_API_URL")

if not api_key or not url:
    raise ValueError(".env의 KRX_API_KEY와 KRX_API_URL을 확인하세요.")

response = requests.get(
    url,
    params={"basDd": "20260803"},
    headers={"AUTH_KEY": api_key, "Accept": "application/json"},
    timeout=30,
)

print("상태 코드:", response.status_code)
response.raise_for_status()

data = response.json()
rows = data.get("OutBlock_1", [])
print("ETF 자료 건수:", len(rows))
if rows:
    print("응답 필드:", ", ".join(rows[0].keys()))
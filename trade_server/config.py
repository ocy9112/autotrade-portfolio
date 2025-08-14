#!/usr/bin/env python3
# ----------------------------------------
# config.py
# 실전 운영 환경 설정 및 공용 함수 모듈
# • Alpaca API만 사용(데이터/주문)
# • 프리+정규+애프터 minute bar 사용, 컬럼 대문자 표준화(OHLCV)
# • 전략 플래그(감성 필터/동적 임계값/확장장 허용/손절 옵션)
# ----------------------------------------

import os
import sys
import requests
from datetime import datetime, timedelta, timezone
import alpaca_trade_api as tradeapi
import pandas as pd

# ─── 실행 모드(paper/prod) 및 데이터피드(sip/iex) ──────────────────────
_arg = sys.argv[1].lower() if len(sys.argv) > 1 and sys.argv[1].lower() in ("prod","paper") else None
TRADE_MODE = _arg or os.getenv("TRADE_MODE", "paper").lower()

if TRADE_MODE == "prod":
    API_URL    = os.getenv("APCA_LIVE_API_BASE_URL", "https://api.alpaca.markets")
    API_KEY    = os.getenv("APCA_LIVE_API_KEY_ID", "")
    API_SECRET = os.getenv("APCA_LIVE_API_SECRET_KEY", "")
    DATA_FEED  = "sip"
else:
    API_URL    = os.getenv("APCA_PAPER_API_BASE_URL", "https://paper-api.alpaca.markets")
    API_KEY    = os.getenv("APCA_PAPER_API_KEY_ID", "")
    API_SECRET = os.getenv("APCA_PAPER_API_SECRET_KEY", "")
    DATA_FEED  = "iex"

# ─── 경로/공유데이터/로그 ───────────────────────────────────────────────
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

BASE_DIR         = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SHARED_DATA_DIR  = os.path.join(BASE_DIR, "shared_data")
LOG_DIR          = os.path.join(BASE_DIR, "logs")
POSITIONS_FILE      = os.path.join(SHARED_DATA_DIR, "positions.csv")
POSITIONS_TEST_FILE = os.path.join(SHARED_DATA_DIR, "positions_test.csv")
TRADES_LOG_FILE     = os.path.join(SHARED_DATA_DIR, "trades.csv")
SLACK_WEBHOOK_URL   = os.getenv("SLACK_WEBHOOK_URL", "")

# ─── 전략 플래그/임계값(환경변수로 제어 가능) ──────────────────────────
USE_SENTIMENT_FILTER   = bool(int(os.getenv("USE_SENTIMENT_FILTER", "0")))  # 부정 감성 차단
USE_DYNAMIC_THRESHOLDS = bool(int(os.getenv("USE_DYNAMIC_THRESHOLDS", "0")))# 변동성 기반 임계값
ALLOW_EXTENDED_HOURS   = bool(int(os.getenv("ALLOW_EXTENDED_HOURS", "1")))  # 프리/애프터 허용
PROFIT_TAKE_RATE       = float(os.getenv("PROFIT_TAKE_RATE", "0.05"))       # +5% 분할익절
TRAILING_STOP_RATE     = float(os.getenv("TRAILING_STOP_RATE", "0.03"))     # -3% 트레일링
STOP_LOSS_ENABLED      = bool(int(os.getenv("STOP_LOSS_ENABLED", "1")))     # 손절 사용
STOP_LOSS_RATE         = float(os.getenv("STOP_LOSS_RATE", "0.03"))         # -3% 손절

# ─── Alpaca REST 클라이언트 ────────────────────────────────────────────
alpaca = tradeapi.REST(API_KEY, API_SECRET, API_URL, api_version="v2")

# ─── 거래 가능 종목 리스트(예: NYSE/NASDAQ, marginable) ────────────────
def get_tradable_symbols() -> list[str]:
    assets = alpaca.list_assets(status="active")
    return [a.symbol for a in assets if a.exchange in ("NYSE", "NASDAQ") and a.marginable]

# ─── 가격 데이터 조회(분봉, OHLCV 대문자, PrevClose 포함) ────────────────
def get_price_data(symbol: str, days: int = 3):
    """
    분봉(1Min) 데이터 조회(프리+정규+애프터). 없으면 10일로 fallback.
    반환: DataFrame columns = ['timestamp','Open','High','Low','Close','Volume','PrevClose']
    """
    try:
        api = tradeapi.REST(API_KEY, API_SECRET, API_URL, api_version="v2")
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        bars = api.get_bars(symbol, "1Min", start=start.isoformat(), end=end.isoformat(), feed=DATA_FEED).df
        if bars is None or bars.empty:
            start = end - timedelta(days=10)
            bars = api.get_bars(symbol, "1Min", start=start.isoformat(), end=end.isoformat(), feed=DATA_FEED).df
        if bars is None or bars.empty:
            return None
        # 인덱스→컬럼, 컬럼명 표준화(대문자)
        df = bars.reset_index().rename(
            columns={"timestamp":"timestamp","open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"}
        )
        # 거래량 0 제거
        df = df[df["Volume"] > 0].copy()
        if df.empty:
            return None
        # PrevClose: 전일 종가(없으면 직전 바 종가로 대체)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df.sort_values("timestamp", inplace=True)
        df["Date"] = df["timestamp"].dt.date
        daily_last = df.groupby("Date")["Close"].last()
        prev_daily = daily_last.shift(1)
        df["PrevClose"] = df["Date"].map(prev_daily.to_dict())
        df["PrevClose"] = df["PrevClose"].fillna(df["Close"].shift(1))
        df.drop(columns=["Date"], inplace=True)
        return df.reset_index(drop=True)
    except Exception as e:
        print(f"[WARN] get_price_data({symbol}) 실패: {e}")
        return None

# ─── 슬랙 알림 ──────────────────────────────────────────────────────────
def send_slack_alert(message: str):
    if not SLACK_WEBHOOK_URL:
        return
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=3)
    except Exception:
        pass

# ─── 뉴스 API 헤더(Investing via RapidAPI) ─────────────────────────────
NEWSAPI_KEY   = os.getenv("NEWSAPI_KEY", "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "investing-com6.p.rapidapi.com")
RAPIDAPI_KEY  = os.getenv("RAPIDAPI_KEY", "")

def get_news_api_headers() -> dict:
    return {"x-rapidapi-host": RAPIDAPI_HOST, "x-rapidapi-key": RAPIDAPI_KEY}


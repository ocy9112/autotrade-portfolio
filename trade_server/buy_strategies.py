#!/usr/bin/env python3
# ----------------------------------------
# buy_strategies.py
# 지침 고정 조건:
#  1) MA5 > MA20
#  2) RSI(14) < 65
#  3) 현재 거래량 > 10일 평균 거래량 * 1.5
#  4) 현재 가격 > 볼린저밴드 상단(BB_high)
#  5) 현재 거래량 > 5일 평균 거래량 * 2
# (옵션) 감성 필터/동적 임계값은 config 플래그로 제어
# ----------------------------------------

import pandas as pd
from trade_server.config import (
    USE_SENTIMENT_FILTER, USE_DYNAMIC_THRESHOLDS
)
from trade_server.ai_sentiment_client import get_ai_sentiment
from trade_server.market_filter import market_allows_entry

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def bollinger(series: pd.Series, window: int = 20, num_sd: float = 2.0):
    ma = series.rolling(window).mean()
    sd = series.rolling(window).std()
    upper = ma + num_sd * sd
    return ma, upper

def _has_enough_data(df: pd.DataFrame) -> bool:
    need = 20  # BB/MA20 계산 최소치
    return len(df) >= need

def buy_signal(symbol: str, df: pd.DataFrame) -> bool:
    try:
        if not market_allows_entry():
            return False
        if not _has_enough_data(df):
            return False

        # (옵션) 감성 필터: 부정이면 차단
        if USE_SENTIMENT_FILTER:
            ai_sig, _ = get_ai_sentiment(symbol)
            if ai_sig == "negative":
                return False

        close = df["Close"]
        vol = df["Volume"]

        ma5 = close.rolling(5).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        rsi = compute_rsi(close, 14).iloc[-1]
        vol5 = vol.rolling(5).mean().iloc[-1]
        vol10 = vol.rolling(10).mean().iloc[-1]
        curr_vol = vol.iloc[-1]
        curr_price = close.iloc[-1]
        _, bb_high = bollinger(close, 20, 2.0)
        bb_high_last = bb_high.iloc[-1]

        # 지침 고정 임계값
        rsi_limit = 65.0
        mul10 = 1.5
        mul5 = 2.0

        # (옵션) 변동성 기반 동적 임계값 - 기본 OFF
        if USE_DYNAMIC_THRESHOLDS:
            tr = (df["High"] - df["Low"]).rolling(14).mean().iloc[-1]
            atr_pct = tr / max(curr_price, 1e-9)
            rsi_limit = max(40.0, 65.0 - atr_pct * 100.0)
            mul10 += atr_pct
            mul5 += atr_pct

        cond = (
            ma5 > ma20 and
            rsi < rsi_limit and
            curr_vol > vol10 * mul10 and
            curr_price > bb_high_last and
            curr_vol > vol5 * mul5
        )
        return bool(cond)
    except Exception as e:
        print(f"[buy_signal 오류] {symbol}: {e}")
        return False


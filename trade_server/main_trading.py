#!/usr/bin/env python3
# ----------------------------------------
# main_trading.py
# • Top100 스크리닝(거래대금)
# • 매수: 지침 고정 조건 일괄 적용
# • 매도: +5% 분할익절, -3% 트레일링, (옵션) -3% 손절
# ----------------------------------------

import os
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from alpaca_trade_api.rest import REST, TimeFrame
from pandas import MultiIndex
import pandas as pd

from trade_server.config import (
    API_KEY, API_SECRET, API_URL, DATA_FEED,
    get_tradable_symbols, get_price_data, send_slack_alert,
    PROFIT_TAKE_RATE, TRAILING_STOP_RATE, STOP_LOSS_ENABLED, STOP_LOSS_RATE,
    USE_SENTIMENT_FILTER
)
from trade_server.buy_strategies import buy_signal
from trade_server.sell_strategies import (
    check_profit_take, check_trailing_stop, check_stop_loss
)
from trade_server.position_manager import (
    load_positions, add_position, update_position, close_position, update_pnl
)
from trade_server.ai_sentiment_client import get_ai_sentiment
from trade_server.trade_logger import log_trade

# ────────────────────────────────────────────────────────────────────────
def fetch_top100() -> list[str]:
    mode = os.getenv("TRADE_MODE", "prod").lower()
    feed = "sip" if mode == "prod" else "iex"
    api = REST(API_KEY, API_SECRET, API_URL, api_version="v2")
    symbols = get_tradable_symbols()
    dollar_vol: dict[str, float] = {}
    chunks = [symbols[i:i+200] for i in range(0, len(symbols), 200)]
    total = len(chunks)
    print(f">>> MODE={mode} FEED={feed} symbols={len(symbols)} chunks={total}")

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(_fetch_chunk, api, c, feed): idx+1 for idx, c in enumerate(chunks)}
        for f in as_completed(futures):
            idx = futures[f]
            dollar_vol.update(f.result())
            print(f"    [{idx}/{total}] chunks done")

    top100 = sorted(dollar_vol, key=lambda s: dollar_vol[s], reverse=True)[:100]
    print(f">>> Top100 selected = {len(top100)}")
    return top100

def _fetch_chunk(api: REST, chunk: list[str], feed: str) -> dict[str, float]:
    vol_map: dict[str, float] = {}
    now = datetime.utcnow().replace(microsecond=0)
    start = (now - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end   = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        bars = api.get_bars(chunk, TimeFrame.Minute, start=start, end=end, feed=feed).df
    except Exception as e:
        print(f"    [WARN] get_bars 실패(feed={feed}): {e}")
        return vol_map
    if bars is None or bars.empty:
        return vol_map

    is_multi = isinstance(bars.columns, MultiIndex)
    for sym in chunk:
        try:
            sub = bars.xs(sym, level=0, axis=1) if is_multi else bars
            if sub.empty:
                continue
            last = sub.iloc[-1]
            vol = float(getattr(last, "volume", getattr(last, "Volume", 0)))
            px  = float(getattr(last, "close",  getattr(last, "Close",  0)))
            if vol > 0 and px > 0:
                vol_map[sym] = vol * px
        except Exception:
            continue
    return vol_map

# ────────────────────────────────────────────────────────────────────────
def _process_buy(api: REST, tkr: str, total: int, idx: int) -> str:
    df = get_price_data(tkr)
    if df is None or len(df) == 0:
        return f"[BUY] {idx}/{total} ▶ {tkr} → 데이터 없음"

    if not buy_signal(tkr, df):  # ← BUGFIX: (symbol, df)
        return f"[BUY] {idx}/{total} ▶ {tkr} → 신호없음"

    # (옵션) 부정 감성 시 진입 차단 플래그 사용 시, 2중 검증
    if USE_SENTIMENT_FILTER:
        ai_signal, _ = get_ai_sentiment(tkr)
        if ai_signal == "negative":
            return f"[BUY] {idx}/{total} ▶ {tkr} → AI 부정 감성 차단"

    ep = float(df["Close"].iloc[-1])
    try:
        api.submit_order(
            symbol=tkr, qty=2, side='buy', type='limit',
            time_in_force='gtc', limit_price=ep, extended_hours=True
        )
    except Exception as e:
        return f"[BUY] {idx}/{total} ▶ {tkr} → 주문실패: {e}"

    add_position(tkr, 2, ep)
    log_trade(tkr, "buy", 2, ep)
    send_slack_alert(f"[매수] {tkr} 2 @ {ep}")
    return f"[EXEC] BUY {idx}/{total} ▶ {tkr} @ {ep}"

def main(symbols: list[str]) -> None:
    api = REST(API_KEY, API_SECRET, API_URL, api_version="v2")
    mode = os.getenv("TRADE_MODE", "prod").upper()
    print(f"=== MODE={mode} Top100={len(symbols)} ===")

    # 1) 매수 루프
    for idx, tkr in enumerate(symbols, start=1):
        print(_process_buy(api, tkr, len(symbols), idx))

    # 2) 보유 포지션 매도/청산 루프
    df = load_positions()
    open_df = df[df["status"] == "open"] if "status" in df.columns else df
    print(f">>> Sell check for {len(open_df)} open positions")

    for i, row in open_df.iterrows():
        s = row["symbol"]
        q = float(row["qty"])
        ep = float(row.get("entry_price", 0))
        hp = float(row.get("highest_price", ep))

        px = get_price_data(s)
        if px is None or len(px) == 0:
            print(f"[SELL] {s} → 데이터 없음")
            continue
        cp = float(px["Close"].iloc[-1])

        # 미실현 손익률 기록(로그성)
        update_pnl(s, cp)

        # 2-1) 분할 익절(+5% 기본): 50% 매도
        if check_profit_take(ep, cp):
            sell_qty = max(1, int(q // 2))
            try:
                api.submit_order(symbol=s, qty=sell_qty, side='sell', type='limit',
                                 time_in_force='gtc', limit_price=cp, extended_hours=True)
            except Exception as e:
                print(f"[SELL] TAKE-PROFIT {s} 주문실패: {e}")
            close_position(s, sell_qty, cp)
            log_trade(s, "sell", sell_qty, cp)
            send_slack_alert(f"[익절] {s} 분할 {sell_qty} @ {cp}")
            print(f"[EXEC] TAKE-PROFIT {s} {sell_qty}@{cp}")
            # 분할 후 잔여 수량 갱신
            q -= sell_qty

        # 2-2) 트레일링 스탑(최고가 대비 -3%): 전량
        elif check_trailing_stop(hp, cp):
            try:
                api.submit_order(symbol=s, qty=int(q), side='sell', type='limit',
                                 time_in_force='gtc', limit_price=cp, extended_hours=True)
            except Exception as e:
                print(f"[SELL] TRAILING {s} 주문실패: {e}")
            close_position(s, q, cp)
            log_trade(s, "sell", q, cp)
            send_slack_alert(f"[트레일링스탑] {s} 전량 @ {cp}")
            print(f"[EXEC] TRAILING-STOP {s} @ {cp}")
            continue  # 전량 매도 후 다음

        # 2-3) (옵션) 손절(진입가 대비 -3%): 전량
        elif check_stop_loss(ep, cp):
            try:
                api.submit_order(symbol=s, qty=int(q), side='sell', type='limit',
                                 time_in_force='gtc', limit_price=cp, extended_hours=True)
            except Exception as e:
                print(f"[SELL] STOP-LOSS {s} 주문실패: {e}")
            close_position(s, q, cp)
            log_trade(s, "sell", q, cp)
            send_slack_alert(f"[손절] {s} 전량 @ {cp}")
            print(f"[EXEC] STOP-LOSS {s} @ {cp}")
            continue

        # 2-4) 최고가 갱신
        if cp > hp:
            update_position(s, "highest_price", cp)
            print(f"[UPDATE] highest_price {s} → {cp}")


#!/usr/bin/env python3
# ----------------------------------------
# position_manager.py
# CSV 스키마(지침): symbol, qty, entry_price, highest_price, status, pnl, timestamp
# - status: "open" / "closed"
# - pnl: 미실현 손익률(%) 저장(로그성 지표)
# ----------------------------------------
import os
import pandas as pd
from datetime import datetime, timezone
from trade_server.config import POSITIONS_FILE

REQUIRED_COLS = ["symbol","qty","entry_price","highest_price","status","pnl","timestamp"]

def _ensure_schema(df: pd.DataFrame) -> pd.DataFrame:
    for c in REQUIRED_COLS:
        if c not in df.columns:
            df[c] = 0 if c in ("qty","entry_price","highest_price","pnl") else ""
    # 기본값/타입 보정
    df["status"] = df["status"].replace("", "open")
    return df[REQUIRED_COLS]

def load_positions(positions_file: str = POSITIONS_FILE) -> pd.DataFrame:
    if not os.path.exists(positions_file):
        df = pd.DataFrame(columns=REQUIRED_COLS)
        df.to_csv(positions_file, index=False)
        return df
    df = pd.read_csv(positions_file)
    if df.empty:
        df = pd.DataFrame(columns=REQUIRED_COLS)
    return _ensure_schema(df)

def save_positions(df: pd.DataFrame, positions_file: str = POSITIONS_FILE):
    os.makedirs(os.path.dirname(positions_file), exist_ok=True)
    _ensure_schema(df).to_csv(positions_file, index=False)

def add_position(symbol: str, qty: float, entry_price: float, positions_file: str = POSITIONS_FILE):
    df = load_positions(positions_file)
    ts = datetime.now(timezone.utc).isoformat()
    if symbol in df["symbol"].values:
        i = df.index[df["symbol"] == symbol][0]
        old_qty = float(df.at[i, "qty"])
        old_ep  = float(df.at[i, "entry_price"])
        new_qty = old_qty + qty
        new_ep  = (old_ep * old_qty + entry_price * qty) / max(new_qty, 1e-9)
        df.at[i, "qty"] = new_qty
        df.at[i, "entry_price"] = new_ep
        df.at[i, "highest_price"] = max(float(df.at[i, "highest_price"]), entry_price)
        df.at[i, "status"] = "open"
        df.at[i, "timestamp"] = ts
    else:
        row = {
            "symbol": symbol, "qty": qty, "entry_price": entry_price,
            "highest_price": entry_price, "status": "open", "pnl": 0.0, "timestamp": ts
        }
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_positions(df, positions_file)

def reduce_position(symbol: str, qty: float, positions_file: str = POSITIONS_FILE):
    df = load_positions(positions_file)
    if symbol not in df["symbol"].values:
        return
    i = df.index[df["symbol"] == symbol][0]
    remaining = float(df.at[i, "qty"]) - qty
    if remaining > 1e-9:
        df.at[i, "qty"] = remaining
    else:
        df.at[i, "qty"] = 0
        df.at[i, "status"] = "closed"
    save_positions(df, positions_file)

def close_position(symbol: str, qty: float, price: float, positions_file: str = POSITIONS_FILE):
    # price는 로그용/확인용, 현재 버전에서는 EP 갱신/실현손익 누적은 trades.csv에서 관리
    reduce_position(symbol, qty, positions_file)

def update_position(symbol: str, field: str, value, positions_file: str = POSITIONS_FILE):
    df = load_positions(positions_file)
    if symbol not in df["symbol"].values:
        return
    i = df.index[df["symbol"] == symbol][0]
    df.at[i, field] = value
    save_positions(df, positions_file)

def update_pnl(symbol: str, curr_price: float, positions_file: str = POSITIONS_FILE):
    """미실현 손익률(%)로 pnl 필드 업데이트(로그성 지표)"""
    df = load_positions(positions_file)
    if symbol not in df["symbol"].values:
        return
    i = df.index[df["symbol"] == symbol][0]
    ep = float(df.at[i, "entry_price"])
    pct = (curr_price - ep) / max(ep, 1e-9) * 100.0
    df.at[i, "pnl"] = round(pct, 3)
    save_positions(df, positions_file)


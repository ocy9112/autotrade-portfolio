#!/usr/bin/env python3
# ----------------------------------------
# sell_strategies.py
# 기본값: +5% 분할익절, -3% 트레일링, (옵션) -3% 손절
# ----------------------------------------
from trade_server.config import (
    PROFIT_TAKE_RATE, TRAILING_STOP_RATE,
    STOP_LOSS_ENABLED, STOP_LOSS_RATE
)

def check_profit_take(entry_price: float, curr_price: float, rate: float = PROFIT_TAKE_RATE) -> bool:
    return (curr_price - entry_price) / max(entry_price, 1e-9) >= rate

def check_trailing_stop(highest_price: float, curr_price: float, rate: float = TRAILING_STOP_RATE) -> bool:
    return (curr_price - highest_price) / max(highest_price, 1e-9) <= -rate

def check_stop_loss(entry_price: float, curr_price: float, rate: float = STOP_LOSS_RATE) -> bool:
    if not STOP_LOSS_ENABLED:
        return False
    return (curr_price - entry_price) / max(entry_price, 1e-9) <= -rate


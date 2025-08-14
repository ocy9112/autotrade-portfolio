#!/usr/bin/env python3
# ----------------------------------------
# trade_logger.py
# 미국주식 자동매매 - 체결/거래/이벤트 로그 기록 모듈
# • trades.csv에 실시간 기록(운영 감사/실현손익 추적)
# • 실전 운영 기준 상세 주석
# ----------------------------------------

import os
import csv
from datetime import datetime
from trade_server.config import TRADES_LOG_FILE

def log_trade(symbol: str,
              side: str,
              qty: float,
              price: float,
              pnl: float = None):
    """
    [실전 전략] 체결내역 로그 기록 함수
    - trades.csv 파일에 타임스탬프, 심볼, 매수/매도, 수량, 가격, 손익 등 저장
    - 파일/디렉토리 없으면 자동 생성(운영 중단 방지)
    - 컬럼: timestamp, symbol, side, qty, price, pnl
    - pnl: 실현손익, 미입력시 빈칸
    - 실전 감사/장기 이력 추적 필수
    """
    os.makedirs(os.path.dirname(TRADES_LOG_FILE), exist_ok=True)
    need_header = not os.path.exists(TRADES_LOG_FILE)
    with open(TRADES_LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if need_header:
            writer.writerow(['timestamp','symbol','side','qty','price','pnl'])
        ts = datetime.utcnow().isoformat()
        writer.writerow([ts, symbol, side, qty, price, pnl if pnl is not None else ''])


#!/usr/bin/env python3
# ----------------------------------------
# market_filter.py
# 프리/정규/애프터 진입 허용 시간대 제어
# 휴장일/공휴일 체크는 단순화(시간대 기준)
# ----------------------------------------
from datetime import datetime, time
from zoneinfo import ZoneInfo
from trade_server.config import ALLOW_EXTENDED_HOURS

ET = ZoneInfo("America/New_York")

def market_allows_entry() -> bool:
    now = datetime.now(ET).time()
    regular = time(9, 30) <= now <= time(16, 0)
    if ALLOW_EXTENDED_HOURS:
        pre    = time(4, 0)  <= now < time(9, 30)
        after  = time(16, 0) <  now <= time(20, 0)
        return pre or regular or after
    return regular


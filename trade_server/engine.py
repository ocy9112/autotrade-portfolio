#!/usr/bin/env python3
# ----------------------------------------
# engine.py
# 실전 자동매매 시스템 공식 진입점
# • TRADE_MODE(paper/prod) 분기(환경/인자)
# • fetch_top100 + main (main_trading.py 기준)
# • yfinance, 테스트, 임시, 예시 코드 절대 없음
# • 실전 운영 문서·정책 100% 일치, 상세 주석
# ----------------------------------------

import sys                                    # 명령줄 인자 처리
import os                                     # 환경변수 설정/확인

# main_trading.py 공식 함수(Top100, 자동매매 메인)
from trade_server.main_trading import main, fetch_top100

def run(mode: str = "prod"):
    """
    [실전 운영]
    - mode: "prod"(실거래) or "paper"(모의투자, IEX)
    - TRADE_MODE 환경변수 자동설정(아래 분기에서 config.py까지 전달)
    - Top100 종목 스크리닝 후 전체 자동매매 메인로직(main) 실행
    """
    os.environ["TRADE_MODE"] = mode
    # 1) Top100 선정 (프리+정규+애프터 전체, 데이터 fallback)
    symbols = fetch_top100()
    print(f"=== {mode.upper()} MODE: fetched Top100 ===")
    # 2) 자동매매 메인로직
    main(symbols)

if __name__ == "__main__":
    """
    [실전 운영]
    - prod/paper 인자 받지 않으면 기본 prod
    - main_trading.py fetch_top100, main만 사용
    - 모든 신호/주문/포지션/알림은 실전 운영 기준으로만 동작
    """
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else None
    mode = arg if arg in ("paper", "prod") else "prod"
    run(mode)


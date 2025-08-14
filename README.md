# 미국주식 자동매매 시스템 (실전 운영 포트폴리오)

이 레포는 **실전 운영 코드에서 민감정보를 제거한 공개 버전**입니다. 실제 키/환경설정은 포함되지 않습니다.

## 1) 전략 요약
- 종목 풀: 미국 주식 **거래대금 Top100** 자동 스크리닝(프리/정규/애프터 포함)
- 매수(모두 충족)
  1) MA5 > MA20
  2) RSI(14) < 65
  3) 현재 거래량 > 10일 평균 × 1.5
  4) 현재가 > 볼린저밴드 상단(BB_high)
  5) 현재 거래량 > 5일 평균 × 2
- 청산
  - +5% 분할 익절(예: 50%)
  - 최고가 대비 -3% 트레일링 스탑
  - 진입가 대비 -3% 손절(옵션)
- 운영 원칙
  - 포지션/잔고/주문 **실시간 기록**, 모든 이벤트 **로그/알림**, 지표/전략 로직 **모듈화**, **extended hours 지원**

## 2) 폴더 구조
- trade_server/  : 신호 생성, 주문 실행(Alpaca), 포지션/손익 CSV/로그
- analysis_server: 뉴스·소셜 감성분석(보유/청산 판단 피드백)
- docs/          : 전략/아키텍처 문서

## 3) 데모 실행(키는 환경변수로 주입)
    pip install -r analysis_server/requirements.txt
    cp trade_server/config.sample.py trade_server/config.py
    export ALPACA_API_KEY="YOUR_KEY"
    export ALPACA_SECRET_KEY="YOUR_SECRET"
    export ALPACA_BASE_URL="https://paper-api.alpaca.markets"   # 실거래: https://api.alpaca.markets
    python3 trade_server/main_trading.py paper

## 4) 환경변수 예시
- ALPACA_API_KEY, ALPACA_SECRET_KEY (필수)
- ALPACA_BASE_URL (선택: paper/live)
- SLACK_WEBHOOK, TELEGRAM_BOT, TELEGRAM_CHAT_ID (선택)

## 5) 문서
- 전략: docs/strategy.md
- 아키텍처: docs/architecture.md

## 6) 면책
본 프로젝트는 투자 자문이 아니며 모든 매매 책임은 사용자에게 있습니다.

## 7) 라이선스
MIT

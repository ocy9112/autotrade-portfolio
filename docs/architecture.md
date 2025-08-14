# 시스템 아키텍처

- trade_server: 신호 생성 → 주문(Alpaca) → 포지션/손익 CSV/로그
- analysis_server: 뉴스·소셜 수집/감성분석 → 청산/보유 판단 피드백
- shared_data: 서버 간 CSV 교환(공개 레포에는 제외)

(간단 흐름)
Market Data → trade_server(signals) → Alpaca Order → positions/logs
News/SNS → analysis_server(sentiment) → feedback → trade_server

#!/usr/bin/env python3
# ----------------------------------------
# ai_sentiment_client.py
# 미국주식 자동매매 - 외부 AI 감성분석 REST API 연동 클라이언트
# • 감성분석 서버(Flask/FastAPI) 호출
# • 네트워크/서버/데이터 예외 완전 처리
# • 실전 운영 상세 주석
# ----------------------------------------

import requests

def get_ai_sentiment(symbol):
    """
    [실전 전략] 감성분석 서버(REST API) 호출, 종목별 신호/점수 반환
    - symbol: 감성분석 대상(티커)
    [반환] (신호:str, 점수:float) → 예: ("positive"/"neutral"/"negative", -1.0~+1.0)
    [정책]
      - REST 응답 포맷: {"signal": "positive", "score": 0.47}
      - 서버/네트워크/응답 예외시 ("neutral", 0) 반환
      - 운영환경에서 서버주소/포트(localhost:5001 등) 반드시 확인/관리
    """
    try:
        # 운영 감성분석 서버 주소/포트에 맞게 수정
        r = requests.get(f"http://localhost:5001/sentiment/{symbol}", timeout=2)
        if r.status_code == 200:
            j = r.json()
            return j.get("signal", "neutral"), float(j.get("score", 0))
    except Exception as e:
        print(f"[AI SENTIMENT] {symbol} 분석 오류: {e}")
    return "neutral", 0

if __name__ == "__main__":
    # 단독 실행 테스트: 임의 티커 감성분석 결과 출력
    sig, score = get_ai_sentiment("AAPL")
    print(f"AAPL 감성: {sig}, 점수: {score}")


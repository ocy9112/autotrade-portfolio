#!/usr/bin/env python3
# ----------------------------------------
# news_client.py
# 미국주식 자동매매 - Investing.com(RapidAPI) 뉴스 API 전용
# • NewsAPI 등 모든 무료/타 API 코드 완전 제거
# • 네트워크/키/응답/서버 예외 완전 처리, 실전 운영 상세 주석
# ----------------------------------------

import requests
from trade_server.config import get_news_api_headers

def fetch_latest_news(symbol: str, page_size: int = 5):
    """
    [실전 전략] Investing.com(RapidAPI) 유료 API로 종목별 최신 뉴스 헤드라인 반환
    - symbol: 티커 또는 페어ID(운영환경/실제 API 정책에 따라 입력)
    - page_size: 가져올 뉴스 개수(기본 5)
    [반환] 기사 헤드라인(str) 리스트. 실패/오류시 빈 리스트
    [주요 정책]
      - RapidAPI Key, 네트워크, 응답 문제 발생 시 항상 빈 리스트 반환(운영 중단 방지)
      - symbol→페어ID 변환이 필요하면, 별도 매핑 딕셔너리/함수 추가 권장
    """
    headers = get_news_api_headers()
    if not headers.get("x-rapidapi-key"):
        print("[news_client] RapidAPI Key 미설정. 뉴스 조회 불가.")
        return []
    try:
        url = f"https://{headers['x-rapidapi-host']}/web-crawling/api/news/latest"
        params = {
            "pair_ID":   symbol,      # 실제 환경에 따라 티커/ID 입력
            "page_size": page_size,
        }
        resp = requests.get(url, headers=headers, params=params, timeout=3)
        resp.raise_for_status()
        data = resp.json()
        # Investing.com API 응답: result[{title, ...}]
        return [item.get("title", "") for item in data.get("result", [])]
    except Exception as e:
        print(f"[news_client] Investing.com API 예외: {e}")
        return []

if __name__ == "__main__":
    # 단독 실행 테스트: AAPL 뉴스 3개 출력
    for line in fetch_latest_news("AAPL", page_size=3):
        print(line)


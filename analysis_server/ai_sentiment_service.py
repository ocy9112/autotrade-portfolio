#!/usr/bin/env python3
# /srv/autotrade-app/analysis_server/ai_sentiment_service.py

from flask import Flask, jsonify, request
from transformers import pipeline
import requests
import os

app = Flask(__name__)

# 1) HuggingFace transformers 감성분석 파이프라인 로드
#    (로컬에 모델이 없으면 최초에 다운로드되며, 이후 캐시)
sentiment_analyzer = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

# 2) 뉴스/공시 등 텍스트 수집 함수 (예: Finnhub, NewsAPI 등)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
def fetch_news(symbol, count=5):
    # 예시: NewsAPI 를 사용
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={symbol}&"
        f"language=en&"
        f"sortBy=publishedAt&"
        f"pageSize={count}&"
        f"apiKey={NEWS_API_KEY}"
    )
    resp = requests.get(url, timeout=3)
    if resp.status_code != 200:
        return []
    articles = resp.json().get("articles", [])
    return [a.get("title","") + ". " + a.get("description","") for a in articles]

@app.route("/sentiment/<symbol>", methods=["GET"])
def sentiment(symbol):
    """
    1) symbol 에 대한 최신 뉴스 5건을 가져와
    2) 각 문장별 감성 점수를 계산한 뒤
    3) 전체 평균 점수로 signal과 score 반환
    """
    texts = fetch_news(symbol, count=5)
    if not texts:
        return jsonify(signal="neutral", score=0.0)

    results = sentiment_analyzer(texts)
    # 모델의 label 예: "1 star" ~ "5 stars" (nlptown 모델 기준)
    # 이를 -1.0 ~ +1.0 스케일로 변환
    def to_score(r):
        stars = int(r["label"].split()[0])
        return (stars - 3) / 2  # 1→-1.0, 3→0.0, 5→+1.0

    scores = [to_score(r) for r in results]
    avg = sum(scores) / len(scores)

    if avg >= 0.3:
        sig = "positive"
    elif avg <= -0.3:
        sig = "negative"
    else:
        sig = "neutral"

    return jsonify(signal=sig, score=round(avg,3))

if __name__ == "__main__":
    # 5001 포트에서 실행
    app.run(host="0.0.0.0", port=5001)


#!/usr/bin/env python3
from flask import Flask, jsonify
import os, requests
from textblob import TextBlob

app = Flask(__name__)

# (환경변수로 NEWS_API_KEY 설정 권장)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

def fetch_news(symbol):
    """NewsAPI.org 에서 최근 뉴스 타이틀+설명 가져오기"""
    if not NEWS_API_KEY:
        return []
    url = (
        "https://newsapi.org/v2/everything"
        f"?q={symbol}&language=en&pageSize=5&apiKey={NEWS_API_KEY}"
    )
    try:
        r = requests.get(url, timeout=3)
        r.raise_for_status()
        data = r.json().get("articles", [])
        return [a.get("title", "") + ". " + (a.get("description") or "") for a in data]
    except:
        return []

def analyze_sentiment(texts):
    """TextBlob 으로 평균 polarity 계산 → signal, score 반환"""
    if not texts:
        return "neutral", 0.0
    scores = [TextBlob(t).sentiment.polarity for t in texts]
    avg = sum(scores) / len(scores)
    if avg >  0.05: return "positive", round(avg, 3)
    if avg < -0.05: return "negative", round(abs(avg), 3)
    return "neutral", round(avg, 3)

@app.route("/sentiment/<symbol>")
def sentiment(symbol):
    news = fetch_news(symbol)
    sig, score = analyze_sentiment(news)
    return jsonify({"signal": sig, "score": score})

if __name__ == "__main__":
    # 0.0.0.0:5001 으로 바인딩
    app.run(host="0.0.0.0", port=5001)


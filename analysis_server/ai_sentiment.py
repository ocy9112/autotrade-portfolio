from fastapi import FastAPI, HTTPException
from transformers import pipeline
from pydantic import BaseModel

app = FastAPI(
    title="AI Sentiment Analysis Server",
    description="뉴스·소셜 감성분석 REST API",
    version="1.0"
)

# 1) HuggingFace 사전학습 모델 로드
sentiment_analyzer = pipeline("sentiment-analysis")

class SentimentResponse(BaseModel):
    signal: str    # positive / negative / neutral
    score: float

@app.get("/sentiment/{symbol}", response_model=SentimentResponse)
def get_sentiment(symbol: str):
    try:
        # (실전: symbol 관련 뉴스 크롤링→텍스트 집계 후 분석)
        # 지금은 예시 텍스트로 대체
        result = sentiment_analyzer("The stock market for " + symbol + " is looking bullish today!")
        label = result[0]["label"].lower()
        score = float(result[0]["score"])
        return {"signal": label, "score": score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {e}")


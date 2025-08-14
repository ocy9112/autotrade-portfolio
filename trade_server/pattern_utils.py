# ----------------------------------------
# pattern_utils.py
# 미국주식 자동매매 - 주요 가격/거래량 패턴 탐지 모듈
# • gap up, 돌파, 눌림목, 거래량폭증 등 실전 적용 공식 신호 패턴
# • 실전 운영 기준 상세 주석
# ----------------------------------------

import pandas as pd

def detect_gap_up(df, threshold=0.02):
    """
    [실전 전략] 갭상승 패턴 탐지
    - 시가(Open)가 전일 종가(PrevClose) 대비 threshold 이상 상승
    - threshold: 기본 2%
    [반환] True/False 시계열(행별)
    """
    if 'Open' not in df.columns or 'PrevClose' not in df.columns:
        # 필수 컬럼 없으면 전체 False 반환(실전 안전운용)
        return pd.Series(False, index=df.index)
    open_ = df['Open']
    prev_close = df['PrevClose']
    # 인덱스/길이 불일치시 보정
    if len(open_) != len(prev_close):
        prev_close = prev_close.reindex(open_.index, fill_value=0)
    cond = (open_ > prev_close * (1 + threshold))
    return cond.fillna(False)

def detect_high_break(df, window=3):
    """
    [실전 전략] 장중 고가 돌파 패턴
    - window 기간내 고점 최대값(이전봉) 돌파시 True
    """
    if 'High' not in df.columns:
        return pd.Series(False, index=df.index)
    high = df['High']
    max_high = high.rolling(window).max().shift(1)
    if len(high) != len(max_high):
        max_high = max_high.reindex(high.index, fill_value=0)
    cond = (high > max_high)
    return cond.fillna(False)

def detect_pullback(df, drop_pct=0.03):
    """
    [실전 전략] 눌림목(고점대비 일정 % 조정)
    - 최근 10봉 최고가 대비 저점이 drop_pct~drop_pct+2% 구간 진입
    """
    if 'High' not in df.columns or 'Low' not in df.columns:
        return pd.Series(False, index=df.index)
    high = df['High']
    low = df['Low']
    rolling_high = high.rolling(10).max().shift(1)
    if len(low) != len(rolling_high):
        rolling_high = rolling_high.reindex(low.index, fill_value=0)
    pullback = (rolling_high - low) / rolling_high
    cond = (pullback >= drop_pct) & (pullback <= drop_pct + 0.02)
    return cond.fillna(False)

def detect_volume_surge(df, multiplier=3):
    """
    [실전 전략] 거래량 폭증 패턴
    - 10일 평균 대비 multiplier배 이상 거래량 발생
    - multiplier: 기본 3배
    """
    if 'Volume' not in df.columns:
        return pd.Series(False, index=df.index)
    volume = df['Volume']
    avg_vol = volume.rolling(10).mean().shift(1)
    if len(volume) != len(avg_vol):
        avg_vol = avg_vol.reindex(volume.index, fill_value=0)
    cond = (volume > avg_vol * multiplier)
    return cond.fillna(False)


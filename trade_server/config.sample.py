# 사용법:
# 1) 이 파일을 config.py로 복사 (운영 레포에는 config.py 커밋 금지)
# 2) 실제 키/토큰은 환경변수로만 주입 (예: ~/.bashrc, systemd, GitHub Actions Secrets)
import os

ALPACA = {
    "API_KEY": os.getenv("ALPACA_API_KEY", ""),
    "SECRET_KEY": os.getenv("ALPACA_SECRET_KEY", ""),
    "BASE_URL": os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
}
NOTIFY = {
    "SLACK_WEBHOOK": os.getenv("SLACK_WEBHOOK", ""),
    "TELEGRAM_BOT": os.getenv("TELEGRAM_BOT", ""),
    "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),
}

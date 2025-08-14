#!/usr/bin/env python3
# 시작 전 점검: 디렉터리/CSV 스키마/환경변수
import os, sys, logging
from pathlib import Path

APP_ROOT = Path("/srv/autotrade-app")
SHARED   = APP_ROOT / "shared_data"
LOG_DIR  = APP_ROOT / "logs"

REQUIRED_ENV = [
    "APCA_PAPER_API_KEY_ID", "APCA_PAPER_API_SECRET_KEY", "APCA_PAPER_API_BASE_URL",
    # 실거래 사용 시 LIVE 키도 환경에 세팅 필요
]

def main() -> int:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
    log = logging.getLogger("preflight")
    for d in [SHARED, LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)
        log.info(f"ok: dir {d}")

    try:
        sys.path.insert(0, str(APP_ROOT))
        from data.schema import check_all  # type: ignore
        check_all(SHARED)
    except Exception as e:
        log.error(f"CSV schema check failed: {e}")
        return 2

    miss = [k for k in REQUIRED_ENV if not os.getenv(k)]
    if miss:
        log.warning(f"missing env (paper 기준): {miss}")
    log.info("preflight OK.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())


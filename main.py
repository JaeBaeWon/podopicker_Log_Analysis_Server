import os
import json
import glob
from datetime import datetime
from dotenv import load_dotenv
from log_parser import parse_log_file
from slack_notify import build_slack_blocks, send_slack_message

# ✅ 환경변수 로드
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

LOG_DIR = "logs"
PROCESSED_FILE = "processed_files.json"
HISTORY_FILE = "history.log"

# ✅ 처리된 파일 목록 불러오기
def load_processed_files():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r") as f:
            return set(json.load(f))
    return set()

# ✅ 처리된 파일 목록 저장
def save_processed_files(processed_set):
    with open(PROCESSED_FILE, "w") as f:
        json.dump(list(processed_set), f, indent=2)

# ✅ 분석 이력 저장
def save_history(log_count, errors, bots, repeated, notified):
    history_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "analyzed_logs": log_count,
        "errors": len(errors),
        "bots": len(bots),
        "repeated": len(repeated),
        "notified": notified
    }
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(history_entry, ensure_ascii=False) + "\n")

# ✅ 메인 처리 흐름
def main():
    processed = load_processed_files()
    all_errors = []
    all_bots = []
    all_repeated = {}
    analyzed_count = 0
    new_files = set()
    threat_files = []

    log_files = sorted(glob.glob(os.path.join(LOG_DIR, "*.gz")))

    for filepath in log_files:
        filename = os.path.basename(filepath)

        if filename in processed:
            print(f"✅ 이미 분석됨: {filename}")
            continue

        print(f"📄 분석 시작: {filename}")
        result = parse_log_file(filepath)

        all_errors.extend(result["errors"])
        all_bots.extend(result["bots"])

        for ip, times in result["repeated"].items():
        all_repeated.setdefault(ip, []).extend(times)

        if result["errors"] or result["bots"] or result["repeated"]:
            threat_files.append(filename)  # ✅ 삭제 전에 감지 여부 기록

        new_files.add(filename)

        os.remove(filepath)
        print(f"🗑️ 삭제 완료: {filename}")

        analyzed_count += 1

    # ✅ 처리된 파일 목록 저장
    save_processed_files(processed.union(new_files))

    # ✅ 위험 요소 여부 판단
    error_count = len(all_errors)
    bot_count = len(all_bots)
    repeated_count = len(all_repeated)

    has_threat = error_count > 5 or bot_count > 10 or repeated_count > 10

    # ✅ Slack 메시지 생성 및 전송
    if has_threat:
        blocks = build_slack_blocks(all_errors, all_bots, all_repeated)
        send_slack_message("🚨 MCP 위험 요소 탐지", blocks=blocks)
    else:
        print("✅ 이상 없음. Slack 전송 생략")


    # ✅ 처리 이력 저장
    save_history(analyzed_count, all_errors, all_bots, all_repeated, notified=has_threat)

    if __name__ == "__main__":
         main()

mport requests
from datetime import datetime

# ✅ 환경변수에서 Slack Webhook 불러오기 (.env에서 로드됨)
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# ✅ Slack 메시지 전송 함수
def send_slack_message(title, blocks=None):
    if not SLACK_WEBHOOK_URL:
        raise ValueError("SLACK_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")

    data = {
        "text": title,
        "blocks": blocks if blocks else [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": title}
            }
        ]
    }

    response = requests.post(SLACK_WEBHOOK_URL, json=data, timeout=5)
    if response.status_code != 200:
        raise ValueError(f"Slack 전송 실패: {response.status_code}, {response.text}")
    else:
        print("✅ Slack 메시지 전송 완료")

# ✅ 간단한 전체 위협 요약
def simple_threat_summary(errors, bots, repeated):
    messages = []
    if len(bots) > 10:
        messages.append("봇 요청 다수")
    if len(errors) > 5:
        messages.append("에러 급증")
    if sum(len(v) for v in repeated.values()) > 2:
        messages.append("반복 요청 다수")
    return " / ".join(messages) if messages else "이상 없음"

# ✅ 간단한 대응 제안
def simple_recommendation(errors, bots, repeated):
    if not (errors or bots or repeated):
        return "지속 모니터링 권장"
    return "WAF 룰 점검 / 반복 요청 차단 / 의심 IP 분석 필요"

# ✅ 영역별 해석 및 조치 설명 추가
def explain_area(errors, bots, repeated):
    explanations = []
    if errors:
        explanations.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*❌ 에러 요청 설명:*\n404 또는 403 에러가 주로 발생했으며, 잘못된 URL 접근 가능성이 있습니다.\n*🔧 [>
            }
        })

    if bots:
        explanations.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🤖 봇 요청 설명:*\nUser-Agent에 'bot', 'crawl' 등의 키워드가 포함된 요청이 다수 감지되었습니다.\n*[>
            }
        })

    if repeated:
        explanations.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🔁 반복 요청 설명:*\n동일 IP에서 짧은 시간 내 같은 경로로 반복 요청이 발생했습니다.\n*🔧 조치:* Rat>
            }
        })

    return explanations

# ✅ 최종 Slack 메시지 blocks 생성 함수
def build_slack_blocks(errors, bots, repeated, threat_files):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    total_errors = len(errors)
    total_bots = len(bots)
    total_repeats = sum(len(v) for v in repeated.values())

    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📊 CloudFront 로그 분석 결과 ({now})*"
            }
        },
        { "type": "divider" },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"• ❌ *에러 요청:* {total_errors}건\n"
                    f"• 🤖 *봇 요청:* {total_bots}건\n"
                    f"• 🔁 *반복 요청:* {total_repeats}건"
                )
            }
        },
        { "type": "divider" },
        *explain_area(errors, bots, repeated),
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*🧾 이상 감지된 로그 파일 목록:*\n" +
                    "\n".join(f"• `{fname}`" for fname in (threat_files or [])[:5]) +
                    ("\n... (더 있음)" if threat_files and len(threat_files) > 5 else "")
                )
            }
        },
        { "type": "divider" },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"⚠️ *종합 요약:*\n{simple_threat_summary(errors, bots, repeated)}\n\n"
                    f"🔧 *대응 권고:*\n{simple_recommendation(errors, bots, repeated)}"
                )
            }
        },
        {
            "type": "context",
            "elements": [
                { "type": "mrkdwn", "text": "🔐 MCP 로그 자동 분석 시스템" }
            ]
        }
    ]


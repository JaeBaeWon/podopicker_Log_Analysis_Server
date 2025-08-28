import os
import google.generativeai as genai
from typing import List, Dict

# 환경 변수에서 API 키 가져오기
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError("❌ GEMINI_API_KEY 환경 변수가 설정되어 있지 않습니다.")

# Gemini API 키 설정
genai.configure(api_key=GEMINI_API_KEY)

# 모델 설정 (무료 플랜에서도 잘 작동하는 빠른 모델)
model = genai.GenerativeModel("models/gemini-1.5-flash-latest")

def summarize_log_analysis(
    errors: List[Dict],
    bots: List[Dict],
    repeated: Dict[str, List]
) -> str:
    prompt = build_prompt(errors, bots, repeated)
    try:
        response = model.generate_content(prompt)
        return response.text if hasattr(response, "text") else "⚠️ Gemini 응답에 텍스트가 없습니다."
    except Exception as e:
        return f"❌ Gemini 호출 중 오류 발생: {str(e)}"

def build_prompt(errors: List[Dict], bots: List[Dict], repeated: Dict[str, List]) -> str:
    prompt_lines = ["\n📄 다음은 CloudFront 로그 분석 결과입니다.\n"]

    if errors:
        prompt_lines.append("🚨 *에러 요청:*")
        for e in errors[:5]:
            prompt_lines.append(f"- `{e['ip']}` → `{e['uri']}` ({e['status']}) @ {e['time']}")
    else:
        prompt_lines.append("✅ 에러 없음.")

    if bots:
        prompt_lines.append("\n🤖 *봇 요청:*")
        for b in bots[:5]:
            prompt_lines.append(f"- `{b['ip']}` → `{b['uri']}` (UA: `{b['ua']}`) @ {b['time']}")
    else:
        prompt_lines.append("✅ 봇 요청 없음.")

    if repeated:
        suspicious = [ip for ip, times in repeated.items() if len(times) > 5]
        if suspicious:
            prompt_lines.append("\n🔁 *반복 요청 IP:*")
        for ip in suspicious:
                prompt_lines.append(f"- `{ip}` → {len(repeated[ip])}회")
        else:
            prompt_lines.append("✅ 반복 요청 없음.")
    else:
        prompt_lines.append("✅ 반복 요청 없음.")

    prompt_lines.append("\n📌 위 내용을 기반으로 잠재적 보안 위협 및 대응 방안을 요약해줘.")

    prompt = "\n".join(prompt_lines)

    # ✅ Gemini에 전달될 프롬프트 출력
    print("\n📤 Gemini에 보낼 Prompt ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓")
    print(prompt)
    print("↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑\n")

    return prompt

import os
import requests

MAX_RETRIES = 1


def call_gemini(prompt: str, model: str, temperature: float, max_tokens: int) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            'GEMINI_API_KEY 환경변수가 설정되지 않았습니다.\n예) export GEMINI_API_KEY="YOUR_KEY"'
        )

    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"API 호출 실패: {e}")

    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError(f"API 응답 형식이 예상과 다릅니다: {data}")


def generate_with_retry(prompt: str, validate_fn, args) -> str | None:
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"[INFO] AI API 요청 중... (시도 {attempt}/{MAX_RETRIES})")
        try:
            response = call_gemini(prompt, args.model, args.temperature, args.max_tokens)
        except RuntimeError as e:
            print(f"[ERROR] {e}")
            return None

        if validate_fn(response):
            return response
        print("[WARN] 형식 검증 실패, 재시도합니다.")
        print("[DEBUG] 실패한 응답 원문 ---")
        print(response)
        print("---")

    print(f"[ERROR] {MAX_RETRIES}번 시도했지만 형식 검증에 실패했습니다.")
    return None
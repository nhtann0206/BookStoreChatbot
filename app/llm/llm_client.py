import os
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = "gemini-2.5-flash-lite"
CACHE_DIR = Path("app/cache")
LOG_FILE = Path("app/logs/llm_log.txt")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

client = genai.Client(api_key=API_KEY)

def _hash_prompt(prompt: str) -> str:
    return hashlib.md5(prompt.encode("utf-8")).hexdigest()

def _cache_read(prompt: str):
    cache_file = CACHE_DIR / f"{_hash_prompt(prompt)}.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            return data.get("response")
        except Exception:
            return None
    return None

def _cache_write(prompt: str, response: str):
    cache_file = CACHE_DIR / f"{_hash_prompt(prompt)}.json"
    cache_file.write_text(
        json.dumps(
            {
                "prompt": prompt,
                "response": response,
                "timestamp": datetime.now().isoformat()
            },
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

def _log(content: str):
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}]\n{content}\n{'-' * 60}\n")

def llm_generate(prompt: str, temperature: float = 0.4, retry: int = 3, use_cache: bool = True) -> str:
    if use_cache:
        cached = _cache_read(prompt)
        if cached:
            _log(f"[CACHE HIT] {prompt[:200]}...")
            return cached

    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
    ]

    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=2048
    )

    for attempt in range(retry):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=config
            )
            text = response.candidates[0].content.parts[0].text.strip()
            if not text:
                raise ValueError("Empty response")
            _cache_write(prompt, text)
            _log(f"[SUCCESS attempt {attempt+1}] {prompt[:120]}...\n{text[:500]}")
            return text
        except Exception as e:
            _log(f"[ERROR attempt {attempt+1}] {str(e)}")
            time.sleep(1.5)

    fallback = "Xin lỗi, hiện tại hệ thống đang bận. Vui lòng thử lại sau 🕐."
    _log(f"[FALLBACK USED] {prompt[:120]}...")
    return fallback

if __name__ == "__main__":
    test_prompt = "Xin chào, bạn khỏe không?"
    print(llm_generate(test_prompt))

import os, json, logging
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO)
from google import genai
from google.genai import types
import re
from typing import Optional, Dict, Any

SYSTEM_PROMPT = """You are an intelligent assistant for a bookstore.
Your job: analyze the user's Vietnamese request and return ONLY a JSON object.
Think step by step internally, but NEVER output the chain-of-thought.

Supported actions:
1) Search:
{"action":"search","filters":{"title":"...","author":"...","category":"..."}}
2) Order:
{"action":"order","book_title":"...","author":"...","quantity":1,"customer_name":"","phone":"","address":""}
3) Chitchat:
{"action":"chitchat","raw":"..."}
4) Unknown:
{"action":"unknown","raw":"..."}

Rules:
- Always return valid JSON only (no extra text).
- If the user requests all books, return {"action":"search","filters":{}}.
- Do not invent facts.
- Only include fields the user provided in the current message. If a field is missing, omit that key.
- Never default quantity to 1 unless the user explicitly said 1.
- In follow-up messages where the user provides contact info (name/phone/address) for an ongoing order, return {"action":"order"} with only the provided fields (do not repeat or change book_title/quantity if the user didn’t restate them).
"""

def _try_parse_first_json_object(text: str) -> Optional[Dict[str, Any]]:
    s = (text or "").strip()
    if not s:
        return None
    # Fast path: use raw_decode to grab first JSON object
    try:
        obj, end = json.JSONDecoder().raw_decode(s)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    # Fallback: find first balanced {...}
    start = s.find("{")
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(s[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                segment = s[start:i+1]
                try:
                    obj = json.loads(segment)
                    return obj if isinstance(obj, dict) else None
                except Exception:
                    return None
    return None

_VN_NUMBER_WORDS = {
    "một": 1, "mot": 1, "mốt": 1,
    "hai": 2, "ba": 3,
    "bốn": 4, "bon": 4, "tư": 4,
    "năm": 5, "lam": 5, "lăm": 5,
    "sáu": 6, "bay": 7, "bảy": 7,
    "tám": 8, "chín": 9, "mười": 10
}
_QUANTITY_RE = re.compile(r'(?P<n>\d+)\s*(?:cu[oô]́n|cu[oô]n|quy[eê]̉n|quy[eê]n)?', re.IGNORECASE)

def _extract_quantity(text: str) -> Optional[int]:
    m = _QUANTITY_RE.search(text or "")
    if m:
        try:
            return int(m.group("n"))
        except Exception:
            pass
    lowered = (text or "").lower()
    for word, val in _VN_NUMBER_WORDS.items():
        if re.search(rf'\b{re.escape(word)}\b', lowered):
            return val
    return None

_STOPWORDS = [
    "tôi","toi","muốn","muon","mua","đặt","dat","đặt mua","dat mua",
    "lấy","lay","thêm","them","cuốn","cuon","quyển","quyen",
    "quyển sách","quyen sach","cuốn sách","cuon sach","sách","sach",
    "xin","vui lòng","vui long","nhé","nhe","nhá","nha","cho","mình","minh"
]

def _extract_book_title(text: str) -> Optional[str]:
    if not text:
        return None
    # Prefer quoted text as title
    quoted = re.findall(r'[\"“”\'’](.*?)[\"“”\'’]', text)
    if quoted:
        candidate = quoted[0].strip()
        return candidate if candidate else None
    # Strip quantity and common stopwords to leave likely title
    s = re.sub(_QUANTITY_RE, ' ', text)
    lowered = s.lower()
    for w in _STOPWORDS:
        lowered = re.sub(rf'\b{re.escape(w)}\b', ' ', lowered)
    lowered = re.sub(r'\s+', ' ', lowered).strip()
    return lowered or None

def _postprocess_llm_json(obj: Dict[str, Any], user_text: str) -> Dict[str, Any]:
    """
    Drop fields that were not explicitly mentioned in this turn to avoid overwriting
    previously captured info (e.g., quantity=1 default from the LLM).
    """
    if not isinstance(obj, dict):
        return obj
    action = obj.get("action")
    if action != "order":
        return obj

    # Detect if the current message explicitly includes quantity or title
    has_qty = _extract_quantity(user_text) is not None
    title_in_msg = _extract_book_title(user_text)

    # If no explicit quantity in this message, remove quantity from JSON to avoid overriding prior state
    if not has_qty and "quantity" in obj:
        try:
            del obj["quantity"]
        except Exception:
            pass

    # If no explicit title in this message, and LLM left it empty or guessed, drop it
    if not title_in_msg:
        if "book_title" in obj and (obj["book_title"] is None or str(obj["book_title"]).strip() == ""):
            try:
                del obj["book_title"]
            except Exception:
                pass

    return obj

def parse_user_input(user_text: str) -> dict:
    logging.info('NLU parse request: %s', user_text)
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        return _rule_parse(user_text)
    try:
        client = genai.Client(api_key=key)
        model = 'gemini-2.5-flash-lite'
        contents = [
            types.Content(
                role='user',
                parts=[types.Part.from_text(text=SYSTEM_PROMPT + '\nUser: ' + user_text)]
            )
        ]
        cfg = types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=0))
        text = ''
        for chunk in client.models.generate_content_stream(model=model, contents=contents, config=cfg):
            text += chunk.text or ''
        text = text.strip()
        obj = _try_parse_first_json_object(text)
        if isinstance(obj, dict):
            return _postprocess_llm_json(obj, user_text)
        raise ValueError("LLM did not return valid JSON")
    except Exception:
        logging.exception('NLU LLM failed, fallback to rule parse')
        return _rule_parse(user_text)

def _rule_parse(text: str) -> dict:
    t = (text or "").lower()

    # Extract common entities
    qty = _extract_quantity(text)
    phone = None
    m2 = re.search(r"(0\d{9})", text or "")
    if m2:
        phone = m2.group(1)

    # Heuristic: this turn is likely providing contact details
    is_contact_turn = bool(phone) or any(k in t for k in ['địa chỉ','dia chi','đặt về','dat ve','giao đến','giao den'])

    # Confirmation that often follows a suggested book; treat as order if qty present
    if any(w in t for w in ['đúng','dung','ok','okay','vâng','vang','phải','phai']):
        if qty:
            return {
                "action": "order",
                # omit book_title to keep previous suggestion
                "quantity": qty,
                "customer_name": "",
                "phone": phone or "",
                "address": ""
            }

    # Order intent if explicit verbs or a quantity is present, or contact details are provided
    if qty or is_contact_turn or any(w in t for w in ['mua','đặt','dat','đặt mua','dat mua','lấy','lay','thêm','them']):
        result = {
            "action": "order",
            "customer_name": "",
            "phone": phone or "",
            "address": ""
        }
        title = _extract_book_title(text)
        if title:
            result["book_title"] = title
        if qty is not None:
            result["quantity"] = qty
        return result

    # Search intent
    if any(w in t for w in ['tìm','tim','còn','giá','thông tin']) or re.search(r'c[oó] .+ kh[oô]ng', t):
        title = _extract_book_title(text)
        return {"action": "search", "filters": {} if not title else {"title": title}}

    # Chitchat
    if any(w in t for w in ['chào','xin chào','cảm ơn','cam on','thank','hello','hi']):
        return {"action":"chitchat","raw": t}

    return {"action":"unknown","raw": t}

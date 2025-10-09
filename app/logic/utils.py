import re
import unicodedata
from difflib import get_close_matches
from typing import List, Optional, Dict, Any

VN_NUM_WORDS = {
    "một": 1, "mot": 1,
    "hai": 2,
    "ba": 3,
    "bốn": 4, "bon": 4, "tư": 4,
    "năm": 5, "nam": 5, "lăm": 5,
    "sáu": 6,
    "bảy": 7, "bay": 7,
    "tám": 8, "tam": 8,
    "chín": 9, "chin": 9,
    "mười": 10, "muoi": 10,
    "mười một": 11, "muoi mot": 11,
    "mười hai": 12, "muoi hai": 12,
    "hai mươi": 20, "hai muoi": 20
}


def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def _strip_accents(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s


def _normalize_for_match(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = _strip_accents(s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _extract_phone(text: str) -> Optional[str]:
    if not text:
        return None
    # handle +84 and 0... with separators
    patterns = [
        r'(\+84|84|0)[\s\.\-]?\d{1,3}[\s\.\-]?\d{3}[\s\.\-]?\d{3,4}',
        r'\b0\d{9,10}\b',
        r'\b\d{3}[\s\.\-]\d{3}[\s\.\-]\d{3,4}\b'
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            val = re.sub(r"[^\d\+]", "", m.group(0))
            # normalize +84 -> 0 if needed
            if val.startswith("+84"):
                val = "0" + val[3:]
            elif val.startswith("84") and not val.startswith("840"):
                # likely missing +, convert to 0...
                val = "0" + val[2:]
            return val
    return None


def _extract_quantity(text: str) -> Optional[int]:
    if not text:
        return None
    # digits first
    m = re.search(r'(\d+)\s*(?:cuốn|cuon|quyển|quyen|quyển|quyen|q|quyen)?\b', text, flags=re.IGNORECASE)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    # words (simple)
    for word, num in VN_NUM_WORDS.items():
        if re.search(r'\b' + re.escape(word) + r'\b', text, flags=re.IGNORECASE):
            return num
    return None


def _extract_address(text: str) -> Optional[str]:
    if not text:
        return None
    # common address introducers
    addr_keywords = [
        r'giao về', r'giao cho', r'giao tới', r'địa chỉ', r'tại', r'đ/c', r'đ dia chi',
        r'số nhà', r'số', r'ngõ', r'ngách', r'đường', r'phố', r'phường', r'xã', r'quận', r'huyện', r'tp', r'tp\.' 
    ]
    for kw in addr_keywords:
        m = re.search(kw + r'\s*[:\-]?\s*(?P<addr>[^,;\n]+)', text, flags=re.IGNORECASE)
        if m and m.group('addr'):
            return clean_text(m.group('addr'))
    # fallback: look for sequences containing house number patterns
    m2 = re.search(r'\b(số\s*\d+[^,;\n]*)', text, flags=re.IGNORECASE)
    if m2:
        return clean_text(m2.group(1))
    return None


def _extract_name(text: str) -> Optional[str]:
    if not text:
        return None
    # patterns: "cho <Name>", "của <Name>", "tên <Name>", "gửi cho <Name>"
    # stop tokens: tại/địa chỉ/số/sdt/phone/giao/,\.
    patterns = [
        r'(?:cho|cho anh|cho chị|cho ông|cho bà|giao cho|gửi cho|giao về)\s+([A-ZĐ][\w\-\.]{1,80}(?:\s+[A-ZĐ][\w\-\.]{1,80})*)',
        r'(?:tên|tên là|tên:)\s*([A-ZĐ][\w\-\.]{1,80}(?:\s+[A-ZĐ][\w\-\.]{1,80})*)',
        r'(?:của)\s+([A-ZĐ][\w\-\.]{1,80}(?:\s+[A-ZĐ][\w\-\.]{1,80})*)'
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            name = m.group(1).strip().strip(',:.-')
            # avoid capturing words that look like addresses/phones
            if not re.search(r'\d', name):
                return name
    # fallback: look for "Tên: X" variants with lower-case too
    m2 = re.search(r'(?:tên[:\s]+)([^,;\n]+)', text, flags=re.IGNORECASE)
    if m2:
        cand = clean_text(m2.group(1))
        cand = re.split(r'[,\n]', cand)[0].strip()
        return cand
    return None


def _match_known_titles(text_norm: str, known_titles: List[str]) -> Optional[str]:
    if not known_titles:
        return None
    # normalize known titles
    normalized_map = { _normalize_for_match(t): t for t in known_titles if t }
    candidates = []
    for norm_title, orig in normalized_map.items():
        if norm_title in text_norm:
            candidates.append((len(norm_title), orig))
    if candidates:
        # return the longest match (prefer longer title)
        candidates.sort(reverse=True)
        return candidates[0][1]
    # fuzzy match - use difflib on words
    all_titles_norm = list(normalized_map.keys())
    best = get_close_matches(text_norm, all_titles_norm, n=1, cutoff=0.7)
    if best:
        return normalized_map[best[0]]
    # also attempt word-level matching: check if >50% words of a title present
    words = set(text_norm.split())
    for norm_title, orig in normalized_map.items():
        twords = set(norm_title.split())
        if not twords:
            continue
        overlap = len(twords & words) / len(twords)
        if overlap >= 0.6:
            return orig
    return None


def _extract_title_by_patterns(text: str, text_norm: str) -> Optional[str]:
    q = re.search(r'["“”\'«»](?P<title>.+?)["“”\'»]', text)
    if q:
        return clean_text(q.group('title'))

    stop_words = r'(?:giao|cho|tại|địa chỉ|sđt|sdt|số|nhà|ngõ|,|;|\.)'
    patterns = [
        # mua/đặt ... [qty] cuốn [title] (stop before 'giao/cho/tại')
        rf'(?:mua|muốn mua|muon mua|đặt|dat|muốn đặt|muon dat)\s*(?:khoảng\s*)?(?:\d+\s*)?(?:cuốn|cuon|quyển|quyen|tập|quyen|quyen)?\s*(?:sách)?\s*(?P<title>.+?)(?=\s+{stop_words}|$)',
        # cuốn/ quyển TITLE ...
        rf'(?:cuốn|cuon|quyển|quyen|tập)\s+(?P<title>.+?)(?=\s+{stop_words}|$)',
        # TITLE <number> cuốn (title before qty)
        r'(?P<title>[A-ZĐ][\w\W]{1,80}?)\s*,?\s*(?:\d+)\s*(?:cuốn|cuon|quyển|quyen)\b',
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            title = m.group('title').strip()
            # remove trailing keywords accidentally captured
            title = re.split(r'\b(?:giao|cho|tại|địa chỉ|sđt|sdt|số|nhà|ngõ)\b', title, flags=re.IGNORECASE)[0].strip()
            title = re.sub(r'^[\-:\s]+|[\-:\s]+$', '', title)
            if title:
                return title
    # last resort: pick capitalized run of words (2+ words)
    cap_run = re.search(r'([A-ZĐ][\w\'\-\.]{1,}\s+[A-ZĐ][\w\'\-\.]{1,}(?:\s+[A-ZĐ][\w\'\-\.]{1,})*)', text)
    if cap_run:
        return clean_text(cap_run.group(1))
    return None


def extract_order_entities(text: str, known_titles: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Robust extractor for order entities.

    Parameters:
      - text: raw user input
      - known_titles: optional list of book titles from DB (used for reliable matching)

    Returns dict with keys:
      - customer_name, book_title, quantity, address, phone
    """
    raw = clean_text(text or "")
    raw_orig = raw
    text_norm = _normalize_for_match(raw)

    phone = _extract_phone(raw)
    quantity = _extract_quantity(raw)
    address = _extract_address(raw)
    name = _extract_name(raw)

    # Try to get title via patterns
    title = _extract_title_by_patterns(raw, text_norm)

    # If pattern didn't find title, try known_titles matching on normalized text
    if (not title or title.strip() == "") and known_titles:
        matched = _match_known_titles(text_norm, known_titles)
        if matched:
            title = matched

    # If title found but looks truncated, try expanding from raw using surrounding words
    if title:
        title = title.strip().strip('.,;:-"\'')
        # sometimes title captured only one word; attempt to expand around that word by extracting up to 4 words
        if len(title.split()) == 1:
            tword = _normalize_for_match(title)
            # attempt to find a longer sequence in raw containing this word
            m = re.search(r'([A-ZĐ][\w\'\-\.]+\s+[A-ZĐ][\w\'\-\.]+\s*[A-ZĐ]?[^\n,;]*)', raw)
            if m:
                cand = clean_text(m.group(0))
                if tword in _normalize_for_match(cand):
                    title = cand

    # Final fallback: known_titles fuzzy match on whole text
    if (not title or title.strip() == "") and known_titles:
        matched = _match_known_titles(text_norm, known_titles)
        if matched:
            title = matched

    # Final cleanups: remove quantity words erroneously included
    if title:
        title = re.sub(r'\b\d+\s*(?:cuốn|cuon|quyển|quyen|tập)\b', '', title, flags=re.IGNORECASE).strip()
        title = re.sub(r'\b(số|sdt|địa chỉ|đ/c)\b.*$', '', title, flags=re.IGNORECASE).strip()
        if title == "":
            title = None

    return {
        "customer_name": name,
        "book_title": title,
        "quantity": quantity,
        "address": address,
        "phone": phone,
        "raw": raw_orig
    }

if __name__ == "__main__":
    tests = [
        "Tôi muốn mua 2 cuốn Truyện Kiều giao cho Quang tại Hà Nội, SĐT 0123456789",
        "Đặt 5 quyển Đắc Nhân Tâm, tên Huy, giao về số 1 Yên Hòa - Cầu Giấy, sđt: 0987654321",
        "Mua 1 sách 'Harry Potter và Hòn đá Phù thủy' cho Lan, địa chỉ: 23 ngõ 5 đường ABC, phone 090-123-4567",
        "Cho tôi 3 cuốn Nhà giả kim - giao đến số 7 phố XYZ. SĐT 0912345678",
        "Mình đặt 2 quyển Dế Mèn phiêu lưu ký, tên: An, 01234567890, giao về Hà Nội",
        "Tôi muốn mua 5 quyền Đắc Nhân Tâm. Tên Huy, Địa chỉ: số 1 Yên Hoà, Cầu Giấy. SĐT 0123456789",
    ]
    known = [
        "Truyện Kiều", "Đắc Nhân Tâm", "Dế Mèn Phiêu Lưu Ký",
        "Harry Potter và Hòn đá Phù thủy", "Nhà giả kim"
    ]
    for t in tests:
        print("INPUT:", t)
        print("EXTRACTED:", extract_order_entities(t, known_titles=known))
        print("-" * 80)

import json
import os
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


load_dotenv()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
PADDLE_OCR_LANG = os.getenv("PADDLE_OCR_LANG", "korean")
PADDLE_PDX_CACHE_HOME = os.getenv("PADDLE_PDX_CACHE_HOME", str(Path(".paddlex").resolve()))


class OCRUnavailableError(RuntimeError):
    pass


@dataclass
class ParsedReceiptItem:
    name: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal | None = None
    line_total: Decimal | None = None


@dataclass
class ParsedReceipt:
    store_name: str | None
    receipt_date: datetime | None
    total_amount: Decimal | None
    currency: str
    raw_text: str
    raw_ocr: Any
    items: list[ParsedReceiptItem]
    image_path: str


_ocr_instance = None


def _get_ocr():
    global _ocr_instance
    if _ocr_instance is not None:
        return _ocr_instance

    os.environ.setdefault("PADDLE_PDX_CACHE_HOME", PADDLE_PDX_CACHE_HOME)
    Path(os.environ["PADDLE_PDX_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)

    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise OCRUnavailableError(
            "PaddleOCR is not installed. Install paddlepaddle and paddleocr first."
        ) from exc

    _ocr_instance = PaddleOCR(
        lang=PADDLE_OCR_LANG,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )
    return _ocr_instance


def save_upload_file(upload_file) -> str:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    extension = Path(upload_file.filename or "").suffix.lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{extension}"
    destination = UPLOAD_DIR / filename

    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return str(destination)


def _normalize_ocr_result(result: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    if isinstance(result, list) and result and not isinstance(result[0], dict):
        for block in result:
            if not isinstance(block, list):
                continue
            for line in block:
                if not isinstance(line, list) or len(line) < 2:
                    continue
                box = line[0]
                text, score = line[1]
                normalized.append({"text": text, "score": score, "box": box})
        return normalized

    for res in result or []:
        data = None
        if hasattr(res, "json"):
            try:
                json_value = res.json
                if callable(json_value):
                    json_value = json_value()
                if isinstance(json_value, str):
                    data = json.loads(json_value)
                elif isinstance(json_value, dict):
                    data = json_value
            except Exception:
                data = None
        elif hasattr(res, "res"):
            data = res.res
        elif isinstance(res, dict):
            data = res

        if not data:
            continue

        if isinstance(data, dict) and "res" in data and isinstance(data["res"], dict):
            data = data["res"]

        rec_texts = data.get("rec_texts", [])
        rec_scores = data.get("rec_scores", [])
        rec_polys = data.get("rec_polys", data.get("dt_polys", []))
        for idx, text in enumerate(rec_texts):
            normalized.append(
                {
                    "text": text,
                    "score": rec_scores[idx] if idx < len(rec_scores) else None,
                    "box": rec_polys[idx] if idx < len(rec_polys) else None,
                }
            )

    return normalized


def run_ocr(image_path: str) -> list[dict[str, Any]]:
    ocr = _get_ocr()

    if hasattr(ocr, "predict"):
        result = ocr.predict(image_path)
    else:
        result = ocr.ocr(image_path, cls=False)

    normalized = _normalize_ocr_result(result)
    if normalized:
        return normalized

    raise OCRUnavailableError("OCR ran but returned no readable text.")


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _box_center_y(box: Any) -> float:
    if not box:
        return 0
    ys = [point[1] for point in box if isinstance(point, (list, tuple)) and len(point) >= 2]
    return sum(ys) / len(ys) if ys else 0


def _box_left_x(box: Any) -> float:
    if not box:
        return 0
    xs = [point[0] for point in box if isinstance(point, (list, tuple)) and len(point) >= 2]
    return min(xs) if xs else 0


def _parse_amount(value: str) -> Decimal | None:
    cleaned = re.sub(r"[^\d.,-]", "", value).replace(",", "")
    if not cleaned or cleaned in {"-", ".", "-."}:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _parse_datetime(text: str) -> datetime | None:
    patterns = [
        r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?",
        r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*(\d{1,2}):(\d{2})(?::(\d{2}))?",
        r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        parts = [int(part) if part is not None else 0 for part in match.groups()]
        if len(parts) >= 5:
            year, month, day, hour, minute, second = (parts + [0])[:6]
            return datetime(year, month, day, hour, minute, second)
        year, month, day = parts[:3]
        return datetime(year, month, day)
    return None


def _looks_like_amount_only(line: str) -> bool:
    return _parse_amount(line) is not None and bool(re.fullmatch(r"[\d,\.\-=\s]+", line))


def _find_total_amount(lines: list[str]) -> Decimal | None:
    total_keywords = ("합계", "총액", "결제금액", "받을금액", "총 결제금액")
    amount_pattern = re.compile(r"(-?\d[\d,]*(?:\.\d{1,2})?)")

    for idx, line in enumerate(lines):
        normalized = _clean_text(line)
        if not any(keyword in normalized for keyword in total_keywords):
            continue
        amounts = amount_pattern.findall(normalized)
        if amounts:
            amount = _parse_amount(amounts[-1])
            if amount is not None:
                return amount
        for next_line in lines[idx + 1 : idx + 3]:
            next_amounts = amount_pattern.findall(_clean_text(next_line))
            if next_amounts:
                amount = _parse_amount(next_amounts[-1])
                if amount is not None:
                    return amount

    for line in reversed(lines):
        amounts = amount_pattern.findall(line)
        if amounts:
            amount = _parse_amount(amounts[-1])
            if amount is not None and amount > 999:
                return amount
    return None


def _looks_like_header(line: str) -> bool:
    header_keywords = ("상품", "품명", "수량", "단가", "금액", "판매", "결제")
    return any(keyword in line for keyword in header_keywords)


def _extract_store_name(lines: list[str]) -> str | None:
    skip_keywords = ("중간계산서", "충간계산서", "영수증", "사업자", "TEL", "테이블", "주문자", "고객수")
    for line in lines[:8]:
        normalized = _clean_text(line).strip("[]")
        if not normalized:
            continue
        if any(keyword in normalized for keyword in skip_keywords):
            continue
        if re.search(r"\d{3,}", normalized):
            continue
        return normalized
    return lines[0] if lines else None


def _extract_items_from_menu_block(lines: list[str]) -> list[ParsedReceiptItem]:
    start_idx = None
    for idx, line in enumerate(lines):
        if "메뉴" in line:
            start_idx = idx
            break

    if start_idx is None:
        return []

    menu_lines: list[str] = []
    stop_keywords = ("합계", "합", "받을금액", "받은금액", "부가세", "공급가액", "현금", "카드", "주문자", "고객수")
    for line in lines[start_idx + 1 :]:
        normalized = _clean_text(line)
        if not normalized:
            continue
        if any(keyword in normalized for keyword in stop_keywords):
            break
        if normalized in {"단가", "수량", "금액", "계="}:
            continue
        menu_lines.append(normalized)

    items: list[ParsedReceiptItem] = []
    idx = 0
    while idx < len(menu_lines):
        name = menu_lines[idx]
        if _looks_like_amount_only(name):
            idx += 1
            continue

        if idx + 3 < len(menu_lines):
            unit_price = _parse_amount(menu_lines[idx + 1])
            quantity = _parse_amount(menu_lines[idx + 2])
            line_total = _parse_amount(menu_lines[idx + 3])
            if unit_price is not None and quantity is not None and line_total is not None:
                items.append(
                    ParsedReceiptItem(
                        name=name,
                        quantity=quantity,
                        unit_price=unit_price,
                        line_total=line_total,
                    )
                )
                idx += 4
                continue

        fallback_item = _parse_item_line(name)
        if fallback_item is not None:
            items.append(fallback_item)
        idx += 1

    return items


def _parse_item_line(line: str) -> ParsedReceiptItem | None:
    normalized = _clean_text(line)
    if len(normalized) < 2 or _looks_like_header(normalized):
        return None

    amount_matches = list(re.finditer(r"-?\d[\d,]*(?:\.\d{1,2})?", normalized))
    if not amount_matches:
        return None

    last_amount = _parse_amount(amount_matches[-1].group())
    if last_amount is None:
        return None

    name_part = normalized[: amount_matches[0].start()].strip()
    if not name_part or any(keyword in normalized for keyword in ("합계", "부가세", "거스름돈", "현금", "카드")):
        return None

    quantity = Decimal("1")
    unit_price = None
    if len(amount_matches) >= 3:
        possible_quantity = _parse_amount(amount_matches[-3].group())
        possible_unit_price = _parse_amount(amount_matches[-2].group())
        if possible_quantity is not None:
            quantity = possible_quantity
        unit_price = possible_unit_price
    elif len(amount_matches) >= 2:
        possible_first = _parse_amount(amount_matches[-2].group())
        if possible_first is not None and possible_first <= 1000:
            quantity = possible_first
        else:
            unit_price = possible_first

    return ParsedReceiptItem(
        name=name_part,
        quantity=quantity,
        unit_price=unit_price,
        line_total=last_amount,
    )


def parse_receipt(ocr_rows: list[dict[str, Any]], image_path: str) -> ParsedReceipt:
    sorted_rows = sorted(
        ocr_rows,
        key=lambda row: (_box_center_y(row.get("box")), _box_left_x(row.get("box"))),
    )
    lines = [_clean_text(row["text"]) for row in sorted_rows if _clean_text(row.get("text", ""))]
    raw_text = "\n".join(lines)

    store_name = _extract_store_name(lines)
    receipt_date = None
    for line in lines:
        receipt_date = _parse_datetime(line)
        if receipt_date is not None:
            break

    total_amount = _find_total_amount(lines)

    items = _extract_items_from_menu_block(lines)
    if not items:
        items = []
        for line in lines:
            item = _parse_item_line(line)
            if item is not None:
                items.append(item)

    return ParsedReceipt(
        store_name=store_name,
        receipt_date=receipt_date,
        total_amount=total_amount,
        currency="KRW",
        raw_text=raw_text,
        raw_ocr=ocr_rows,
        items=items,
        image_path=image_path,
    )


def extract_receipt_from_upload(upload_file) -> ParsedReceipt:
    image_path = save_upload_file(upload_file)
    ocr_rows = run_ocr(image_path)
    return parse_receipt(ocr_rows, image_path=image_path)

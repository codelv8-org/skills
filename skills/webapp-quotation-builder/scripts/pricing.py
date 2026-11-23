#!/usr/bin/env python3
"""ตรวจข้อมูลและคำนวณราคา Web App โดยปฏิเสธข้อมูลที่ไม่ครบหรือผิดเงื่อนไข

ใช้โมดูลนี้เป็นแหล่งยอดเงินของ PDF ลูกค้า ใช้ Decimal คำนวณเงินและรับอัตราภาษีจากข้อมูลที่ยืนยันแล้ว
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

SATANG = Decimal("0.01")


class QuoteValidationError(ValueError):
    pass


def D(value, field: str) -> Decimal:
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise QuoteValidationError(f"{field}: invalid number {value!r}") from exc
    if not dec.is_finite():
        raise QuoteValidationError(f"{field}: non-finite number")
    return dec


def money(amount: Decimal) -> Decimal:
    return amount.quantize(SATANG, rounding=ROUND_HALF_UP)


def money_text(amount: Decimal | str) -> str:
    return f"{money(D(amount,'amount')):,.2f}"


def required_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise QuoteValidationError(f"{field} is required")
    return value.strip()


def load_quote(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        quote = json.load(f)
    if not isinstance(quote, dict):
        raise QuoteValidationError("Root must be JSON object")
    return quote


def calculate(quote: dict) -> dict:
    demo = quote.get("demo") is True
    try:
        provider = quote["provider"]
        customer = quote["customer"]
        header = quote["quotation"]
        pricing = quote["pricing"]
        milestones = quote["milestones"]
        scope = quote["scope"]
        delivery = quote["delivery"]
        after_sales = quote["after_sales"]
    except (KeyError, TypeError) as exc:
        raise QuoteValidationError(f"Missing required section: {exc}") from exc

    for section_name, section in (
        ("provider", provider), ("customer", customer), ("quotation", header),
        ("pricing", pricing), ("scope", scope), ("delivery", delivery),
        ("after_sales", after_sales),
    ):
        if not isinstance(section, dict):
            raise QuoteValidationError(f"{section_name} must be object")

    for field in ("name", "address", "contact"):
        required_text(provider.get(field), f"provider.{field}")
    for field in ("name", "address", "contact"):
        required_text(customer.get(field), f"customer.{field}")
    for field in ("number", "issue_date", "valid_until", "project_name", "summary", "lead_time", "acceptance", "ip_terms", "revision_policy"):
        required_text(header.get(field), f"quotation.{field}")
    if str(header.get("currency", "THB")).upper() != "THB":
        raise QuoteValidationError("Currently only THB supported; no silent FX conversion")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,49}", header["number"]):
        raise QuoteValidationError("quotation.number: use 1-50 letters/numbers/hyphen/underscore/dot")
    try:
        issue_date = date.fromisoformat(header["issue_date"])
        valid_until = date.fromisoformat(header["valid_until"])
    except ValueError as exc:
        raise QuoteValidationError("issue_date and valid_until must be YYYY-MM-DD") from exc
    if valid_until < issue_date:
        raise QuoteValidationError("Quotation expiry cannot precede issue date")

    if not isinstance(provider.get("vat_registered"), bool):
        raise QuoteValidationError("provider.vat_registered must be explicitly true or false; do not guess")
    vat_registered = provider["vat_registered"]
    rate = D(pricing.get("vat_rate"), "pricing.vat_rate")
    if rate < 0 or rate > 100:
        raise QuoteValidationError("VAT rate must be 0..100")
    if vat_registered and rate <= 0:
        raise QuoteValidationError("VAT registered seller requires confirmed positive VAT rate")
    if not vat_registered and rate != 0:
        raise QuoteValidationError("Non-VAT-registered seller cannot add VAT")
    if vat_registered and not demo:
        tin = re.sub(r"\D", "", str(provider.get("tax_id", "")))
        if len(tin) != 13:
            raise QuoteValidationError("VAT registered issuer must supply 13-digit tax ID for production quote")

    forbidden = ("[กรอก", "[ระบุ", "todo", "tbd", "xxx", "สมมติ", "example.invalid")
    if not demo:
        strings = [provider.get("name", ""), provider.get("address", ""), customer.get("name", ""), customer.get("address", ""), header.get("project_name", "")]
        if any(any(f in str(x).lower() for f in forbidden) for x in strings):
            raise QuoteValidationError("Production quote contains placeholders/fake example data")

    items = pricing.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= 8:
        raise QuoteValidationError("pricing.items must have 1..8 grouped work packages for A4")
    computed_items = []
    subtotal = Decimal("0")
    for idx, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise QuoteValidationError(f"pricing.items[{idx}] must be object")
        name = required_text(item.get("name"), f"items[{idx}].name")
        required_text(item.get("detail"), f"items[{idx}].detail")
        required_text(item.get("unit"), f"items[{idx}].unit")
        quantity = D(item.get("quantity"), f"items[{idx}].quantity")
        unit_price = D(item.get("unit_price"), f"items[{idx}].unit_price")
        if quantity <= 0 or quantity > 10000 or unit_price < 0:
            raise QuoteValidationError(f"{name}: quantity must be >0; unit_price >=0")
        line_total = money(quantity * unit_price)
        subtotal += line_total
        computed_items.append({"number": idx, "name": name, "detail": item["detail"], "unit": item["unit"], "quantity": quantity, "unit_price": money(unit_price), "total": line_total})
    subtotal = money(subtotal)
    if subtotal <= 0:
        raise QuoteValidationError("Quote total must be positive")
    discount = money(D(pricing.get("discount", 0), "pricing.discount"))
    if not 0 <= discount < subtotal:
        raise QuoteValidationError("Discount must be between 0 and subtotal (exclusive)")
    taxable = money(subtotal - discount)
    vat = money(taxable * rate / Decimal("100")) if vat_registered else Decimal("0.00")
    total = money(taxable + vat)

    if not isinstance(milestones, list) or not 1 <= len(milestones) <= 5:
        raise QuoteValidationError("milestones must have 1..5 payment events")
    percent_sum = sum((D(m.get("percent"), f"milestones[{i}].percent") for i, m in enumerate(milestones)), Decimal("0"))
    if percent_sum != 100:
        raise QuoteValidationError(f"Milestone percentages must add to 100, got {percent_sum}")
    computed_milestones = []
    remaining = total
    for idx, entry in enumerate(milestones):
        required_text(entry.get("label"), f"milestones[{idx}].label")
        required_text(entry.get("trigger"), f"milestones[{idx}].trigger")
        percent = D(entry["percent"], f"milestones[{idx}].percent")
        if percent <= 0:
            raise QuoteValidationError("Milestone percentage must be positive")
        part = money(total * percent / Decimal("100")) if idx + 1 < len(milestones) else remaining
        remaining -= part
        computed_milestones.append({**entry, "percent": percent, "amount": part})
    if sum((m["amount"] for m in computed_milestones), Decimal("0")) != total:
        raise QuoteValidationError("Milestone allocation invariant failed")

    modules = scope.get("modules")
    phases = delivery.get("phases")
    if not isinstance(modules, list) or not 1 <= len(modules) <= 18:
        raise QuoteValidationError("scope.modules needs 1..18 scoped modules; slides paginate in groups of six")
    if not isinstance(phases, list) or not 1 <= len(phases) <= 15:
        raise QuoteValidationError("delivery.phases needs 1..15 phases; slides paginate in groups of five")
    if not isinstance(delivery.get("handover"), list) or not 1 <= len(delivery["handover"]) <= 4:
        raise QuoteValidationError("delivery.handover must have 1..4 grouped deliverables for slides")
    for field in ("warranty", "change_rate"):
        required_text(after_sales.get(field), f"after_sales.{field}")
    if not isinstance(scope.get("not_included"), list) or len(scope["not_included"]) > 3:
        raise QuoteValidationError("scope.not_included must be list with 0..3 grouped exclusions")
    for field in ("included", "excluded"):
        if not isinstance(after_sales.get(field), list) or len(after_sales[field]) > 3:
            raise QuoteValidationError(f"after_sales.{field} must be list with 0..3 grouped points")

    return {
        "demo": demo,
        "items": computed_items,
        "subtotal": subtotal,
        "discount": discount,
        "taxable": taxable,
        "vat": vat,
        "vat_rate": rate,
        "vat_registered": vat_registered,
        "total": total,
        "milestones": computed_milestones,
        "issue_date": issue_date,
        "valid_until": valid_until,
        "quote_id": header["number"],
    }


def public_math(calc):
    return {
        "subtotal": str(calc["subtotal"]), "discount": str(calc["discount"]),
        "taxable": str(calc["taxable"]), "vat": str(calc["vat"]),
        "vat_rate": str(calc["vat_rate"]), "vat_registered": calc["vat_registered"],
        "total": str(calc["total"]),
        "milestones": [dict(label=x["label"], percent=str(x["percent"]), amount=str(x["amount"]), trigger=x["trigger"]) for x in calc["milestones"]],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", help="Path to quote-data JSON")
    args = parser.parse_args()
    calc = calculate(load_quote(args.json_file))
    print(json.dumps(public_math(calc), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

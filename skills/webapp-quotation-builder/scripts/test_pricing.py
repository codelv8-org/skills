#!/usr/bin/env python3
"""ทดสอบการคำนวณและการปฏิเสธข้อมูลที่ไม่พร้อมออกใบเสนอราคา"""

import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path

from pricing import QuoteValidationError, calculate, load_quote

EXAMPLE = Path(__file__).resolve().parents[1] / "assets" / "quote-data.example.json"


class PricingTests(unittest.TestCase):
    def setUp(self):
        self.data = load_quote(EXAMPLE)

    def test_basic_nonvat(self):
        c = calculate(self.data)
        self.assertEqual(c["subtotal"], Decimal("69000.00"))
        self.assertEqual(c["vat"], Decimal("0.00"))
        self.assertEqual(c["total"], Decimal("69000.00"))
        self.assertEqual(sum(m["amount"] for m in c["milestones"]), c["total"])

    def test_vat_and_discount(self):
        self.data["provider"]["vat_registered"] = True
        self.data["provider"]["tax_id"] = "0000000000000"  # ใช้ในชุดทดสอบเท่านั้น
        self.data["pricing"]["vat_rate"] = 7
        self.data["pricing"]["discount"] = 9000
        c = calculate(self.data)
        self.assertEqual(c["taxable"], Decimal("60000.00"))
        self.assertEqual(c["vat"], Decimal("4200.00"))
        self.assertEqual(c["total"], Decimal("64200.00"))
        self.assertEqual([m["amount"] for m in c["milestones"]], [Decimal("19260.00"), Decimal("25680.00"), Decimal("19260.00")])

    def test_vat_unregistered_refused(self):
        self.data["pricing"]["vat_rate"] = 7
        with self.assertRaisesRegex(QuoteValidationError, "Non-VAT-registered"):
            calculate(self.data)

    def test_vat_unknown_refused(self):
        self.data["provider"]["vat_registered"] = None
        with self.assertRaisesRegex(QuoteValidationError, "explicitly"):
            calculate(self.data)

    def test_milestone_rounding_residual(self):
        self.data["pricing"]["items"][0]["unit_price"] = 9000.01
        self.data["milestones"] = [
            {"label": "งวด1", "percent": 33, "trigger": "อนุมัติงวด 1"},
            {"label": "งวด2", "percent": 33, "trigger": "อนุมัติงวด 2"},
            {"label": "งวด3", "percent": 34, "trigger": "อนุมัติงวด 3"},
        ]
        c = calculate(self.data)
        self.assertEqual(c["total"], Decimal("69000.01"))
        self.assertEqual(sum(m["amount"] for m in c["milestones"]), Decimal("69000.01"))

    def test_bad_split_refused(self):
        self.data["milestones"][0]["percent"] = 31
        with self.assertRaisesRegex(QuoteValidationError, "100"):
            calculate(self.data)

    def test_production_requires_real_client(self):
        self.data["demo"] = False
        with self.assertRaisesRegex(QuoteValidationError, "placeholders"):
            calculate(self.data)

    def test_items_too_many_refused(self):
        self.data["pricing"]["items"] *= 3
        with self.assertRaisesRegex(QuoteValidationError, "1..8"):
            calculate(self.data)

    def test_negative_discount_refused(self):
        self.data["pricing"]["discount"] = -1
        with self.assertRaisesRegex(QuoteValidationError, "Discount"):
            calculate(self.data)

    def test_date_order_refused(self):
        self.data["quotation"]["valid_until"] = "2026-11-10"
        with self.assertRaisesRegex(QuoteValidationError, "expiry"):
            calculate(self.data)


if __name__ == "__main__":
    unittest.main(verbosity=2)

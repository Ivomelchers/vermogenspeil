"""Tests for Saxo CSV parser."""

from datetime import datetime
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from apps.integrations.saxo.parser import parse_saxo_csv, SaxoRow
from apps.portfolio.models import TransactionType


class SaxoParserTestCase(TestCase):
    def test_parse_saxo_handles_zero_quantity(self):
        """Test that rows with zero quantity are skipped."""
        csv_content = """Dato,Tid,Symbol,Beskrivelse,Type,Antal,Kurs,Beløb,Gebyr
01-01-2026,09:30:00,IWDA,iShares Core MSCI World,BUY,0,100.50,0,0
"""
        result = parse_saxo_csv(csv_content)

        # Zero quantity rows are skipped
        assert len(result.rows) == 0
        assert len(result.skipped) == 1

    def test_parse_saxo_decimal_parsing(self):
        """Test decimal parsing with both comma and dot separators."""
        from apps.integrations.saxo.parser import _parse_decimal

        assert _parse_decimal("100.50") == Decimal("100.50")
        assert _parse_decimal("100,50") == Decimal("100.50")
        assert _parse_decimal("0") == Decimal("0")
        assert _parse_decimal("") == Decimal("0")

    def test_parse_saxo_transaction_type_normalization(self):
        """Test transaction type normalization."""
        from apps.integrations.saxo.parser import _normalize_transaction_type

        assert _normalize_transaction_type("BUY") == TransactionType.BUY
        assert _normalize_transaction_type("buy") == TransactionType.BUY
        assert _normalize_transaction_type("KØBT") == TransactionType.BUY
        assert _normalize_transaction_type("SELL") == TransactionType.SELL
        assert _normalize_transaction_type("DIVIDEND") == TransactionType.DIVIDEND
        assert _normalize_transaction_type("DEPOSIT") == TransactionType.DEPOSIT

    def test_saxo_row_dataclass(self):
        """Test SaxoRow dataclass creation."""
        now = timezone.now()
        row = SaxoRow(
            external_id="test_123",
            symbol="IWDA",
            name="iShares World",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("10"),
            price_eur=Decimal("100.50"),
            fee_eur=Decimal("5.00"),
            total_eur=Decimal("1005.00"),
            occurred_at=now,
            transaction_hash="abc123",
        )

        assert row.symbol == "IWDA"
        assert row.quantity == Decimal("10")
        assert row.currency == "EUR"

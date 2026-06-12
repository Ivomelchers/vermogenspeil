"""Tests for Saxo CSV parser."""

from datetime import datetime
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from apps.integrations.saxo.parser import parse_saxo_csv
from apps.portfolio.models import TransactionType


SAMPLE_SAXO_CSV = """Dato,Tid,Symbol,Beskrivelse,Type,Antal,Kurs,Beløb,Gebyr
01-01-2026,09:30:00,IWDA,iShares Core MSCI World ETF UCITS ETF (Acc),BUY,10,100.50,1005.00,5.00
02-01-2026,10:15:00,ASML,ASML Holding NV,SELL,5,250.75,1253.75,10.00
03-01-2026,14:45:00,IESX,iShares Core S&P 500 ETF,BUY,20,500.00,10000.00,20.00
"""


class SaxoParserTestCase(TestCase):
    def test_parse_basic_saxo_csv(self):
        """Test parsing a basic Saxo CSV file."""
        result = parse_saxo_csv(SAMPLE_SAXO_CSV)

        assert len(result.rows) == 3
        assert len(result.skipped) == 0

        # Check first row (BUY)
        row = result.rows[0]
        assert row.symbol == "IWDA"
        assert row.name == "iShares Core MSCI World ETF UCITS ETF (Acc)"
        assert row.transaction_type == TransactionType.BUY
        assert row.quantity == Decimal("10")
        assert row.price_eur == Decimal("100.50")
        assert row.fee_eur == Decimal("5.00")
        assert row.total_eur == Decimal("1005.00")

        # Check second row (SELL)
        row = result.rows[1]
        assert row.symbol == "ASML"
        assert row.transaction_type == TransactionType.SELL
        assert row.quantity == Decimal("5")
        assert row.price_eur == Decimal("250.75")

        # Check third row
        row = result.rows[2]
        assert row.symbol == "IESX"
        assert row.quantity == Decimal("20")

    def test_parse_saxo_with_different_delimiter(self):
        """Test parsing Saxo CSV with semicolon delimiter."""
        csv_content = """Dato;Tid;Symbol;Beskrivelse;Type;Antal;Kurs;Beløb;Gebyr
01-01-2026;09:30:00;IWDA;iShares Core MSCI World;BUY;10;100,50;1005,00;5,00
"""
        result = parse_saxo_csv(csv_content)

        assert len(result.rows) == 1
        row = result.rows[0]
        assert row.symbol == "IWDA"
        assert row.quantity == Decimal("10")
        assert row.price_eur == Decimal("100.50")

    def test_parse_saxo_with_dividend(self):
        """Test parsing Saxo CSV with dividend transaction."""
        csv_content = """Dato,Tid,Symbol,Beskrivelse,Type,Antal,Kurs,Beløb,Gebyr
01-01-2026,09:30:00,IWDA,iShares Core MSCI World,DIVIDEND,0,0,50.00,0
"""
        result = parse_saxo_csv(csv_content)

        assert len(result.rows) == 1
        row = result.rows[0]
        assert row.transaction_type == TransactionType.DIVIDEND
        assert row.total_eur == Decimal("50.00")

    def test_parse_saxo_with_deposit(self):
        """Test parsing Saxo CSV with deposit."""
        csv_content = """Dato,Tid,Symbol,Beskrivelse,Type,Antal,Kurs,Beløb,Gebyr
01-01-2026,09:30:00,EUR,Deposit,DEPOSIT,0,1,1000.00,0
"""
        result = parse_saxo_csv(csv_content)

        assert len(result.rows) == 1
        row = result.rows[0]
        assert row.transaction_type == TransactionType.DEPOSIT
        assert row.total_eur == Decimal("1000.00")

    def test_parse_saxo_handles_zero_quantity(self):
        """Test that rows with zero quantity are skipped."""
        csv_content = """Dato,Tid,Symbol,Beskrivelse,Type,Antal,Kurs,Beløb,Gebyr
01-01-2026,09:30:00,IWDA,iShares Core MSCI World,BUY,0,100.50,0,0
"""
        result = parse_saxo_csv(csv_content)

        assert len(result.rows) == 0
        assert len(result.skipped) == 1
        assert "nul" in result.skipped[0].reason.lower()

    def test_parse_saxo_deduplication_hash(self):
        """Test that transaction hashes are generated for deduplication."""
        result = parse_saxo_csv(SAMPLE_SAXO_CSV)

        row = result.rows[0]
        assert row.transaction_hash is not None
        assert len(row.transaction_hash) == 64  # SHA256 hex
        assert row.external_id is not None

from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.pricing.instrument_resolver import resolve_yahoo_ticker
from apps.pricing.models import InstrumentMapping, MappingSource
from apps.pricing.openfigi_client import OpenFigiMatch
from apps.pricing.services.instrument_service import (
    ensure_instrument_mapping,
    sync_seed_mappings,
)


class InstrumentServiceTests(TestCase):
    def test_sync_seed(self):
        sync_seed_mappings()
        self.assertTrue(InstrumentMapping.objects.filter(isin="IE00B4L5Y983").exists())
        self.assertEqual(resolve_yahoo_ticker("IE00B4L5Y983"), "IWDA.AS")

    @override_settings(OPENFIGI_ENABLED=True)
    @patch("apps.pricing.services.instrument_service.fetch_isin_match")
    def test_openfigi_creates_mapping(self, mock_fetch):
        mock_fetch.return_value = OpenFigiMatch(
            yahoo_ticker="VWCE.AS",
            mic="XAMS",
            exch_code="AS",
            security_type="ETF",
            asset_type="etf",
        )
        mapping = ensure_instrument_mapping("XX0000000001", allow_network=True)
        self.assertIsNotNone(mapping)
        assert mapping is not None
        self.assertEqual(mapping.source, MappingSource.OPENFIGI)
        self.assertEqual(resolve_yahoo_ticker("XX0000000001"), "VWCE.AS")

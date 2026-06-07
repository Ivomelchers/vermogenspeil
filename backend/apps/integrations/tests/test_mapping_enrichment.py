"""Deterministische kolom-enrichment zonder AI."""

from django.test import SimpleTestCase

from apps.integrations.csv.mapping_enrichment import enrich_column_mapping
from apps.integrations.degiro.column_schema import DEGIRO_SCHEMA

V2_HEADERS = [
    "Settlement date",
    "Execution time",
    "Security label",
    "Identifier ISIN",
    "Segment",
    "Trading floor",
    "Units held",
    "Price per unit",
    "Amount local",
    "EUR value",
    "Currency pair",
    "Conversion charge",
    "Broker fee",
    "Net settlement",
    "Ticket id",
]


class MappingEnrichmentTests(SimpleTestCase):
    def test_v2_headers_enriched_without_ai(self):
        mapped = enrich_column_mapping(
            DEGIRO_SCHEMA,
            original_headers=V2_HEADERS,
            mapped={},
        )
        self.assertEqual(mapped["date"], "Settlement date")
        self.assertEqual(mapped["total"], "Net settlement")
        self.assertEqual(mapped["product"], "Security label")
        self.assertEqual(mapped["isin"], "Identifier ISIN")
        self.assertEqual(mapped["order_id"], "Ticket id")
        self.assertNotEqual(mapped.get("total"), "EUR value")

    def test_enrichment_does_not_overwrite_existing(self):
        mapped = enrich_column_mapping(
            DEGIRO_SCHEMA,
            original_headers=V2_HEADERS,
            mapped={"date": "Settlement date", "total": "Net settlement"},
        )
        self.assertEqual(mapped["date"], "Settlement date")
        self.assertEqual(mapped["product"], "Security label")

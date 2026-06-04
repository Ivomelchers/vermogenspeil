"""ISIN → Yahoo-ticker: DB-cache, seed JSON, OpenFIGI (platform-onafhankelijk)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from django.conf import settings
from django.db import transaction

from apps.portfolio.models import Asset, AssetType
from apps.pricing.isin import looks_like_isin
from apps.pricing.models import InstrumentMapping, MappingSource
from apps.pricing.openfigi_client import fetch_isin_match, openfigi_enabled

logger = logging.getLogger(__name__)

_SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "euronext_isin_tickers.json"


@dataclass
class ResolveReport:
    requested: int = 0
    resolved: int = 0
    already_known: int = 0
    failed: int = 0
    isins_failed: list[str] = field(default_factory=list)


def load_seed_json() -> dict[str, str]:
    try:
        raw = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Seed ISIN-map niet geladen: %s", exc)
        return {}
    if not isinstance(raw, dict):
        return {}
    return {str(k).upper(): str(v) for k, v in raw.items()}


def sync_seed_mappings() -> tuple[int, int]:
    """Returns (created, updated). Overschrijft ook OpenFIGI-tickers in de seed."""
    created = 0
    updated = 0
    for isin, ticker in load_seed_json().items():
        row, was_created = InstrumentMapping.objects.update_or_create(
            isin=isin,
            defaults={"yahoo_ticker": ticker, "source": MappingSource.SEED_JSON},
        )
        if was_created:
            created += 1
        elif row.yahoo_ticker != ticker or row.source != MappingSource.SEED_JSON:
            row.yahoo_ticker = ticker
            row.source = MappingSource.SEED_JSON
            row.save(update_fields=["yahoo_ticker", "source", "updated_at"])
            updated += 1
    return created, updated


def get_mapping(isin: str) -> InstrumentMapping | None:
    upper = isin.upper().strip()
    if not looks_like_isin(upper):
        return None
    return InstrumentMapping.objects.filter(isin=upper).first()


def asset_type_for_isin(isin: str) -> str:
    mapping = get_mapping(isin)
    return mapping.asset_type if mapping and mapping.asset_type else ""


@transaction.atomic
def ensure_instrument_mapping(
    isin: str,
    *,
    mic_hint: str = "",
    allow_network: bool = True,
) -> InstrumentMapping | None:
    upper = isin.upper().strip()
    if not looks_like_isin(upper):
        return None

    existing = InstrumentMapping.objects.filter(isin=upper).first()
    if existing:
        seed = load_seed_json()
        if upper in seed and (
            existing.yahoo_ticker != seed[upper]
            or existing.source == MappingSource.OPENFIGI
        ):
            existing.yahoo_ticker = seed[upper]
            existing.source = MappingSource.SEED_JSON
            existing.save(update_fields=["yahoo_ticker", "source", "updated_at"])
        elif mic_hint and not existing.mic:
            existing.mic = mic_hint.upper()
            existing.save(update_fields=["mic", "updated_at"])
        return existing

    seed = load_seed_json()
    if upper in seed:
        return InstrumentMapping.objects.create(
            isin=upper,
            yahoo_ticker=seed[upper],
            mic=(mic_hint or "").upper(),
            source=MappingSource.SEED_JSON,
        )

    if allow_network and openfigi_enabled():
        match = fetch_isin_match(upper, mic_hint=mic_hint)
        if match:
            return InstrumentMapping.objects.create(
                isin=upper,
                yahoo_ticker=match.yahoo_ticker,
                mic=match.mic or mic_hint.upper(),
                asset_type=match.asset_type,
                security_type=match.security_type,
                source=MappingSource.OPENFIGI,
            )
    return None


def ensure_instrument_mappings(
    isins: list[str],
    *,
    mic_hints: dict[str, str] | None = None,
    allow_network: bool = True,
    max_network_calls: int | None = None,
) -> ResolveReport:
    hints = {k.upper(): v for k, v in (mic_hints or {}).items()}
    unique = sorted({s.upper() for s in isins if looks_like_isin(s)})
    report = ResolveReport(requested=len(unique))
    limit = max_network_calls
    if limit is None:
        limit = getattr(settings, "INSTRUMENT_RESOLVE_MAX_PER_IMPORT", 15)

    network_used = 0
    for isin in unique:
        if InstrumentMapping.objects.filter(isin=isin).exists():
            report.already_known += 1
            continue
        can_network = allow_network and network_used < limit
        mapping = ensure_instrument_mapping(
            isin,
            mic_hint=hints.get(isin, ""),
            allow_network=can_network,
        )
        if mapping:
            report.resolved += 1
            if mapping.source == MappingSource.OPENFIGI:
                network_used += 1
        else:
            report.failed += 1
            report.isins_failed.append(isin)
    return report


def collect_isins_from_parse_rows(rows: list) -> tuple[list[str], dict[str, str]]:
    isins: list[str] = []
    mic_hints: dict[str, str] = {}
    for row in rows:
        symbol = getattr(row, "symbol", "") or ""
        if not looks_like_isin(symbol):
            continue
        upper = symbol.upper()
        isins.append(upper)
        mic = getattr(row, "mic", "") or ""
        if mic:
            mic_hints[upper] = mic.upper()
    return isins, mic_hints


def resolve_after_csv_import(parse_result) -> ResolveReport:
    isins, mic_hints = collect_isins_from_parse_rows(parse_result.rows)
    if not isins:
        return ResolveReport()
    return ensure_instrument_mappings(isins, mic_hints=mic_hints, allow_network=True)


def resolve_unmapped_portfolio_isins(*, max_calls: int = 20) -> ResolveReport:
    symbols = [
        s.upper()
        for s in Asset.objects.exclude(asset_type=AssetType.CASH)
        .values_list("symbol", flat=True)
        .distinct()
        if looks_like_isin(s)
    ]
    known = set(InstrumentMapping.objects.filter(isin__in=symbols).values_list("isin", flat=True))
    missing = [s for s in symbols if s not in known]
    return ensure_instrument_mappings(missing, allow_network=True, max_network_calls=max_calls)


def list_unmapped_isins(symbols: list[str]) -> list[str]:
    known = set(InstrumentMapping.objects.values_list("isin", flat=True))
    seed = set(load_seed_json().keys())
    all_known = known | seed
    return [s.upper() for s in symbols if looks_like_isin(s) and s.upper() not in all_known]

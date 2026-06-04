"""DEGIRO-specifieke kolomvoorkeuren (één plek voor parser + schema-analyse)."""

# (subtotaal-kolom, afschrijfbedrag-kolom) — normalized header keys
_SETTLEMENT_TOTAL_PAIRS: tuple[tuple[str, str], ...] = (
    ("waarde eur", "totaal eur"),
    ("value", "total"),
)


def prefer_settlement_total_column(
    columns: dict[str, str | None],
    header_map: dict[str, str],
) -> dict[str, str | None]:
    """
    DEGIRO heeft vaak een subtotaal (Value / Waarde EUR) én het echte
    afschrijfbedrag (Total / Totaal EUR, incl. kosten). Gebruik altijd Total.
    """
    for subtotal_key, settlement_key in _SETTLEMENT_TOTAL_PAIRS:
        subtotal = header_map.get(subtotal_key)
        settlement = header_map.get(settlement_key)
        if not subtotal or not settlement:
            continue
        if columns.get("total") == subtotal:
            updated = dict(columns)
            updated["total"] = settlement
            return updated
    return columns


def prefer_totaal_eur_column(
    mapped_columns: dict[str, str],
    header_map: dict[str, str],
) -> dict[str, str]:
    """Schema-analyse: zelfde logica als parser-resolver."""
    totaal = header_map.get("totaal eur")
    waarde = header_map.get("waarde eur")
    if not totaal or not waarde:
        return mapped_columns
    if mapped_columns.get("total") != waarde:
        return mapped_columns
    updated = dict(mapped_columns)
    updated["total"] = totaal
    return updated


def prefer_totaal_in_resolver(
    columns: dict[str, str | None],
    header_map: dict[str, str],
) -> dict[str, str | None]:
    """Parser-resolver: canonical → CSV-kolomnaam."""
    return prefer_settlement_total_column(columns, header_map)

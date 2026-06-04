"""DEGIRO-specifieke kolomvoorkeuren (één plek voor parser + schema-analyse)."""


def prefer_totaal_eur_column(
    mapped_columns: dict[str, str],
    header_map: dict[str, str],
) -> dict[str, str]:
    """
    NL-export heeft 'Waarde EUR' én 'Totaal EUR' — total = afschrijfbedrag (Totaal EUR).
    """
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
    waarde = header_map.get("waarde eur")
    totaal = header_map.get("totaal eur")
    if not totaal or not waarde or columns.get("total") != waarde:
        return columns
    updated = dict(columns)
    updated["total"] = totaal
    return updated

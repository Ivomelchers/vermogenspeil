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


def prefer_settlement_total_mapped(
    mapped_columns: dict[str, str],
    norm_to_original: dict[str, str],
) -> dict[str, str]:
    """Schema-analyse: Value/Waarde → Total/Totaal EUR wanneer beide aanwezig."""
    as_resolver: dict[str, str | None] = dict(mapped_columns)
    fixed = prefer_settlement_total_column(as_resolver, norm_to_original)
    return {k: v for k, v in fixed.items() if v}


def prefer_totaal_eur_column(
    mapped_columns: dict[str, str],
    header_map: dict[str, str],
) -> dict[str, str]:
    """Schema-analyse: NL Waarde EUR → Totaal EUR."""
    result = prefer_settlement_total_mapped(mapped_columns, header_map)
    totaal = header_map.get("totaal eur")
    waarde = header_map.get("waarde eur")
    if totaal and waarde and result.get("total") == waarde:
        updated = dict(result)
        updated["total"] = totaal
        return updated
    return result


def prefer_totaal_in_resolver(
    columns: dict[str, str | None],
    header_map: dict[str, str],
) -> dict[str, str | None]:
    """Parser-resolver: canonical → CSV-kolomnaam."""
    return prefer_settlement_total_column(columns, header_map)


def degiro_diagnostic_column_notes(
    mapped_columns: dict[str, str],
    norm_to_original: dict[str, str],
) -> tuple[set[str], list[dict]]:
    """
    Kolommen die niet als 'unmapped' getoond worden + duidelijke info voor admin/preview.
    """
    exclude_normalized: set[str] = set()
    notes: list[dict] = []

    for subtotal_key, settlement_key in _SETTLEMENT_TOTAL_PAIRS:
        if settlement_key not in norm_to_original:
            continue
        if mapped_columns.get("total") != norm_to_original.get(settlement_key):
            continue
        if subtotal_key in norm_to_original:
            exclude_normalized.add(subtotal_key)
            notes.append(
                {
                    "code": "column_by_design",
                    "severity": "info",
                    "message": (
                        f"Kolom '{norm_to_original[subtotal_key]}' wordt bewust overgeslagen — "
                        f"'{norm_to_original[settlement_key]}' is het transactiebedrag (incl. kosten)."
                    ),
                    "file_header": norm_to_original[subtotal_key],
                }
            )
        break

    optional_info = {
        "beurs": (
            "Kolom 'Beurs' is niet nodig voor de import; de beurs staat in 'Uitvoeringsplaats' (MIC)."
        ),
        "autofx kosten": (
            "Kolom 'AutoFX Kosten' is optioneel; wisselkosten zitten meestal al in 'Totaal EUR'."
        ),
    }
    for norm_key, message in optional_info.items():
        if norm_key not in norm_to_original:
            continue
        exclude_normalized.add(norm_key)
        notes.append(
            {
                "code": "column_optional",
                "severity": "info",
                "message": message,
                "file_header": norm_to_original[norm_key],
            }
        )

    return exclude_normalized, notes

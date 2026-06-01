"""Box 3-rapport als PDF (reportlab)."""

import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FORFAIT_STEP_LABELS: dict[str, str] = {
    "schulden_aftrekbaar_eur": "Aftrekbare schulden",
    "rendement_bank_eur": "Rendement banktegoeden",
    "rendement_overig_eur": "Rendement overige bezittingen",
    "rendement_schulden_eur": "Rendement schulden",
    "belastbaar_rendement_eur": "Belastbaar rendement (R)",
    "rendementsgrondslag_eur": "Rendementsgrondslag (RG)",
    "grondslag_sparen_beleggen_eur": "Grondslag sparen en beleggen (GSB)",
    "aandeel_percent": "Aandeel (%)",
    "voordeel_eur": "Voordeel sparen en beleggen (V)",
    "belasting_bruto_eur": "Belasting bruto",
    "aftrek_dubbele_belasting_eur": "Aftrek dubbele belasting",
    "belasting_netto_eur": "Te betalen (forfaitair)",
}

FORFAIT_STEP_ORDER: list[str] = list(FORFAIT_STEP_LABELS.keys())

WERKELIJK_COMPONENT_LABELS: dict[str, str] = {
    "dividend_eur": "Dividend",
    "rente_bank_eur": "Rente banktegoeden",
    "huur_eur": "Huurinkomsten",
    "staking_eur": "Staking / crypto-rente",
    "overige_inkomsten_eur": "Overige inkomsten",
    "reguliere_voordelen_eur": "Reguliere voordelen",
    "waardemutatie_eur": "Waardemutatie",
    "bijtelling_eur": "Bijtelling vastgoed",
    "rente_schulden_eur": "Rente schulden (RNT_s)",
    "woz_investering_eur": "WOZ-verhogende investeringen",
}

_MONTHS_NL = (
    "januari",
    "februari",
    "maart",
    "april",
    "mei",
    "juni",
    "juli",
    "augustus",
    "september",
    "oktober",
    "november",
    "december",
)


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Heading1"],
            fontSize=16,
            textColor=colors.HexColor("#14213D"),
            spaceAfter=12,
        ),
        "heading": ParagraphStyle(
            "Heading",
            parent=base["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#1E3A5F"),
            spaceBefore=14,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#14213D"),
        ),
        "muted": ParagraphStyle(
            "Muted",
            parent=base["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#4A5878"),
        ),
    }


def _parse_decimal(value: str) -> Decimal | None:
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return Decimal(raw.replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def format_eur_display(value: str) -> str:
    """Nederlands bedrag: € 36.230,16."""
    amount = _parse_decimal(value)
    if amount is None:
        return str(value)
    negative = amount < 0
    amount = abs(amount)
    whole, _, frac = f"{amount:.2f}".partition(".")
    grouped_parts: list[str] = []
    while len(whole) > 3:
        grouped_parts.insert(0, whole[-3:])
        whole = whole[:-3]
    if whole:
        grouped_parts.insert(0, whole)
    grouped = ".".join(grouped_parts) if grouped_parts else "0"
    prefix = "- " if negative else ""
    return f"{prefix}€ {grouped},{frac}"


def format_step_display(key: str, value: str) -> str:
    if key == "aandeel_percent":
        amount = _parse_decimal(value)
        if amount is not None:
            whole, _, frac = f"{amount:.2f}".partition(".")
            return f"{whole},{frac}%"
        return f"{value}%"
    if key.endswith("_eur") or key in ("belasting_bruto_eur", "belasting_netto_eur"):
        return format_eur_display(value)
    return str(value)


def format_generated_at(iso_timestamp: str) -> str:
    if not iso_timestamp:
        return ""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        month = _MONTHS_NL[dt.month - 1]
        return f"{dt.day} {month} {dt.year} om {dt.strftime('%H:%M')}"
    except (ValueError, TypeError):
        return iso_timestamp


def _table(data: list[list[str]], col_widths=None, *, numeric_col: int | None = None) -> Table:
    table = Table(data, colWidths=col_widths, hAlign="LEFT")
    style_commands: list = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F1EC")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#14213D")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D6D3CA")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    if numeric_col is not None and len(data) > 1:
        style_commands.append(("ALIGN", (numeric_col, 1), (numeric_col, -1), "RIGHT"))
        style_commands.append(("FONTNAME", (numeric_col, 1), (numeric_col, -1), "Helvetica"))
    table.setStyle(TableStyle(style_commands))
    return table


def _ordered_steps(steps: dict) -> list[tuple[str, str]]:
    ordered: list[tuple[str, str]] = []
    seen: set[str] = set()
    for key in FORFAIT_STEP_ORDER:
        if key in steps:
            ordered.append((key, steps[key]))
            seen.add(key)
    for key, val in steps.items():
        if key not in seen:
            ordered.append((key, val))
    return ordered


def build_box3_pdf(report: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    st = _styles()
    story: list = []

    year = report.get("year", "")
    story.append(Paragraph(f"Box 3-rapport {year}", st["title"]))
    story.append(
        Paragraph(
            f"Gegenereerd: {format_generated_at(report.get('generated_at', ''))}",
            st["muted"],
        )
    )
    ctx = report.get("tax_year_context") or {}
    if ctx.get("rule"):
        story.append(Paragraph(ctx["rule"], st["muted"]))
    story.append(Spacer(1, 0.4 * cm))

    forfait = report.get("forfaitair") or {}
    if forfait.get("available"):
        story.append(Paragraph("Forfaitaire berekening", st["heading"]))
        story.append(
            Paragraph(
                f"Te betalen (forfaitair): <b>{format_eur_display(forfait.get('tax_due_eur', '0'))}</b>",
                st["body"],
            )
        )
        if forfait.get("parameters_provisional"):
            story.append(
                Paragraph(
                    "Let op: percentages banktegoeden en schulden zijn nog voorlopig.",
                    st["muted"],
                )
            )

        inputs = forfait.get("box3_inputs") or {}
        story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph("Box 3-invoer (peildatum)", st["body"]))
        story.append(
            _table(
                [
                    ["Categorie", "Bedrag"],
                    ["Banktegoeden (B)", format_eur_display(inputs.get("banktegoeden_eur", "0"))],
                    [
                        "Overige bezittingen (O)",
                        format_eur_display(inputs.get("overige_bezittingen_eur", "0")),
                    ],
                    ["Schulden (S)", format_eur_display(inputs.get("schulden_eur", "0"))],
                ],
                col_widths=[9 * cm, 7 * cm],
                numeric_col=1,
            )
        )

        steps = (forfait.get("calculation") or {}).get("steps") or {}
        if steps:
            story.append(Spacer(1, 0.25 * cm))
            story.append(Paragraph("Tussenstappen", st["body"]))
            step_rows = [["Stap", "Bedrag"]]
            for key, val in _ordered_steps(steps):
                label = FORFAIT_STEP_LABELS.get(key, key.replace("_", " "))
                step_rows.append([label, format_step_display(key, val)])
            story.append(_table(step_rows, col_widths=[9 * cm, 7 * cm], numeric_col=1))

        disclaimer = forfait.get("disclaimer")
        if disclaimer:
            story.append(Spacer(1, 0.15 * cm))
            story.append(Paragraph(disclaimer, st["muted"]))

    werkelijk = report.get("werkelijk") or {}
    if werkelijk.get("available"):
        story.append(Paragraph("Werkelijk rendement", st["heading"]))
        story.append(
            Paragraph(
                f"Te betalen (werkelijk): <b>{format_eur_display(werkelijk.get('tax_due_eur', '0'))}</b>",
                st["body"],
            )
        )
        calc = werkelijk.get("calculation") or {}
        if calc:
            summary_rows = [
                ["Onderdeel", "Bedrag"],
                ["Startwaarde (1 jan)", format_eur_display(calc.get("w_start_eur", "0"))],
                ["Huidige waarde", format_eur_display(calc.get("w_end_eur", "0"))],
                ["Netto inleg", format_eur_display(calc.get("netto_inleg_eur", "0"))],
                [
                    "Werkelijk rendement",
                    f"{format_eur_display(calc.get('werkelijk_rendement_eur', '0'))} "
                    f"({format_step_display('aandeel_percent', calc.get('werkelijk_percent', '0'))})",
                ],
            ]
            story.append(_table(summary_rows, col_widths=[9 * cm, 7 * cm], numeric_col=1))

            components = calc.get("components") or {}
            if components:
                story.append(Spacer(1, 0.15 * cm))
                comp_rows = [["Onderdeel", "Bedrag"]]
                for key, val in components.items():
                    label = WERKELIJK_COMPONENT_LABELS.get(key, key.replace("_", " "))
                    comp_rows.append([label, format_eur_display(val)])
                story.append(_table(comp_rows, col_widths=[9 * cm, 7 * cm], numeric_col=1))

        if werkelijk.get("provisional_note"):
            story.append(Paragraph(werkelijk["provisional_note"], st["muted"]))

    comparison = report.get("comparison")
    if comparison:
        story.append(Paragraph("Vergelijking forfaitair vs. werkelijk", st["heading"]))
        story.append(Paragraph(comparison.get("message", ""), st["body"]))
        story.append(
            Paragraph(
                f"Forfaitair: {format_eur_display(comparison.get('forfait_tax_eur', '0'))} · "
                f"Werkelijk: {format_eur_display(comparison.get('werkelijk_tax_eur', '0'))} · "
                f"Toegepast: <b>{format_eur_display(comparison.get('applied_tax_eur', '0'))}</b>",
                st["body"],
            )
        )

    banks = report.get("bank_balances") or []
    if banks:
        story.append(Paragraph("Banktegoeden (handmatig)", st["heading"]))
        rows = [["Omschrijving", "Saldo peildatum"]]
        for b in banks:
            rows.append(
                [
                    b.get("label", ""),
                    format_eur_display(str(b.get("balance_eur", "0"))),
                ]
            )
        story.append(_table(rows, col_widths=[9 * cm, 7 * cm], numeric_col=1))

    debts = report.get("debts") or []
    if debts:
        story.append(Paragraph("Schulden (handmatig)", st["heading"]))
        rows = [["Omschrijving", "Openstaand", "Rentelast YTD"]]
        for d in debts:
            rows.append(
                [
                    d.get("label", ""),
                    format_eur_display(str(d.get("outstanding_eur", "0"))),
                    format_eur_display(str(d.get("interest_paid_ytd_eur", "0"))),
                ]
            )
        story.append(_table(rows, col_widths=[6 * cm, 5 * cm, 5 * cm], numeric_col=1))

    properties = report.get("real_estate") or []
    if properties:
        story.append(Paragraph("Vastgoed (handmatig)", st["heading"]))
        rows = [["Omschrijving", "Waarde", "Bijtelling", "Huur YTD"]]
        for p in properties:
            rows.append(
                [
                    p.get("label", ""),
                    format_eur_display(str(p.get("value_eur", "0"))),
                    format_eur_display(str(p.get("bijtelling_eur", "0"))),
                    format_eur_display(str(p.get("rental_income_ytd_eur", "0"))),
                ]
            )
        story.append(_table(rows, col_widths=[5 * cm, 4 * cm, 4 * cm, 4 * cm], numeric_col=1))

    positions_start = report.get("positions_start") or []
    if positions_start:
        story.append(Paragraph("Posities peildatum (snapshot)", st["heading"]))
        rows = [["Symbool", "Waarde", "Bron"]]
        for pos in positions_start[:40]:
            rows.append(
                [
                    pos.get("symbol", ""),
                    format_eur_display(str(pos.get("value_eur", "0"))),
                    pos.get("valuation_source", ""),
                ]
            )
        story.append(_table(rows, col_widths=[4 * cm, 6 * cm, 6 * cm], numeric_col=1))

    positions_end = report.get("positions_end") or []
    if positions_end:
        story.append(Paragraph("Posities huidig", st["heading"]))
        rows = [["Symbool", "Waarde", "Bron"]]
        for pos in positions_end[:40]:
            rows.append(
                [
                    pos.get("symbol", ""),
                    format_eur_display(str(pos.get("value_eur", "0"))),
                    pos.get("valuation_source", ""),
                ]
            )
        story.append(_table(rows, col_widths=[4 * cm, 6 * cm, 6 * cm], numeric_col=1))

    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            "Dit rapport is indicatief en vervangt geen officiële aangifte bij de Belastingdienst.",
            st["muted"],
        )
    )

    doc.build(story)
    return buffer.getvalue()

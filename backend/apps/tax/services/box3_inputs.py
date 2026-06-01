from apps.tax.services.manual_assets import manual_box3_totals, merge_box3_totals
from apps.tax.services.snapshot_inputs import extract_box3_totals_from_snapshot_data


def box3_inputs_for_user(user, year: int, snapshot_data: dict | None) -> dict[str, str]:
    portfolio = (
        extract_box3_totals_from_snapshot_data(snapshot_data)
        if snapshot_data
        else {
            "banktegoeden_eur": "0.00",
            "overige_bezittingen_eur": "0.00",
            "schulden_eur": "0.00",
        }
    )
    manual = manual_box3_totals(user, year)
    return merge_box3_totals(portfolio, manual)

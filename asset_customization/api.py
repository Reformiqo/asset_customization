import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist()
def get_asset_details(asset, date):
    """Return gross_purchase_amount and NBV as of the given date (C-04)."""
    asset_doc = frappe.get_doc("Asset", asset)
    gross = flt(asset_doc.gross_purchase_amount)

    if not asset_doc.calculate_depreciation:
        nbv = flt(asset_doc.value_after_depreciation)
    else:
        from erpnext.assets.doctype.asset.depreciation import (
            get_value_after_depreciation_on_disposal_date,
        )
        try:
            nbv = flt(get_value_after_depreciation_on_disposal_date(asset, date))
        except Exception:
            nbv = flt(asset_doc.value_after_depreciation)

    return {
        "gross_purchase_amount": gross,
        "nbv": nbv,
        "asset_name": asset_doc.asset_name,
        "asset_category": asset_doc.asset_category,
        "company": asset_doc.company,
    }

import frappe
from frappe import _


def execute(filters=None):
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": _("ARPL Document"), "fieldname": "name", "fieldtype": "Link", "options": "Asset Replacement", "width": 140},
        {"label": _("Replacement Date"), "fieldname": "replacement_date", "fieldtype": "Date", "width": 120},
        {"label": _("Composite Asset"), "fieldname": "composite_asset", "fieldtype": "Link", "options": "Asset", "width": 140},
        {"label": _("Composite Asset Name"), "fieldname": "composite_asset_name", "fieldtype": "Data", "width": 180},
        {"label": _("Old Component"), "fieldname": "old_component_asset", "fieldtype": "Link", "options": "Asset", "width": 140},
        {"label": _("Old Component Name"), "fieldname": "old_component_name", "fieldtype": "Data", "width": 160},
        {"label": _("Old NBV"), "fieldname": "old_asset_nbv", "fieldtype": "Currency", "width": 120},
        {"label": _("Old Gross Value"), "fieldname": "old_asset_gross_value", "fieldtype": "Currency", "width": 120},
        {"label": _("New Component"), "fieldname": "new_component_asset", "fieldtype": "Link", "options": "Asset", "width": 140},
        {"label": _("New Component Name"), "fieldname": "new_component_name", "fieldtype": "Data", "width": 160},
        {"label": _("New Gross Value"), "fieldname": "new_asset_gross_value", "fieldtype": "Currency", "width": 120},
        {"label": _("Reason"), "fieldname": "reason_for_replacement", "fieldtype": "Data", "width": 100},
        {"label": _("Journal Entry"), "fieldname": "journal_entry", "fieldtype": "Link", "options": "Journal Entry", "width": 140},
        {"label": _("Submitted By"), "fieldname": "owner", "fieldtype": "Link", "options": "User", "width": 160},
        {"label": _("Submitted On"), "fieldname": "creation", "fieldtype": "Datetime", "width": 160},
    ]


def get_data(filters):
    conditions = ["ar.docstatus = 1"]
    values = {}

    if filters.get("company"):
        conditions.append("a.company = %(company)s")
        values["company"] = filters["company"]
    if filters.get("composite_asset"):
        conditions.append("ar.composite_asset = %(composite_asset)s")
        values["composite_asset"] = filters["composite_asset"]
    if filters.get("from_date"):
        conditions.append("ar.replacement_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("ar.replacement_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]
    if filters.get("reason"):
        conditions.append("ar.reason_for_replacement = %(reason)s")
        values["reason"] = filters["reason"]

    return frappe.db.sql(
        """
        SELECT ar.name, ar.replacement_date, ar.composite_asset, ar.composite_asset_name,
            ar.old_component_asset, ar.old_component_name, ar.old_asset_nbv, ar.old_asset_gross_value,
            ar.new_component_asset, ar.new_component_name, ar.new_asset_gross_value,
            ar.reason_for_replacement, ar.journal_entry, ar.owner, ar.creation
        FROM `tabAsset Replacement` ar
        LEFT JOIN `tabAsset` a ON a.name = ar.composite_asset
        WHERE {conditions}
        ORDER BY ar.replacement_date DESC
        """.format(conditions=" AND ".join(conditions)),
        values, as_dict=True,
    )

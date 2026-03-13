frappe.query_reports["Asset Component Replacement History"] = {
    filters: [
        {
            fieldname: "company", label: __("Company"), fieldtype: "Link",
            options: "Company", default: frappe.defaults.get_user_default("Company"),
        },
        {
            fieldname: "composite_asset", label: __("Composite Asset"), fieldtype: "Link",
            options: "Asset", get_query: () => ({ filters: { is_composite_asset: 1 } }),
        },
        {
            fieldname: "from_date", label: __("From Date"), fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.nowdate(), -12),
        },
        {
            fieldname: "to_date", label: __("To Date"), fieldtype: "Date",
            default: frappe.datetime.nowdate(),
        },
        {
            fieldname: "reason", label: __("Reason"), fieldtype: "Select",
            options: "\nFailure\nDamage\nUpgrade\nEnd of Life\nWarranty\nOther",
        },
    ],
};

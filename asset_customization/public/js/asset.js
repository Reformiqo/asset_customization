// C-01: "Replace Component" button on submitted composite assets
frappe.ui.form.on("Asset", {
    refresh(frm) {
        if (frm.doc.is_composite_asset && frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Replace Component"), function () {
                frappe.new_doc("Asset Replacement", {
                    composite_asset: frm.doc.name,
                    composite_asset_name: frm.doc.asset_name,
                });
            }, __("Actions"));
        }
    },
});

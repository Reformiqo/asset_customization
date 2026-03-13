frappe.ui.form.on("Asset Replacement", {
    refresh(frm) {
        // C-03: Filter old component — only assets belonging to this composite
        frm.set_query("old_component_asset", () => ({
            filters: {
                custom_parent_composite_asset: frm.doc.composite_asset,
                docstatus: 1,
            },
        }));
        // C-03: Filter new component — only standalone assets (not in any composite)
        frm.set_query("new_component_asset", () => ({
            filters: {
                custom_parent_composite_asset: ["is", "not set"],
                docstatus: 1,
            },
        }));
    },

    // C-04: Auto-fetch old component values
    old_component_asset(frm) {
        if (!frm.doc.old_component_asset) {
            frm.set_value("old_asset_gross_value", 0);
            frm.set_value("old_asset_nbv", 0);
            return;
        }
        if (!frm.doc.replacement_date) {
            frappe.msgprint(__("Please set Replacement Date first."));
            return;
        }
        frappe.call({
            method: "asset_customization.api.get_asset_details",
            args: { asset: frm.doc.old_component_asset, date: frm.doc.replacement_date },
            callback(r) {
                if (r.message) {
                    frm.set_value("old_asset_gross_value", r.message.gross_purchase_amount);
                    frm.set_value("old_asset_nbv", r.message.nbv);
                }
            },
        });
    },

    // C-04: Auto-fetch new component values
    new_component_asset(frm) {
        if (!frm.doc.new_component_asset) {
            frm.set_value("new_asset_gross_value", 0);
            return;
        }
        frappe.call({
            method: "asset_customization.api.get_asset_details",
            args: { asset: frm.doc.new_component_asset, date: frm.doc.replacement_date || frappe.datetime.nowdate() },
            callback(r) {
                if (r.message) {
                    frm.set_value("new_asset_gross_value", r.message.gross_purchase_amount);
                }
            },
        });
    },

    // C-04: Recalculate NBV on date change
    replacement_date(frm) {
        if (frm.doc.old_component_asset && frm.doc.replacement_date) {
            frappe.call({
                method: "asset_customization.api.get_asset_details",
                args: { asset: frm.doc.old_component_asset, date: frm.doc.replacement_date },
                callback(r) {
                    if (r.message) {
                        frm.set_value("old_asset_gross_value", r.message.gross_purchase_amount);
                        frm.set_value("old_asset_nbv", r.message.nbv);
                    }
                },
            });
        }
    },
});

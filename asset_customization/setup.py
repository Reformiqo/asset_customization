import frappe
from frappe import _


def after_install():
    create_custom_fields()
    frappe.msgprint(_("Asset Customization installed successfully!"))


def after_migrate():
    create_custom_fields()


def create_custom_fields():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    # C-08: Custom fields on Asset DocType
    custom_fields = {
        "Asset": [
            dict(
                fieldname="custom_parent_composite_asset",
                fieldtype="Link",
                label="Parent Composite Asset",
                options="Asset",
                insert_after="is_composite_asset",
                read_only=1,
                description="Which composite asset this component belongs to.",
            ),
            dict(
                fieldname="custom_replacement_reference",
                fieldtype="Link",
                label="Replacement Reference",
                options="Asset Replacement",
                insert_after="custom_parent_composite_asset",
                read_only=1,
                description="The ARPL document that replaced this component.",
            ),
            dict(
                fieldname="custom_replacement_history_section",
                fieldtype="Section Break",
                label="Component Replacement History",
                insert_after="custom_replacement_reference",
                depends_on="eval:doc.is_composite_asset",
                collapsible=1,
            ),
            dict(
                fieldname="custom_replacement_history",
                fieldtype="Table",
                label="Replacement History",
                options="Asset Component Replacement",
                insert_after="custom_replacement_history_section",
                read_only=1,
                allow_on_submit=1,
            ),
        ],
    }
    create_custom_fields(custom_fields, update=True)

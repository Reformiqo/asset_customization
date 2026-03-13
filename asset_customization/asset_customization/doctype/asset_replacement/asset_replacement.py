import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate


class AssetReplacement(Document):
    def validate(self):
        self.run_validations()

    def before_submit(self):
        self.run_validations()

    def on_submit(self):
        self.update_old_component()
        self.update_new_component()
        self.update_composite_asset()
        self.create_journal_entry()
        self.db_set("status", "Submitted")

    # C-09: Block cancellation
    def on_cancel(self):
        frappe.throw(
            _(
                "Asset Replacement cannot be cancelled after submission. "
                "GL entries have been posted and the Composite Asset has been updated. "
                "Please contact your Finance Manager for manual correction."
            )
        )

    # ── C-05: Validations ────────────────────────────────────────────────
    def run_validations(self):
        composite = frappe.get_cached_doc("Asset", self.composite_asset)
        old_asset = frappe.get_cached_doc("Asset", self.old_component_asset)
        new_asset = frappe.get_cached_doc("Asset", self.new_component_asset)

        # V-01: Composite must be a composite asset
        if not composite.is_composite_asset:
            frappe.throw(_("Asset {0} is not a Composite Asset.").format(self.composite_asset))

        # V-02: Old component must belong to this composite
        if old_asset.get("custom_parent_composite_asset") != self.composite_asset:
            frappe.throw(
                _("Old Component {0} is not linked to Composite Asset {1}.").format(
                    self.old_component_asset, self.composite_asset
                )
            )

        # V-03: Old component must not already be unlinked
        if not old_asset.get("custom_parent_composite_asset"):
            frappe.throw(_("Old Component {0} has already been unlinked.").format(self.old_component_asset))

        # V-04: New component must not be linked to any composite
        if new_asset.get("custom_parent_composite_asset"):
            frappe.throw(
                _("New Component {0} is already linked to Composite Asset {1}.").format(
                    self.new_component_asset, new_asset.custom_parent_composite_asset
                )
            )

        # V-05: Cannot replace with itself
        if self.old_component_asset == self.new_component_asset:
            frappe.throw(_("Old and New Component cannot be the same asset."))

        # V-06: No future date
        if getdate(self.replacement_date) > getdate(nowdate()):
            frappe.throw(_("Replacement Date cannot be a future date."))

        # V-07: Replacement date >= old component purchase date
        if old_asset.purchase_date and getdate(self.replacement_date) < getdate(old_asset.purchase_date):
            frappe.throw(
                _("Replacement Date {0} is before Old Component purchase date {1}.").format(
                    self.replacement_date, old_asset.purchase_date
                )
            )

        # V-08: Role check
        user_roles = frappe.get_roles(frappe.session.user)
        if "System Manager" not in user_roles and "Accounts Manager" not in user_roles:
            frappe.throw(_("Only System Manager or Accounts Manager can submit Asset Replacement."))

    # ── C-06: Update Old Component ───────────────────────────────────────
    def update_old_component(self):
        old_asset = frappe.get_doc("Asset", self.old_component_asset)
        old_asset.db_set("custom_parent_composite_asset", None)
        old_asset.db_set("custom_replacement_reference", self.name)

        # Freeze future depreciation entries
        if old_asset.calculate_depreciation:
            depr_schedules = frappe.get_all(
                "Asset Depreciation Schedule",
                filters={"asset": old_asset.name, "docstatus": 1},
                pluck="name",
            )
            for schedule_name in depr_schedules:
                schedule = frappe.get_doc("Asset Depreciation Schedule", schedule_name)
                for entry in schedule.depreciation_schedule:
                    if (
                        getdate(entry.schedule_date) > getdate(self.replacement_date)
                        and not entry.journal_entry
                    ):
                        frappe.db.set_value(
                            "Depreciation Schedule", entry.name, "journal_entry", "SKIPPED"
                        )

    # ── C-06: Update New Component ───────────────────────────────────────
    def update_new_component(self):
        frappe.db.set_value("Asset", self.new_component_asset, "custom_parent_composite_asset", self.composite_asset)

    # ── C-06: Update Composite Asset ─────────────────────────────────────
    def update_composite_asset(self):
        composite = frappe.get_doc("Asset", self.composite_asset)

        # Append replacement history row
        composite.append("custom_replacement_history", {
            "replacement_date": self.replacement_date,
            "old_component_asset": self.old_component_asset,
            "new_component_asset": self.new_component_asset,
            "arpl_document": self.name,
            "reason": self.reason_for_replacement,
            "replaced_by": frappe.session.user,
        })
        composite.flags.ignore_validate = True
        composite.save(ignore_permissions=True)

        # Recalculate gross value
        old_gross = flt(self.old_asset_gross_value)
        new_gross = flt(self.new_asset_gross_value)
        updated_gross = flt(composite.gross_purchase_amount) - old_gross + new_gross
        frappe.db.set_value("Asset", self.composite_asset, "gross_purchase_amount", updated_gross)

        # Audit trail comment
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Asset",
            "reference_name": self.composite_asset,
            "content": _("Component replaced: {0} → {1} via {2}. Reason: {3}").format(
                self.old_component_asset, self.new_component_asset,
                self.name, self.reason_for_replacement,
            ),
        }).insert(ignore_permissions=True)

    # ── C-07: Auto Journal Entry ─────────────────────────────────────────
    def create_journal_entry(self):
        from erpnext.assets.doctype.asset.depreciation import (
            get_depreciation_accounts,
            get_disposal_account_and_cost_center,
        )

        old_asset = frappe.get_doc("Asset", self.old_component_asset)
        new_asset = frappe.get_doc("Asset", self.new_component_asset)
        company = old_asset.company

        old_fa, old_accum, _ = get_depreciation_accounts(old_asset.asset_category, company)
        new_fa, _, _ = get_depreciation_accounts(new_asset.asset_category, company)

        cwip = frappe.db.get_value(
            "Asset Category Account",
            {"parent": new_asset.asset_category, "company_name": company},
            "capital_work_in_progress_account",
        )
        if not cwip:
            cwip = frappe.get_cached_value("Company", company, "capital_work_in_progress_account")
        if not cwip:
            frappe.throw(_("Set Capital Work in Progress Account in Asset Category {0} or Company {1}").format(
                new_asset.asset_category, company
            ))

        disposal_account, cost_center = get_disposal_account_and_cost_center(company)

        old_gross = flt(self.old_asset_gross_value)
        old_nbv = flt(self.old_asset_nbv)
        accum_depr = old_gross - old_nbv
        new_gross = flt(self.new_asset_gross_value)

        je = frappe.new_doc("Journal Entry")
        je.voucher_type = "Journal Entry"
        je.posting_date = self.replacement_date
        je.company = company
        je.user_remark = _("Component Replacement: {0}").format(self.name)

        # Row 1: Dr Accumulated Depreciation, Cr Fixed Asset (remove old)
        if accum_depr > 0:
            je.append("accounts", {
                "account": old_accum, "debit_in_account_currency": accum_depr,
                "cost_center": cost_center, "reference_type": "Asset",
                "reference_name": self.old_component_asset,
            })
        je.append("accounts", {
            "account": old_fa, "credit_in_account_currency": old_gross,
            "cost_center": cost_center, "reference_type": "Asset",
            "reference_name": self.old_component_asset,
        })

        # Row 2: Dr Loss on Disposal (write off NBV) — skip if NBV = 0
        if old_nbv > 0:
            je.append("accounts", {
                "account": disposal_account, "debit_in_account_currency": old_nbv,
                "cost_center": cost_center, "reference_type": "Asset",
                "reference_name": self.old_component_asset,
            })

        # Row 3: Dr Fixed Asset (new), Cr CWIP (new)
        je.append("accounts", {
            "account": new_fa, "debit_in_account_currency": new_gross,
            "cost_center": cost_center, "reference_type": "Asset",
            "reference_name": self.new_component_asset,
        })
        je.append("accounts", {
            "account": cwip, "credit_in_account_currency": new_gross,
            "cost_center": cost_center, "reference_type": "Asset",
            "reference_name": self.new_component_asset,
        })

        je.flags.ignore_permissions = True
        je.insert()
        je.submit()
        self.db_set("journal_entry", je.name)
        frappe.msgprint(_("Journal Entry {0} created.").format(
            frappe.utils.get_link_to_form("Journal Entry", je.name)
        ))

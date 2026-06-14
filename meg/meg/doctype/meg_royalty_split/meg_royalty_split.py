import frappe
from frappe.model.document import Document
from frappe.utils import today, flt


class MEGRoyaltySplit(Document):

    def validate(self):
        self._validate_splits_total()

    def _validate_splits_total(self):
        total_pct = sum(flt(row.percentage) for row in self.splits)
        if self.splits and abs(total_pct - 100) > 0.01:
            frappe.throw(f"Split percentages must total 100%. Currently: {total_pct}%")

    def process(self):
        if self.status != "Pending":
            frappe.throw("Only Pending royalty splits can be processed.")

        je = frappe.get_doc({
            "doctype": "Journal Entry",
            "posting_date": today(),
            "accounts": self._build_je_lines(),
            "user_remark": f"Royalty split: {self.title}",
        })
        je.insert(ignore_permissions=True)
        je.submit()

        self.journal_entry = je.name
        self.status = "Processed"
        self.posted_date = today()
        self.save(ignore_permissions=True)

        return je.name

    def _build_je_lines(self):
        lines = []
        # Debit the revenue account
        lines.append({
            "account": frappe.db.get_single_value("MEG Settings", "default_revenue_account"),
            "debit_in_account_currency": flt(self.total_amount),
            "credit_in_account_currency": 0,
        })
        # Credit each recipient
        for row in self.splits:
            amount = flt(self.total_amount) * flt(row.percentage) / 100
            lines.append({
                "account": row.payable_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": amount,
                "party_type": "Supplier" if row.party_type == "Supplier" else None,
                "party": row.party if row.party else None,
            })
        return lines


def process_pending_royalties():
    """Called daily by scheduler."""
    pending = frappe.get_all(
        "MEG Royalty Split",
        filters={"status": "Pending"},
        fields=["name"],
    )
    for row in pending:
        doc = frappe.get_doc("MEG Royalty Split", row.name)
        try:
            doc.process()
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"MEG Royalty Split failed: {doc.name}")

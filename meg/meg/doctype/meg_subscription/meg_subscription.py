import frappe
from frappe.model.document import Document
from frappe.utils import add_months, add_days, today, getdate, nowdate
from dateutil.relativedelta import relativedelta


class MEGSubscription(Document):

    def before_save(self):
        if not self.next_billing_date and self.start_date:
            self.next_billing_date = self._next_date(self.start_date)

    def _next_date(self, from_date):
        cycle_map = {"Monthly": 1, "Quarterly": 3, "Yearly": 12}
        months = cycle_map.get(self.billing_cycle, 1)
        return str(getdate(from_date) + relativedelta(months=months))

    def create_invoice(self):
        invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": self.customer,
            "currency": self.currency,
            "posting_date": today(),
            "due_date": today(),
            "meg_subscription": self.name,
            "items": [{
                "item_name": self.plan_name,
                "description": f"{self.plan_name} — {self.billing_cycle} subscription",
                "qty": 1,
                "rate": self.amount,
                "uom": "Nos",
            }],
        })
        invoice.insert(ignore_permissions=True)
        invoice.submit()

        self.next_billing_date = self._next_date(self.next_billing_date or today())
        self.save(ignore_permissions=True)

        return invoice.name


def process_due_subscriptions():
    """Called daily by scheduler."""
    due = frappe.get_all(
        "MEG Subscription",
        filters={
            "status": "Active",
            "next_billing_date": ("<=", today()),
            "auto_renew": 1,
        },
        fields=["name"],
    )
    for row in due:
        doc = frappe.get_doc("MEG Subscription", row.name)
        try:
            invoice_name = doc.create_invoice()
            frappe.logger().info(f"MEG Subscription {doc.name}: created invoice {invoice_name}")
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"MEG Subscription renewal failed: {doc.name}")


def on_invoice_submit(doc, method):
    """Tag subscription invoices on submit."""
    pass

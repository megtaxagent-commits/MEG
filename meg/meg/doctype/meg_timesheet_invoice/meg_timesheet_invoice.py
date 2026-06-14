import frappe
from frappe.utils import today, flt


def create_invoice_from_timesheet(doc, method):
    """
    Auto-creates a Sales Invoice when a Timesheet is submitted,
    if the timesheet has a customer and hourly rate set.
    """
    if not doc.customer or not doc.time_logs:
        return

    total_hours = sum(flt(log.hours) for log in doc.time_logs)
    if total_hours <= 0:
        return

    hourly_rate = flt(doc.get("meg_hourly_rate") or 0)
    if hourly_rate <= 0:
        return

    invoice = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": doc.customer,
        "posting_date": today(),
        "meg_timesheet": doc.name,
        "items": _build_invoice_items(doc, hourly_rate),
    })
    invoice.insert(ignore_permissions=True)
    invoice.submit()

    frappe.msgprint(f"Invoice {invoice.name} created from Timesheet {doc.name}", alert=True)


def _build_invoice_items(timesheet, hourly_rate):
    items = []
    for log in timesheet.time_logs:
        if not log.hours:
            continue
        items.append({
            "item_name": log.activity_type or "Consulting",
            "description": log.description or log.activity_type,
            "qty": flt(log.hours),
            "rate": hourly_rate,
            "uom": "Hour",
        })
    return items

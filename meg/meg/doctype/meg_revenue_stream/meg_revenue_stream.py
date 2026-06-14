import frappe
from frappe.model.document import Document
from frappe.utils import today, getdate, get_first_day, get_last_day


class MEGRevenueStream(Document):
    pass


def generate_monthly_summary():
    """Called monthly. Creates a summary journal note per active stream."""
    streams = frappe.get_all(
        "MEG Revenue Stream",
        filters={"is_active": 1},
        fields=["name", "stream_name", "income_account", "cost_center"],
    )
    for stream in streams:
        _log_stream_summary(stream)


def _log_stream_summary(stream):
    month_start = get_first_day(today())
    month_end = get_last_day(today())

    invoices = frappe.db.sql("""
        SELECT SUM(si.base_grand_total) as total
        FROM `tabSales Invoice` si
        WHERE si.meg_revenue_stream = %s
          AND si.docstatus = 1
          AND si.posting_date BETWEEN %s AND %s
    """, (stream["name"], month_start, month_end), as_dict=True)

    total = invoices[0].total or 0
    frappe.logger().info(
        f"MEG Revenue Stream {stream['stream_name']}: {total} for {month_start} to {month_end}"
    )

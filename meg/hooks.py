app_name = "meg"
app_title = "MEG"
app_publisher = "MEG"
app_description = "ERP for SMEs and Creators"
app_email = "admin@meg.com"
app_license = "MIT"
app_version = "0.0.1"

required_apps = ["erpnext"]

doc_events = {
    "Sales Invoice": {
        "on_submit": "meg.doctype.meg_subscription.meg_subscription.on_invoice_submit",
    },
    "Timesheet": {
        "on_submit": "meg.doctype.meg_timesheet_invoice.meg_timesheet_invoice.create_invoice_from_timesheet",
    },
}

scheduler_events = {
    "daily": [
        "meg.doctype.meg_subscription.meg_subscription.process_due_subscriptions",
        "meg.doctype.meg_royalty_split.meg_royalty_split.process_pending_royalties",
    ],
    "monthly": [
        "meg.doctype.meg_revenue_stream.meg_revenue_stream.generate_monthly_summary",
    ],
}

fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "MEG"]]},
]

after_install = "meg.setup.after_install"

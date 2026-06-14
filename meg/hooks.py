app_name = "meg"
app_title = "MEG"
app_publisher = "MEG"
app_description = "ERP for SMEs and Creators"
app_email = "admin@meg.com"
app_license = "MIT"
app_version = "0.0.1"

# Required apps
required_apps = ["erpnext"]

# DocType overrides
override_doctype_class = {}

# Document events
doc_events = {
    "Sales Invoice": {
        "on_submit": "meg.meg.doctype.meg_subscription.meg_subscription.on_invoice_submit",
    },
    "Timesheet": {
        "on_submit": "meg.meg.doctype.meg_timesheet_invoice.meg_timesheet_invoice.create_invoice_from_timesheet",
    },
}

# Scheduled tasks
scheduler_events = {
    "daily": [
        "meg.meg.doctype.meg_subscription.meg_subscription.process_due_subscriptions",
        "meg.meg.doctype.meg_royalty_split.meg_royalty_split.process_pending_royalties",
    ],
    "monthly": [
        "meg.meg.doctype.meg_revenue_stream.meg_revenue_stream.generate_monthly_summary",
    ],
}

# Website
website_route_rules = []

# Fixtures (export these doctypes with bench export-fixtures)
fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "MEG"]]},
    {"dt": "Property Setter", "filters": [["module", "=", "MEG"]]},
]

# Permissions
permission_query_conditions = {}

# After install
after_install = "meg.setup.after_install"

import frappe


def after_install():
    create_meg_roles()
    create_default_revenue_categories()


def create_meg_roles():
    roles = ["MEG Creator", "MEG Accountant", "MEG Manager"]
    for role in roles:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role}).insert()


def create_default_revenue_categories():
    categories = [
        "Freelance Income",
        "Subscription Revenue",
        "Royalty Income",
        "Digital Product Sales",
        "Passive Income",
        "Salary",
    ]
    for cat in categories:
        if not frappe.db.exists("MEG Revenue Category", cat):
            frappe.get_doc({
                "doctype": "MEG Revenue Category",
                "category_name": cat,
            }).insert()

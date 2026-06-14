import frappe
import json
import hmac
import hashlib
from frappe.utils import today


@frappe.whitelist(allow_guest=True)
def handle():
    """
    Endpoint: /api/method/meg.meg.api.stripe_webhook.handle
    Register this URL in your Stripe dashboard as a webhook.
    """
    payload = frappe.request.data
    sig_header = frappe.request.headers.get("Stripe-Signature", "")

    stream = _get_stripe_stream()
    if not stream:
        frappe.throw("No active Stripe revenue stream configured.", frappe.PermissionError)

    secret = stream.get_password("webhook_secret")
    if not _verify_signature(payload, sig_header, secret):
        frappe.throw("Invalid Stripe signature.", frappe.PermissionError)

    event = json.loads(payload)
    _dispatch(event, stream)

    return {"status": "ok"}


def _verify_signature(payload, sig_header, secret):
    try:
        parts = dict(p.split("=", 1) for p in sig_header.split(","))
        ts = parts.get("t", "")
        v1 = parts.get("v1", "")
        signed = f"{ts}.{payload.decode('utf-8')}"
        expected = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, v1)
    except Exception:
        return False


def _get_stripe_stream():
    name = frappe.db.get_value(
        "MEG Revenue Stream",
        {"source_platform": "Stripe", "is_active": 1},
        "name",
    )
    return frappe.get_doc("MEG Revenue Stream", name) if name else None


def _dispatch(event, stream):
    etype = event.get("type")

    if etype == "invoice.payment_succeeded":
        _create_invoice_from_stripe(event["data"]["object"], stream)
    elif etype == "customer.subscription.deleted":
        _cancel_subscription(event["data"]["object"])
    else:
        frappe.logger().info(f"MEG Stripe webhook: unhandled event type {etype}")


def _create_invoice_from_stripe(stripe_invoice, stream):
    customer_email = stripe_invoice.get("customer_email")
    amount = stripe_invoice.get("amount_paid", 0) / 100  # Stripe uses cents
    currency = stripe_invoice.get("currency", "usd").upper()
    gateway_sub_id = stripe_invoice.get("subscription")

    customer = _get_or_create_customer(customer_email)

    invoice = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": customer,
        "currency": currency,
        "posting_date": today(),
        "meg_revenue_stream": stream.name,
        "items": [{
            "item_name": "Stripe Payment",
            "description": f"Stripe Invoice {stripe_invoice.get('id')}",
            "qty": 1,
            "rate": amount,
            "uom": "Nos",
        }],
    })
    invoice.insert(ignore_permissions=True)
    invoice.submit()


def _cancel_subscription(stripe_sub):
    sub_id = stripe_sub.get("id")
    name = frappe.db.get_value("MEG Subscription", {"gateway_subscription_id": sub_id}, "name")
    if name:
        doc = frappe.get_doc("MEG Subscription", name)
        doc.status = "Cancelled"
        doc.save(ignore_permissions=True)


def _get_or_create_customer(email):
    existing = frappe.db.get_value("Customer", {"email_id": email}, "name")
    if existing:
        return existing
    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": email,
        "email_id": email,
        "customer_type": "Individual",
        "customer_group": "Individual",
        "territory": "All Territories",
    })
    customer.insert(ignore_permissions=True)
    return customer.name

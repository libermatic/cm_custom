# -*- coding: utf-8 -*-
import frappe
from toolz.curried import merge, keyfilter
from firebase_admin import auth

from cm_custom.api.firebase import get_decoded_token, app
from cm_custom.api.utils import handle_error, transform_route


@frappe.whitelist(allow_guest=True)
@handle_error
def get(token):
    decoded_token = get_decoded_token(token)
    customer_id = frappe.db.exists(
        "Customer", {"cm_firebase_uid": decoded_token["uid"]}
    )
    if not customer_id:
        return None
    doc = frappe.get_doc("Customer", customer_id)
    orders = frappe.db.exists("Sales Order", {"customer": customer_id})
    return merge(
        keyfilter(lambda x: x in ["name", "customer_name"], doc.as_dict()),
        {"can_register_messaging": bool(orders)},
    )


@frappe.whitelist(allow_guest=True)
@handle_error
def create(token, **kwargs):
    decoded_token = get_decoded_token(token)
    session_user = frappe.session.user
    webapp_user = frappe.get_cached_value(
        "Ahong eCommerce Settings", None, "webapp_user"
    )
    if not webapp_user:
        frappe.throw(frappe._("Site setup not complete"))

    frappe.set_user(webapp_user)
    uid = decoded_token["uid"]
    customer_id = frappe.db.exists("Customer", {"cm_firebase_uid": uid})
    if customer_id:
        frappe.throw(frappe._("Customer already created"))

    args = keyfilter(
        lambda x: x
        in [
            "customer_name",
            "mobile_no",
            "email",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "country",
            "pincode",
        ],
        kwargs,
    )

    print(args)
    doc = frappe.get_doc(
        merge(
            {
                "doctype": "Customer",
                "cm_firebase_uid": uid,
                "cm_mobile_no": args.get("mobile_no"),
                "customer_type": "Individual",
                "customer_group": frappe.db.get_single_value(
                    "Selling Settings", "customer_group"
                ),
                "territory": frappe.db.get_single_value(
                    "Selling Settings", "territory"
                ),
            },
            args,
        )
    ).insert()
    auth.set_custom_user_claims(uid, {"customer": True}, app=app)

    frappe.set_user(session_user)
    return keyfilter(lambda x: x in ["name", "customer_name"], doc.as_dict())

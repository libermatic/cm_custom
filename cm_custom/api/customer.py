# -*- coding: utf-8 -*-
import frappe
from toolz.curried import compose, merge, keyfilter
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


@frappe.whitelist(allow_guest=True)
@handle_error
def list_addresses(token, page="1", page_length="10"):
    decoded_token = get_decoded_token(token)
    customer_id = frappe.db.exists(
        "Customer", {"cm_firebase_uid": decoded_token["uid"]}
    )
    if not customer_id:
        frappe.throw(frappe._("Customer does not exist on backend"))

    get_count = compose(
        lambda x: x[0][0],
        lambda x: frappe.db.sql(
            """
                SELECT COUNT(name) FROM `tabDynamic Link` WHERE
                    parenttype = 'Address' AND
                    link_doctype = 'Customer' AND
                    link_name = %(link_name)s
            """,
            values={"link_name": x},
        ),
    )
    addresses = frappe.db.sql(
        """
            SELECT
                a.name AS name,
                a.address_line1 AS address_line1,
                a.address_line2 AS address_line2,
                a.city AS city,
                a.state AS state,
                a.country AS country,
                a.pincode AS pincode
            FROM `tabDynamic Link` AS dl
            LEFT JOIN `tabAddress` AS a ON a.name = dl.parent
            WHERE dl.parenttype = 'Address' AND
                dl.link_doctype = 'Customer' AND
                dl.link_name = %(link_name)s
            GROUP BY a.name
            ORDER BY a.modified DESC
            LIMIT %(start)s, %(page_length)s
        """,
        values={
            "link_name": customer_id,
            "start": (frappe.utils.cint(page) - 1) * frappe.utils.cint(page_length),
            "page_length": frappe.utils.cint(page_length),
        },
        as_dict=1,
    )

    count = get_count(customer_id)
    return {
        "count": count,
        "pages": frappe.utils.ceil(count / frappe.utils.cint(page_length)),
        "items": addresses,
    }

# -*- coding: utf-8 -*-
import frappe
from toolz.curried import compose, merge, keyfilter
from firebase_admin import auth

from cm_custom.api.firebase import get_decoded_token, app
from cm_custom.api.utils import handle_error, transform_route

CUSTOMER_FIELDS = ["name", "customer_name", "mobile_no", "email_id"]


def get_customer_id(token):
    decoded_token = get_decoded_token(token)
    customer_id = frappe.db.exists(
        "Customer", {"cm_firebase_uid": decoded_token["uid"]}
    )
    if not customer_id:
        frappe.throw(frappe._("Customer does not exist on backend"))
    return customer_id


@frappe.whitelist(allow_guest=True)
@handle_error
def get(token):
    try:
        customer_id = get_customer_id(token)
    except:
        return None
    doc = frappe.get_doc("Customer", customer_id)
    orders = frappe.db.exists("Sales Order", {"customer": customer_id})
    return merge(
        keyfilter(lambda x: x in CUSTOMER_FIELDS, doc.as_dict()),
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

    uid = decoded_token["uid"]
    customer_id = frappe.db.exists("Customer", {"cm_firebase_uid": uid})
    if customer_id:
        frappe.throw(frappe._("Customer already created"))

    args = keyfilter(
        lambda x: x
        in [
            "customer_name",
            "mobile_no",
            "email_id",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "country",
            "pincode",
        ],
        kwargs,
    )

    def insert_or_update():
        existing = frappe.db.exists("Customer", {"cm_mobile_no": args.get("mobile_no")})
        if existing:
            doc = frappe.get_doc("Customer", existing)
            doc.update(
                {"customer_name": args.get("customer_name"), "cm_firebase_uid": uid}
            )
            if args.get("address_line1") and args.get("city"):
                address = _create_address(existing, args)
                doc.update({"customer_primary_address": address.get("name")})
            print([args.get("email_id"), doc.customer_primary_contact])
            if args.get("email_id") and doc.customer_primary_contact:
                contact = frappe.get_doc("Contact", doc.customer_primary_contact)
                contact.add_email(args.get("email_id"), autosave=True)
            doc.save(ignore_permissions=True)
            return doc

        frappe.set_user(webapp_user)
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
        ).insert(ignore_permissions=True)
        frappe.set_user(session_user)
        return doc

    doc = insert_or_update()
    auth.set_custom_user_claims(uid, {"customer": True}, app=app)
    return keyfilter(lambda x: x in CUSTOMER_FIELDS, doc.as_dict())


@frappe.whitelist(allow_guest=True)
@handle_error
def update(token, **kwargs):
    customer_id = get_customer_id(token)

    args = keyfilter(lambda x: x in ["customer_name"], kwargs)
    doc = frappe.get_doc("Customer", customer_id)
    doc.update(args)
    doc.save(ignore_permissions=True)
    return keyfilter(lambda x: x in CUSTOMER_FIELDS, doc.as_dict())


@frappe.whitelist(allow_guest=True)
@handle_error
def list_addresses(token, page="1", page_length="10"):
    customer_id = get_customer_id(token)

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


@frappe.whitelist(allow_guest=True)
@handle_error
def get_address(token, name):
    customer_id = get_customer_id(token)
    if not frappe.db.exists(
        "Dynamic Link",
        {"parent": name, "link_doctype": "Customer", "link_name": customer_id},
    ):
        frappe.throw(frappe._("Address not found"))

    return frappe.get_cached_value(
        "Address",
        name,
        fieldname=[
            "name",
            "address_line1",
            "address_line1",
            "city",
            "state",
            "country",
            "pincode",
        ],
        as_dict=1,
    )


@frappe.whitelist(allow_guest=True)
@handle_error
def create_address(token, **kwargs):
    customer_id = get_customer_id(token)
    return _create_address(customer_id, kwargs)


def _create_address(customer, args):
    fields = ["address_line1", "address_line2", "city", "state", "country", "pincode"]
    _args = keyfilter(lambda x: x in fields, args)
    doc = frappe.get_doc(
        merge({"doctype": "Address", "address_type": "Billing"}, _args)
    )
    doc.append("links", {"link_doctype": "Customer", "link_name": customer})
    doc.insert(ignore_permissions=True)
    return keyfilter(lambda x: x in ["name"] + fields, doc.as_dict())


@frappe.whitelist(allow_guest=True)
@handle_error
def delete_address(token, name):
    customer_id = get_customer_id(token)
    if not frappe.db.exists(
        "Dynamic Link",
        {"parent": name, "link_doctype": "Customer", "link_name": customer_id},
    ):
        frappe.throw(frappe._("Address not found"))

    frappe.delete_doc("Address", name, ignore_permissions=True)
    return None

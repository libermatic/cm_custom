# -*- coding: utf-8 -*-
from erpnext.accounts.doctype.tax_rule.tax_rule import get_tax_template
import frappe
import json
from toolz import keyfilter, merge, compose, groupby

from cm_custom.api.utils import handle_error
from cm_custom.api.customer import get_customer_id


@frappe.whitelist(allow_guest=True)
@handle_error
def make(token, **kwargs):
    customer_id = get_customer_id(token)

    session_user = frappe.session.user
    webapp_user = frappe.get_cached_value(
        "Ahong eCommerce Settings", None, "webapp_user"
    )
    if not webapp_user:
        frappe.throw(frappe._("Site setup not complete"))
    frappe.set_user(webapp_user)

    doc = _make_sales_order(customer_id, **kwargs)
    doc.run_method("calculate_taxes_and_totals")
    doc.run_method("set_taxes")

    frappe.set_user(session_user)
    return _get_formatted_sales_order(doc)


@frappe.whitelist(allow_guest=True)
@handle_error
def create(token, **kwargs):
    customer_id = get_customer_id(token)

    session_user = frappe.session.user
    webapp_user = frappe.get_cached_value(
        "Ahong eCommerce Settings", None, "webapp_user"
    )
    if not webapp_user:
        frappe.throw(frappe._("Site setup not complete"))
    frappe.set_user(webapp_user)

    doc = _make_sales_order(customer_id, **kwargs)
    doc.insert()
    doc.submit()

    frappe.set_user(session_user)
    return _get_formatted_sales_order(doc)


def _make_sales_order(customer_id, **kwargs):
    settings = frappe.get_single("Ahong eCommerce Settings")
    args = keyfilter(lambda x: x in ["transaction_date", "customer_address"], kwargs)
    location = (
        frappe.get_cached_value("Address", args.get("customer_address"), "location")
        if args.get("customer_address")
        else None
    )
    delivery_charges = (
        frappe.get_cached_value("Location", location, "delivery_charges_template")
        if location
        else None
    )

    doc = frappe.get_doc(
        merge(
            {
                "doctype": "Sales Order",
                "status": "Draft",
                "docstatus": 0,
                "__islocal": 1,
                "customer": customer_id,
                "order_type": "Shopping Cart",
                "company": settings.company
                or frappe.defaults.get_user_default("company"),
                "delivery_date": args.get("transaction_date"),
                "shipping_address_name": args.get("customer_address"),
                "currency": frappe.defaults.get_user_default("currency"),
                "selling_price_list": frappe.get_cached_value(
                    "Selling Settings", None, "selling_price_list"
                ),
                "taxes_and_charges": delivery_charges,
            },
            args,
        )
    )

    print(kwargs)
    print(doc.taxes_and_charges)

    for item_args in json.loads(kwargs.get("items", "[]")):
        doc.append(
            "items",
            merge(
                keyfilter(lambda x: x in ["item_code", "qty", "rate"], item_args),
                {
                    "delivery_date": args.get("transaction_date"),
                    "warehouse": settings.warehouse
                    or frappe.get_cached_value(
                        "Stock Settings", None, "default_warehouse"
                    ),
                    "uom": frappe.get_cached_value(
                        "Item", item_args.get("item_code"), "stock_uom"
                    ),
                },
            ),
        )

    doc.flags.ignore_permissions = True
    doc.run_method("set_missing_values")
    doc.run_method("calculate_taxes_and_totals")
    doc.run_method("set_taxes")
    return doc


@frappe.whitelist(allow_guest=True)
@handle_error
def get_list(token, page="1", page_length="10"):
    customer_id = get_customer_id(token)

    session_user = frappe.session.user
    webapp_user = frappe.get_cached_value(
        "Ahong eCommerce Settings", None, "webapp_user"
    )
    if not webapp_user:
        frappe.throw(frappe._("Site setup not complete"))
    frappe.set_user(webapp_user)

    get_count = compose(
        lambda x: x[0][0],
        lambda x: frappe.get_all(
            "Sales Order",
            fields=["count(name)"],
            filters={"customer": x},
            as_list=1,
        ),
    )

    orders = frappe.db.get_list(
        "Sales Order",
        fields="*",
        filters={
            "customer": customer_id,
            "docstatus": (">", 0),
        },
        limit_start=(frappe.utils.cint(page) - 1) * frappe.utils.cint(page_length),
        limit_page_length=frappe.utils.cint(page_length),
        order_by="modified desc",
    )
    order_ids = [x.get("name") for x in orders]
    order_items_by_order = (
        groupby(
            "parent",
            frappe.get_all(
                "Sales Order Item",
                fields="*",
                filters={
                    "parent": ("in", order_ids),
                },
            ),
        )
        if order_ids
        else {}
    )
    order_taxes_by_order = (
        groupby(
            "parent",
            frappe.get_all(
                "Sales Taxes and Charges",
                fields="*",
                filters={
                    "parent": ("in", order_ids),
                },
            ),
        )
        if order_ids
        else {}
    )

    count = get_count(customer_id)
    items = [
        _get_formatted_sales_order(
            merge(
                x,
                {
                    "items": order_items_by_order.get(x.get("name")) or [],
                    "taxes": order_taxes_by_order.get(x.get("name")) or [],
                },
            ),
            is_dict=True,
        )
        for x in orders
    ]

    print(orders)
    frappe.set_user(session_user)
    return {
        "count": count,
        "pages": frappe.utils.ceil(count / frappe.utils.cint(page_length)),
        "items": items,
    }


def _get_formatted_sales_order(doc, is_dict=False):
    _doc = doc if is_dict else doc.as_dict()

    return merge(
        keyfilter(
            lambda x: x
            in [
                "name",
                "transaction_date",
                "delivery_date",
                "total",
                "total_taxes_and_charges",
                "grand_total",
                "rounding_adjustment",
                "rounded_total",
                "status",
                "delivery_status",
            ],
            _doc,
        ),
        {
            "items": [
                keyfilter(
                    lambda x: x
                    in [
                        "name",
                        "item_code",
                        "item_name",
                        "item_group",
                        "image",
                        "qty",
                        "price_list_rate",
                        "rate",
                        "amount",
                        "net_amount",
                    ],
                    x,
                )
                for x in _doc.get("items")
            ],
            "taxes": [
                keyfilter(
                    lambda x: x
                    in ["name", "description", "tax_amount", "included_in_print_rate"],
                    x,
                )
                for x in _doc.get("taxes")
            ],
        },
    )

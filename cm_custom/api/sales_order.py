# -*- coding: utf-8 -*-
import frappe
import json
from toolz import keyfilter, merge

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
    doc.calculate_taxes_and_totals()

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
    args = keyfilter(lambda x: x in ["transaction_date", "customer_address"], kwargs)

    doc = frappe.get_doc(
        merge(
            {
                "doctype": "Sales Order",
                "customer": customer_id,
                "order_type": "Shopping Cart",
                "company": frappe.defaults.get_user_default("company"),
                "currency": frappe.defaults.get_user_default("currency"),
                "selling_price_list": frappe.get_cached_value(
                    "Selling Settings", None, "selling_price_list"
                ),
            },
            args,
        )
    )

    warehouse = frappe.get_cached_value("Stock Settings", None, "default_warehouse")
    for item_args in json.loads(kwargs.get("items", "[]")):
        doc.append(
            "items",
            merge(
                keyfilter(lambda x: x in ["item_code", "qty", "rate"], item_args),
                {
                    "warehouse": warehouse,
                    "uom": frappe.get_cached_value(
                        "Item", item_args.get("item_code"), "stock_uom"
                    ),
                },
            ),
        )

    doc.set_missing_values()
    return doc


def _get_formatted_sales_order(doc):
    return merge(
        keyfilter(
            lambda x: x
            in [
                "name",
                "transaction_date",
                "delivery_date",
                "total",
                "grand_total",
                "rounding_adjustment",
                "rounded_total",
            ],
            doc.as_dict(),
        ),
        {
            "items": [
                keyfilter(
                    lambda x: x
                    in [
                        "item_code",
                        "item_name",
                        "item_group",
                        "qty",
                        "price_list_rate",
                        "rate",
                        "amount",
                        "net_amount",
                    ],
                    x.as_dict(),
                )
                for x in doc.items
            ],
            "taxes": [
                keyfilter(lambda x: x in ["description", "tax_amount"], x.as_dict())
                for x in doc.taxes
            ],
        },
    )

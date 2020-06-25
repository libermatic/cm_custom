# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe


def after_migrate():
    print("Setting up defaults...")
    setup_defaults()


def setup_defaults():
    _update_settings()
    _set_naming_series()


def settings():
    return {
        "Buying Settings": {"supp_master_name": "Naming Series"},
        "Selling Settings": {
            "cust_master_name": "Naming Series",
            "customer_group": "Individual",
        },
        "Stock Settings": {"item_naming_by": "Naming Series"},
        "Accounts Settings": {"allow_cost_center_in_entry_of_bs_account": 1},
    }


def naming_series():
    return {
        "Item": "IT.YY.",
        "Customer": "CU.YY.",
        "Supplier": "SU.YY.",
        "Sales Order": "SO.YY.",
        "Delivery Note": "DN.YY.",
        "Sales Invoice": "SI.YY.",
        "Purchase Order": "PO.YY.",
        "Purchase Receipt": "PR.YY.",
        "Purchase Invoice": "PI.YY.",
        "Payment Entry": "PE.YY.",
        "Journal Entry": "JV.YY.",
    }


def _update_settings():
    def update(doctype, params):
        doc = frappe.get_single(doctype)
        doc.update(params)
        doc.save(ignore_permissions=True)

    for args in settings().items():
        update(*args)


def _set_naming_series():
    from frappe.custom.doctype.property_setter.property_setter import (
        make_property_setter,
    )

    def update(doctype, series):
        field = frappe.model.meta.get_meta(doctype).get_field("naming_series")
        if series not in field.options:
            options = series + "\n" + (field.options or "")
            make_property_setter(
                doctype, "naming_series", "options", options, "Text",
            )
        if series != field.default:
            make_property_setter(
                doctype, "naming_series", "default", series, "Text",
            )

    for args in naming_series().items():
        update(*args)

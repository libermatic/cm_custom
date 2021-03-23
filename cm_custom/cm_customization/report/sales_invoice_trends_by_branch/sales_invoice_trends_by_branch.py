# Copyright (c) 2013, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from toolz.curried import groupby, valmap
from toolz.functoolz import compose

from cm_custom.cm_customization.report.trends import get_columns, get_data


def execute(filters=None):
    if not filters:
        filters = {}
    conditions = get_columns(filters, "Sales Invoice")
    data = get_data(filters, conditions)
    return _extend_columns(conditions["columns"], filters), _extend_data(data, filters)


def _extend_columns(columns, filters):
    if filters.get("based_on") != "Item":
        return columns
    print(columns)
    print(filters)
    return columns[:2] + ["Default Supplier:Link/Supplier:120"] + columns[2:]


def _extend_data(data, filters):
    if filters.get("based_on") != "Item":
        return data

    get_suppliers = compose(
        valmap(lambda vals: min(vals, key=lambda x: x.get("idx")).get("supplier")),
        groupby("parent"),
        frappe.get_all,
    )
    suppliers_by_item = get_suppliers(
        "Item Supplier",
        filters={"parent": ("in", [x[0] for x in data])},
        fields=["parent", "idx", "supplier"],
    )

    def add_supplier(row):
        return row[:2] + [suppliers_by_item.get(row[0]) or ""] + row[2:]

    return [add_supplier(x) for x in data]

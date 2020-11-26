# Copyright (c) 2013, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from toolz.curried import concatv, compose


def execute(filters=None):
    columns = _get_columns(filters)
    clauses, values = _get_filters(filters)
    keys = [x.get("fieldname") for x in columns]
    return _get_columns(filters), _get_data(clauses, values, keys)


def _get_columns(filters):
    return [
        {
            "label": "Item Code",
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 120,
        },
        {
            "label": "Item Name",
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "Balance",
            "fieldname": "balance",
            "fieldtype": "Float",
            "width": 90,
        },
        {
            "label": "Supplier",
            "fieldname": "supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 120,
        },
        {
            "label": "Supplier Name",
            "fieldname": "supplier_name",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "Warehouse",
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 120,
        },
    ]


def _get_filters(filters):
    join = compose(lambda x: " AND ".join(x), concatv)
    clauses = join(
        ["True"],
        ["`tabItem`.item_group = %(item_group)s"] if filters.get("item_group") else [],
        ["`tabBin`.warehouse = %(warehouse)s"] if filters.get("warehouse") else [],
        ["`tabItem Supplier`.supplier = %(supplier)s"]
        if filters.get("supplier")
        else [],
    )
    return clauses, filters


def _get_data(clauses, values, keys):
    rows = frappe.db.sql(
        """
            SELECT
                `tabItem`.name AS item_code,
                `tabItem`.item_name,
                `tabBin`.actual_qty AS balance,
                `tabItem Supplier`.supplier,
                `tabSupplier`.supplier_name,
                `tabBin`.warehouse
            FROM `tabItem`
            LEFT JOIN `tabItem Supplier` ON
                `tabItem Supplier`.parent = `tabItem`.name
            LEFT JOIN `tabSupplier` ON
                `tabSupplier`.name = `tabItem Supplier`.supplier
            LEFT JOIN `tabBin` ON
                `tabBin`.item_code = `tabItem`.name
            WHERE {clauses}
        """.format(
            clauses=clauses
        ),
        values=values,
    )
    return rows

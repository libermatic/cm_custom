# Copyright (c) 2013, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from toolz.curried import compose, reduceby, filter, map

from erpnext.stock.report.batch_wise_balance_history.batch_wise_balance_history import (
    execute as batch_wise_balance_history,
)


def execute(filters=None):
    columns, data = batch_wise_balance_history(filters)
    batch_idx = next(x for x, v in enumerate(columns) if v.startswith("Batch"))
    balance_idx = next(x for x, v in enumerate(columns) if v.startswith("Balance Qty"))
    return (
        _extend_columns(columns, batch_idx),
        _extend_data(filters, data, batch_idx, balance_idx),
    )


def _extend_columns(columns, batch_idx):
    idx = batch_idx + 1
    return (
        columns[:idx]
        + ["Expiry Date:Date:100", "Expiry(in Days):Int:60"]
        + columns[idx:]
    )


def _extend_data(filters, data, batch_idx, balance_idx):
    get_batches = compose(
        reduceby("name", lambda x: x[0]),
        lambda batches: frappe.db.sql(
            """
                SELECT
                    name,
                    expiry_date,
                    IF(expiry_date, DATEDIFF(expiry_date, %(today)s), '')  AS expiry_in_days
                FROM `tabBatch` WHERE name IN %(batches)s
            """,
            values={"today": frappe.utils.today(), "batches": batches},
            as_dict=1,
        )
        if batches
        else [],
        set,
        filter(lambda x: x),
        map(lambda x: x[batch_idx]),
    )
    batches = get_batches(data)
    idx = batch_idx + 1

    def get_cells(row):
        batch = batches.get(row[batch_idx])
        if batch:
            return [batch.get("expiry_date"), batch.get("expiry_in_days")]
        return [None, None]

    def will_show(row):
        if not filters.hide_zero_stock:
            return True
        return row[balance_idx] != 0

    return [(x[:idx] + get_cells(x) + x[idx:]) for x in data if will_show(x)]

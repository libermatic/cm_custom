# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe


def set_missing_values(doc, method, for_validate=False):
    doc.branch = frappe.get_cached_value("POS Profile", doc.pos_profile, "branch")


def validate(doc, method):
    if doc.is_return and doc.paid_amount:
        paid_invoice = frappe.get_cached_value(
            "Sales Invoice", doc.return_against, "paid_amount"
        )
        paid_returns = _get_paid_amount_from_returns(doc.return_against)
        paid_payments = _get_paid_amount_from_payment_entries(doc.return_against)
        paid_amount = paid_invoice + paid_returns + paid_payments
        if -doc.paid_amount > paid_amount:
            frappe.throw(
                frappe._(
                    """
                    <p>Paid amount cannot be greater than <strong>{}</strong>.</p>
                    <p>
                        If you want to proceed, create the return invoice without
                        payment and then make payment from the original invoice.
                    </p>
                    """.format(
                        frappe.utils.fmt_money(paid_amount, currency=doc.currency)
                    )
                )
            )


def before_save(doc, method):
    if not doc.is_pos:
        doc.payments = []
        if doc.is_return:
            doc.outstanding_amount = 0


def _get_paid_amount_from_returns(si):
    return (
        frappe.get_all(
            "Sales Invoice",
            fields=["sum(paid_amount) as paid_amount"],
            filters={"docstatus": 1, "is_return": 1, "return_against": si,},
        )[0].get("paid_amount")
        or 0
    )


def _get_paid_amount_from_payment_entries(si):
    payments = frappe.db.sql(
        """
            SELECT
                SUM(per.allocated_amount) AS paid_amount,
                pe.payment_type
            FROM `tabPayment Entry Reference` AS per
            LEFT JOIN `tabPayment Entry` AS pe ON
                pe.name = per.parent
            WHERE
                pe.docstatus = 1 AND
                per.reference_doctype = 'Sales Invoice' AND
                per.reference_name = %(reference_name)s
            GROUP BY pe.payment_type
        """,
        values={"reference_name": si},
    )

    return sum([x[0] * 1 if x[1] == "Receive" else -1 for x in payments])


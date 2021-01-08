# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe


def set_missing_values(doc, method, for_validate=False):
    doc.branch = frappe.get_cached_value("POS Profile", doc.pos_profile, "branch")




def before_save(doc, method):
    if not doc.is_pos:
        doc.payments = []
        if doc.is_return:
            doc.outstanding_amount = 0

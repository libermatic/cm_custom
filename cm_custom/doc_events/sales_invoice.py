# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe


def set_missing_values(doc, method, for_validate=False):
    doc.branch = frappe.get_cached_value("POS Profile", doc.pos_profile, "branch")


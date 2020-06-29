# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe


def before_save(doc, method):
    doc.cm_branch = frappe.get_cached_value("POS Profile", doc.pos_profile, "branch")


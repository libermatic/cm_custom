# -*- coding: utf-8 -*-
from __future__ import unicode_literals

def before_save(doc, method):
    doc.branch = frappe.get_cached_value(
        "POS Profile", self.pos_profile, "branch"
    )
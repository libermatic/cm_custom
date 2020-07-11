# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe


def before_insert(doc, method):
    if not doc.mobile_no:
        doc.mobile_no = doc.cm_mobile_no

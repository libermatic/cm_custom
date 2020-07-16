# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
import json
from six import string_types
from toolz.curried import dissoc


@frappe.whitelist()
def get_item_details(args, doc=None, for_validate=False, overwrite_warehouse=True):
    from erpnext.stock.get_item_details import get_item_details

    _args = json.loads(args) if isinstance(args, string_types) else args
    return get_item_details(
        dissoc(_args, "item_tax_template"), doc, for_validate, overwrite_warehouse
    )

# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
import json
from six import string_types
from toolz.curried import dissoc, merge


@frappe.whitelist()
def get_item_details(args, doc=None, for_validate=False, overwrite_warehouse=True):
    from erpnext.stock.get_item_details import get_item_details

    _args = json.loads(args) if isinstance(args, string_types) else args
    return get_item_details(
        dissoc(_args, "item_tax_template"), doc, for_validate, overwrite_warehouse
    )


@frappe.whitelist()
def apply_price_list(args, as_doc=False):
    from erpnext.stock.get_item_details import apply_price_list

    def proc_args(args):
        if args.get("is_return"):
            return merge(
                args,
                {
                    "items": [
                        merge(x, {"qty": -x.get("qty", 0)})
                        for x in args.get("items", [])
                    ]
                },
            )
        return args

    _args = json.loads(args) if isinstance(args, string_types) else args
    return apply_price_list(proc_args(_args), as_doc)

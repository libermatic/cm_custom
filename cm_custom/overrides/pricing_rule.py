# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
import json
from six import string_types
from toolz.curried import merge


@frappe.whitelist()
def apply_pricing_rule(args, doc=None):
    from erpnext.accounts.doctype.pricing_rule.pricing_rule import apply_pricing_rule

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
    return apply_pricing_rule(proc_args(_args), doc)

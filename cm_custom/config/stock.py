# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _


def get_data():
    return [
        {
            "label": _("Stock Reports"),
            "items": [
                {
                    "type": "report",
                    "is_query_report": True,
                    "name": "Stock Balance with Supplier",
                    "doctype": "Bin",
                },
            ],
        },
        {
            "label": _("Key Reports"),
            "items": [
                {
                    "type": "report",
                    "is_query_report": True,
                    "name": "Batch-Wise Balance History with Expiry",
                    "doctype": "Batch",
                },
            ],
        },
    ]

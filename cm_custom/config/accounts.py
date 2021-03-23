# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _


def get_data():
    return [
        {
            "label": _("Profitability"),
            "items": [
                {
                    "type": "report",
                    "is_query_report": True,
                    "name": "Sales Invoice Trends by Branch",
                    "doctype": "Sales Invoice",
                },
            ],
        },
    ]

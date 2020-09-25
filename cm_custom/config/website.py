# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _


def get_data():
    return [
        {
            "label": _("Setup"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Ahong eCommerce Settings",
                    "label": _("Ahong eCommerce Settings"),
                    "settings": 1,
                },
            ],
        },
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from posx.doc_events.purchase_receipt import set_or_create_batch


def before_validate(doc, method):
    if (
        doc.stock_entry_type in ["Material Receipt", "Repack"]
        and doc._action == "submit"
    ):
        for item in doc.items:
            if item.t_warehouse:
                item.px_mfg_date = item.cm_mfg_date
                item.px_exp_date = item.cm_exp_date
                item.px_batch_price_list_rate = item.cm_batch_price_list_rate
            else:
                item.cm_mfg_date = None
                item.cm_exp_date = None
                item.cm_batch_price_list_rate = None
        set_or_create_batch(doc, method)

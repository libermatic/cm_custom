# -*- coding: utf-8 -*-
import frappe
from toolz.curried import merge
import html

from cm_custom.api.utils import handle_error, transform_route

ITEM_GROUP_FIELDS = [
    "name",
    "is_group",
    "route",
    "parent_item_group",
    "description",
    "image",
]


@frappe.whitelist(allow_guest=True)
@handle_error
def get_all():
    groups = frappe.get_all(
        "Item Group",
        filters={"show_in_website": 1},
        fields=ITEM_GROUP_FIELDS,
        order_by="lft, rgt",
    )
    return [merge(x, {"route": transform_route(x)}) for x in groups]


@frappe.whitelist(allow_guest=True)
@handle_error
def get(name=None, route=None):
    _name = _get_name(name, route)
    if not _name:
        return None

    group = frappe.get_cached_value("Item Group", _name, ITEM_GROUP_FIELDS, as_dict=1)
    return merge(group, {"route": transform_route(group)})


def _get_name(name=None, route=None):
    if name:
        return html.unescape(name)
    if route:
        return frappe.db.exists(
            "Item Group", {"route": (route or "").replace("__", "/")}
        )
    return None

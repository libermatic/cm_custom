# -*- coding: utf-8 -*-
import frappe
from toolz.curried import merge
import html
from erpnext.accounts.doctype.sales_invoice.pos import get_child_nodes

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
def get_all(list_type="all"):
    filters = {"show_in_website": 1}
    if list_type == "home":
        home_item_groups = [
            x
            for (x,) in frappe.get_all(
                "Website Item Group",
                fields=["item_group"],
                filters={
                    "parent": "Ahong eCommerce Settings",
                    "parentfield": "home_item_groups",
                },
                as_list=1,
            )
        ]
        if home_item_groups:
            filters.update({"name": ("in", home_item_groups)})
    elif list_type == "section":
        return _get_section_groups()

    groups = frappe.get_all(
        "Item Group",
        filters=filters,
        fields=ITEM_GROUP_FIELDS,
        order_by="lft, rgt",
    )
    return [merge(x, {"route": transform_route(x)}) for x in groups]


def _get_section_groups():
    section_item_groups = [
        {
            "category": x,
            "groups": [
                child
                for child in get_child_nodes("Item Group", x)
                if child.get("name") != x
            ],
        }
        for (x,) in frappe.get_all(
            "Website Item Group",
            fields=["item_group"],
            filters={
                "parent": "Ahong eCommerce Settings",
                "parentfield": "section_item_groups",
            },
            as_list=1,
            order_by="idx asc",
        )
    ]

    group_ids = [x.get("category") for x in section_item_groups] + [
        y
        for x in section_item_groups
        for y in [group.get("name") for group in x.get("groups")]
    ]

    groups_by_id = (
        {
            x.get("name"): {**x, "route": transform_route(x)}
            for x in frappe.get_all(
                "Item Group",
                filters={"name": ("in", group_ids), "show_in_website": 1},
                fields=ITEM_GROUP_FIELDS,
                order_by="lft, rgt",
            )
        }
        if group_ids
        else {}
    )

    result = [
        {
            "category": groups_by_id.get(x.get("category")),
            "groups": [
                groups_by_id.get(y.get("name"))
                for y in x.get("groups")
                if groups_by_id.get(y.get("name"))
            ],
        }
        for x in section_item_groups
    ]

    return [x for x in result if x.get("groups")]


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

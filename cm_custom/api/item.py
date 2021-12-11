# -*- coding: utf-8 -*-
import frappe
from erpnext.utilities.product import get_price

@frappe.whitelist()
def list_item_price_list_rates(item_codes):
    _item_codes = frappe.parse_json(item_codes)
    if not _item_codes:
        return []

    return frappe.db.get_list(
        "Item Price",
        fields=["item_code", "price_list_rate"],
        filters={
            "item_code": ("in", _item_codes),
            "selling": 1,
            "price_list": frappe.db.get_single_value("Shopping Cart Settings", "price_list"),
            "ifnull(valid_from, '2000-01-01')": ("<", frappe.utils.today()),
            "ifnull(valid_upto, '2100-01-01')": (">", frappe.utils.today()),
        },
        order_by="valid_from desc",
    )


@frappe.whitelist()
def list_item_rates(item_codes):
    _item_codes = frappe.parse_json(item_codes)
    if not _item_codes:
        return []

    price_list = frappe.db.get_single_value("Shopping Cart Settings", "price_list")
    customer_group = frappe.db.get_single_value("Selling Settings", "customer_group")
    company = frappe.db.get_single_value("Shopping Cart Settings", "company")

    def get_rate(item_code):
        price = (
            get_price(
                item_code,
                price_list,
                customer_group=customer_group,
                company=company,
            ) or {}
        )
        return price.get("price_list_rate")

    return [{"item_code": item_code, "rate": get_rate(item_code)} for item_code in _item_codes]


@frappe.whitelist()
def list_item_stock_qtys(item_codes):
    _item_codes = frappe.parse_json(item_codes)
    if not _item_codes:
        return []

    tree = frappe.db.get_value(
        "Warehouse",
        frappe.db.get_single_value("Ahong eCommerce Settings", "warehouse"),
        fieldname=["lft", "rgt"],
    )

    if not tree:
        return []

    warehouses = [
        x for (x,) in frappe.get_all(
            "Warehouse",
            filters={
                "lft": (">=", tree[0]),
                "rgt": ("<=", tree[1]),
            },
            as_list=1,
        )
    ]
    if not warehouses:
        return []

    return frappe.db.sql(
        """
            SELECT
                b.item_code AS item_code,
                GREATEST(
                    SUM(
                        b.actual_qty - b.reserved_qty - b.reserved_qty_for_production - b.reserved_qty_for_sub_contract
                    ),
                    0
                ) / IFNULL(C.conversion_factor, 1) AS stock_qty
            FROM `tabBin` AS b
            INNER JOIN `tabItem` AS i
                ON b.item_code = i.item_code
            LEFT JOIN `tabUOM Conversion Detail` C
                ON i.sales_uom = C.uom AND C.parent = i.item_code
            WHERE b.item_code IN %(item_codes)s AND b.warehouse in %(warehouses)s
            GROUP BY b.item_code
        """,
        values={
            "item_codes": _item_codes,
            "warehouses": warehouses,
        },
        as_dict=1,
    )


@frappe.whitelist()
def stock(limit_start=0, limit_page_length=20, item_group=None, search=None, show_zero=0):
    clauses = ["1"]
    values = {
        "limit_start": frappe.utils.cint(limit_start),
        "limit_page_length": frappe.utils.cint(limit_page_length),
    }
    warehouse = frappe.db.get_value("Server Script", "list_bin", "script")

    if warehouse:
        tree = frappe.db.get_value(
            "Warehouse",
            warehouse,
            fieldname=["lft", "rgt"],
        )
        warehouses = [
            x for (x,) in frappe.get_all(
                "Warehouse",
                filters={
                    "lft": (">=", tree[0]),
                    "rgt": ("<=", tree[1]),
                },
                as_list=1,
            )
        ]
        if warehouses:
            clauses.append("`tabBin`.warehouse IN %(warehouses)s")
            values.update({"warehouses": warehouses})
   
    if item_group:
        tree = frappe.db.get_value(
            "Item Group",
            item_group,
            fieldname=["lft", "rgt"],
        )
        if tree:
            item_groups = [
                x for (x,) in frappe.get_all(
                    "Item Group",
                    filters={
                        "lft": (">=", tree[0]),
                        "rgt": ("<=", tree[1]),
                    },
                    as_list=1,
                )
            ]
            if item_groups:
                clauses.append("`tabItem`.item_group IN %(item_groups)s")
                values.update({"item_groups": item_groups})
        else:
            clauses.append("`tabItem`.item_group = '_no_item_group'")


    if search:
        or_clauses = [
            "`tabItem`.name LIKE %(search)s",
            "`tabItem`.item_name LIKE %(search)s",
            "`tabItem`.description LIKE %(search)s",
        ]
        clauses.append(f"({' OR '.join(or_clauses)})")
        values.update({"search": f"%{search}%"})

    if not frappe.parse_json(show_zero):
        clauses.append("`tabBin`.actual_qty > 0")

    return frappe.db.sql(
        """
            SELECT
                `tabItem`.name,
                `tabItem`.item_name,
                `tabItem`.item_group,
                SUM(`tabBin`.reserved_qty) AS reserved_qty,
                SUM(`tabBin`.actual_qty) AS actual_qty,
                SUM(`tabBin`.ordered_qty) AS ordered_qty,
                SUM(`tabBin`.indented_qty) AS indented_qty,
                SUM(`tabBin`.planned_qty) AS planned_qty,
                SUM(`tabBin`.projected_qty) AS projected_qty
            FROM `tabBin`
            LEFT JOIN `tabItem`
                ON `tabItem`.name = `tabBin`.item_code
            WHERE {clauses}
            GROUP BY `tabBin`.item_code
            ORDER BY `tabItem`.item_name
            LIMIT %(limit_page_length)s OFFSET %(limit_start)s
        """.format(clauses=" AND ".join(clauses)),
        values=values,
        as_dict=1,
    )

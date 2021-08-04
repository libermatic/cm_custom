# -*- coding: utf-8 -*-
import frappe
from toolz.curried import (
    compose,
    merge,
    unique,
    concat,
    valmap,
    groupby,
    first,
    excepts,
    keyfilter,
    map,
    filter,
)
import html
from erpnext.portal.product_configurator.utils import (
    get_products_for_website,
    get_product_settings,
    get_item_codes_by_attributes,
    get_conditions,
)
from erpnext.shopping_cart.product_info import get_product_info_for_website
from erpnext.accounts.doctype.sales_invoice.pos import get_child_nodes
from erpnext.utilities.product import get_price, get_qty_in_stock

from cm_custom.api.utils import handle_error, transform_route


@frappe.whitelist(allow_guest=True)
@handle_error
def get_list(page="1", field_filters=None, attribute_filters=None, search=None):
    other_fieldnames = ["item_group", "thumbnail", "has_variants"]
    price_list = frappe.db.get_single_value("Shopping Cart Settings", "price_list")
    products_settings = get_product_settings()
    products_per_page = products_settings.products_per_page

    get_other_fields = compose(
        valmap(excepts(StopIteration, first, lambda _: {})),
        groupby("name"),
        lambda item_codes: frappe.db.sql(
            """
                SELECT name, {other_fieldnames}
                FROM `tabItem`
                WHERE name IN %(item_codes)s
            """.format(
                other_fieldnames=", ".join(other_fieldnames)
            ),
            values={"item_codes": item_codes},
            as_dict=1,
        ),
        lambda items: [x.get("name") for x in items],
    )

    frappe.form_dict.start = (frappe.utils.cint(page) - 1) * products_per_page
    kwargs = _get_args(field_filters, attribute_filters, search)
    items = get_products_for_website(**kwargs)
    other_fields = get_other_fields(items) if items else {}
    item_prices = _get_item_prices(price_list, items) if items else {}
    get_rates = _rate_getter(price_list, item_prices)
    stock_qtys_by_item = _get_stock_by_item(items) if items else {}

    return [
        merge(
            x,
            get_rates(x.get("name")),
            {k: other_fields.get(x.get("name"), {}).get(k) for k in other_fieldnames},
            {
                "route": transform_route(x),
                "description": frappe.utils.strip_html_tags(x.get("description") or ""),
                "stock_qty": stock_qtys_by_item.get(x.get("name"), 0),
            },
        )
        for x in items
    ]


@frappe.whitelist(allow_guest=True)
@handle_error
def get_count(field_filters=None, attribute_filters=None, search=None):
    products_settings = get_product_settings()
    products_per_page = products_settings.products_per_page

    def get_pages(count):
        return frappe.utils.ceil(count / products_per_page)

    kwargs = _get_args(field_filters, attribute_filters, search)

    def get_field_filters():
        if not field_filters:
            return []

        meta = frappe.get_meta("Item")

        def get_filter(fieldname, values):
            df = meta.get_field(fieldname)
            if df.fieldtype == "Table MultiSelect":
                child_meta = frappe.get_meta(df.options)
                fields = child_meta.get(
                    "fields", {"fieldtype": "Link", "in_list_view": 1}
                )
                if fields:
                    return [df.options, fields[0].fieldname, "in", values]
            return ["Item", fieldname, "in", values]

        return [get_filter(k, v) for k, v in kwargs.get("field_filters").items() if v]

    def get_attribute_conditions():
        if not attribute_filters:
            return None
        return get_conditions(
            [
                [
                    "Item",
                    "name",
                    "in",
                    get_item_codes_by_attributes(kwargs.get("attribute_filters")),
                ]
            ]
        )

    def get_default_conditions():
        return get_conditions([["Item", "disabled", "=", 0]])

    def get_variant_conditions():
        if products_settings.hide_variants:
            return get_conditions([["Item", "show_in_website", "=", 1]])
        return get_conditions(
            [
                ["Item", "show_in_website", "=", 1],
                ["Item", "show_variant_in_website", "=", 1],
            ],
            "or",
        )

    def get_search_conditions():
        if not search:
            return None
        meta = frappe.get_meta("Item")
        search_fields = set(
            meta.get_search_fields(),
            ["name", "item_name", "description", "item_group"],
        )
        return get_conditions(
            [["Item", field, "like", "%(search)s"] for field in search_fields], "or"
        )

    _field_filters = get_field_filters()
    conditions = " and ".join(
        [
            c
            for c in [
                get_attribute_conditions(),
                get_conditions(_field_filters, "and"),
                get_default_conditions(),
                get_variant_conditions(),
                get_search_conditions(),
            ]
            if c
        ]
    )
    left_joins = " ".join(
        [
            "LEFT JOIN `tab{0}` ON `tab{}`.parent = `tabItem`.name".format(f[0])
            for f in _field_filters
            if f[0] != "Item"
        ]
    )

    count = frappe.db.sql(
        """
            SELECT COUNT(`tabItem`.name) FROM `tabItem` {left_joins}
            WHERE {conditions}
        """.format(
            left_joins=left_joins, conditions=conditions
        )
    )[0][0]

    return {"count": count, "pages": get_pages(count)}


@frappe.whitelist(allow_guest=True)
@handle_error
def get(name=None, route=None):
    item_code = _get_name(name, route)
    if not item_code:
        frappe.throw(frappe._("Item does not exist at this route"))

    doc = frappe.get_cached_value(
        "Item",
        item_code,
        fieldname=[
            "name",
            "item_name",
            "item_group",
            "has_variants",
            "description",
            "web_long_description",
            "image",
            "website_image",
        ],
        as_dict=1,
    )

    price_list = frappe.get_cached_value("Shopping Cart Settings", None, "price_list")
    item_prices = _get_item_prices(price_list, [doc])
    get_rate = _rate_getter(price_list, item_prices)

    return merge({"route": route}, doc, get_rate(doc.get("name")))


@frappe.whitelist(allow_guest=True)
@handle_error
def get_product_info(name=None, item_code=None, route=None, token=None):
    # todo: first set user from token
    frappe.set_user(
        frappe.get_cached_value("Ahong eCommerce Settings", None, "webapp_user")
    )

    item_code = item_code or _get_name(name, route)

    if not item_code:
        frappe.throw(frappe._("Item does not exist at this route"))

    item_for_website = get_product_info_for_website(
        item_code, skip_quotation_creation=True
    )
    stock_status = _get_stock_qty(item_code)

    return {
        "price": keyfilter(
            lambda x: x in ["currency", "price_list_rate"],
            item_for_website.get("product_info", {}).get("price", {}),
        ),
        "stock_qty": stock_status.get("stock_qty"),
    }


@frappe.whitelist(allow_guest=True)
@handle_error
def get_media(name=None, route=None):
    item_code = _get_name(name, route)

    def get_values(name):
        return frappe.get_cached_value(
            "Item",
            name,
            ["thumbnail", "image", "website_image", "slideshow"],
            as_dict=1,
        )

    def get_slideshows(slideshow):
        if not slideshow:
            return None
        doc = frappe.get_cached_doc("Website Slideshow", slideshow)
        if not doc:
            return None
        return [x.get("image") for x in doc.slideshow_items if x.get("image")]

    variant_of = frappe.get_cached_value("Item", item_code, "variant_of")
    images = get_values(item_code)
    template_images = get_values(variant_of) if variant_of else {}

    def get_image(field):
        return images.get(field) or template_images.get(field)

    return {
        "thumbnail": get_image("thumbnail"),
        "image": get_image("image"),
        "website_image": get_image("website_image"),
        "slideshow": get_slideshows(get_image("slideshow")),
    }


@frappe.whitelist(allow_guest=True)
@handle_error
def get_related_items(name=None, route=None):
    item_code = _get_name(name, route)
    if not item_code:
        frappe.throw(frappe._("Item does not exist at this route"))

    item_group = frappe.get_cached_value("Item", item_code, "item_group")
    result = get_list(field_filters={"item_group": [item_group]})
    return [x for x in result if x.get("name") != item_code]


def _get_name(name=None, route=None):
    if name:
        return html.unescape(name)
    if route:
        return frappe.db.exists("Item", {"route": (route or "").replace("__", "/")})
    return None


_get_item_prices = compose(
    valmap(excepts(StopIteration, first, lambda _: {})),
    groupby("item_code"),
    lambda price_list, items: frappe.db.sql(
        """
            SELECT item_code, price_list_rate
            FROM `tabItem Price`
            WHERE price_list = %(price_list)s AND item_code IN %(item_codes)s
        """,
        values={"price_list": price_list, "item_codes": [x.get("name") for x in items]},
        as_dict=1,
    )
    if price_list
    else {},
)


def _rate_getter(price_list, item_prices):
    def fn(item_code):
        price_obj = (
            get_price(
                item_code,
                price_list,
                customer_group=frappe.get_cached_value(
                    "Selling Settings", None, "customer_group"
                ),
                company=frappe.defaults.get_global_default("company"),
            )
            or {}
        )
        price_list_rate = item_prices.get(item_code, {}).get("price_list_rate")
        item_price = price_obj.get("price_list_rate") or price_list_rate
        return {
            "price_list_rate": item_price,
            "slashed_rate": price_list_rate if price_list_rate != item_price else None,
        }

    return fn


def _get_args(field_filters=None, attribute_filters=None, search=None):
    get_item_groups = compose(
        list,
        unique,
        map(lambda x: x.get("name")),
        concat,
        map(lambda x: get_child_nodes("Item Group", x) if x else []),
    )
    field_dict = (
        frappe.parse_json(field_filters)
        if isinstance(field_filters, str)
        else field_filters
    ) or {}
    item_groups = (
        get_item_groups(field_dict.get("item_group"))
        if field_dict.get("item_group")
        else None
    )
    return {
        "field_filters": merge(
            field_dict, {"item_group": item_groups} if item_groups else {}
        ),
        "attribute_filters": frappe.parse_json(attribute_filters),
        "search": search,
    }


@frappe.whitelist(allow_guest=True)
@handle_error
def get_recent_items():
    price_list = frappe.db.get_single_value("Shopping Cart Settings", "price_list")
    products_per_page = frappe.db.get_single_value(
        "Products Settings", "products_per_page"
    )
    items = frappe.db.sql(
        """
            SELECT
                name, item_name, item_group, route, has_variants,
                thumbnail, image, website_image,
                description, web_long_description
            FROM `tabItem`
            WHERE show_in_website = 1
            ORDER BY modified DESC
            LIMIT %(products_per_page)s
        """,
        values={"products_per_page": products_per_page},
        as_dict=1,
    )
    item_prices = _get_item_prices(price_list, items) if items else {}
    get_rates = _rate_getter(price_list, item_prices)
    stock_qtys_by_item = _get_stock_by_item(items) if items else {}

    return [
        merge(
            x,
            get_rates(x.get("name")),
            {
                "route": transform_route(x),
                "description": frappe.utils.strip_html_tags(x.get("description") or ""),
                "stock_qty": stock_qtys_by_item.get(x.get("name"), 0),
            },
        )
        for x in items
    ]


@frappe.whitelist(allow_guest=True)
@handle_error
def get_featured_items():
    homepage = frappe.get_single("Homepage")

    if not homepage.products:
        return []

    price_list = frappe.db.get_single_value("Shopping Cart Settings", "price_list")
    items = frappe.db.sql(
        """
            SELECT
                name, item_name, item_group, route, has_variants,
                thumbnail, image, website_image,
                description, web_long_description
            FROM `tabItem`
            WHERE show_in_website = 1 AND name IN %(featured)s
            ORDER BY modified DESC
        """,
        values={"featured": [x.item_code for x in homepage.products]},
        as_dict=1,
    )
    item_prices = _get_item_prices(price_list, items) if items else {}
    get_rates = _rate_getter(price_list, item_prices)
    stock_qtys_by_item = _get_stock_by_item(items) if items else {}

    return [
        merge(
            x,
            get_rates(x.get("name")),
            {
                "route": transform_route(x),
                "description": frappe.utils.strip_html_tags(x.get("description") or ""),
                "stock_qty": stock_qtys_by_item.get(x.get("name"), 0),
            },
        )
        for x in items
    ]


def _get_stock_qty(name):
    stock_status = get_qty_in_stock(
        name,
        "website_warehouse",
        frappe.db.get_single_value("Ahong eCommerce Settings", "warehouse"),
    )

    return {
        "in_stock": stock_status.in_stock,
        "stock_qty": stock_status.stock_qty[0][0] if stock_status.stock_qty else 0,
        "is_stock_item": stock_status.is_stock_item,
    }


def _get_stock_by_item(items):
    warehouse = frappe.db.get_single_value("Ahong eCommerce Settings", "warehouse")
    return {
        x["item_code"]: x["stock_qty"]
        for x in frappe.db.sql(
            """
                SELECT b.item_code,
                    GREATEST(
                        b.actual_qty - b.reserved_qty - b.reserved_qty_for_production - b.reserved_qty_for_sub_contract,
                        0
                    ) / IFNULL(C.conversion_factor, 1) AS stock_qty
                FROM `tabBin` AS b
                INNER JOIN `tabItem` AS i
                    ON b.item_code = i.item_code
                LEFT JOIN `tabUOM Conversion Detail` C
                    ON i.sales_uom = C.uom AND C.parent = i.item_code
                WHERE b.item_code IN %(item_codes)s AND b.warehouse=%(warehouse)s
            """,
            values={
                "item_codes": [x.get("name") for x in items],
                "warehouse": warehouse,
            },
            as_dict=1,
        )
    }

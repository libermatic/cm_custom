# -*- coding: utf-8 -*-
import frappe
from frappe.website.doctype.website_settings.website_settings import (
    get_website_settings,
)
from toolz.curried import merge, keyfilter

from cm_custom.api.utils import handle_error, transform_route


@frappe.whitelist(allow_guest=True)
@handle_error
def get_slideshow():
    homepage = frappe.get_single("Homepage")
    if homepage.hero_section_based_on != "Slideshow" or not homepage.slideshow:
        return None

    def get_route(item):
        ref_doctype, ref_name = item.get("cm_ref_doctype"), item.get("cm_ref_docname")
        if ref_doctype and ref_name:
            route, show_in__website = frappe.get_cached_value(
                ref_doctype, ref_name, ["route", "show_in_website"]
            )
            if route and show_in__website:
                return transform_route({"route": route})
        return None

    return [
        merge(
            keyfilter(lambda y: y in ["image", "heading", "description"], x),
            {"route": get_route(x), "kind": x.get("cm_ref_doctype")},
        )
        for x in frappe.get_all(
            "Website Slideshow Item",
            filters={"parent": homepage.slideshow},
            fields=[
                "image",
                "heading",
                "description",
                "cm_ref_doctype",
                "cm_ref_docname",
            ],
        )
    ]


@frappe.whitelist(allow_guest=True)
@handle_error
def get_settings():
    ahong_settings = frappe.get_single("Ahong eCommerce Settings")
    website_settings = get_website_settings()

    return merge(
        keyfilter(lambda x: x in ["copyright", "footer_address"], website_settings),
        {
            "privacy": bool(ahong_settings.privacy),
            "terms": bool(ahong_settings.terms),
            "show_about_us": bool(ahong_settings.show_about_us),
            "hide_build_info": bool(ahong_settings.hide_build_info),
        },
    )

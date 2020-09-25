# -*- coding: utf-8 -*-
import frappe
import firebase_admin
from firebase_admin import auth, messaging

cred = firebase_admin.credentials.Certificate(
    "{}/../firebase-admin-sdk.json".format(frappe.get_app_path("cm_custom"))
)

app = firebase_admin.initialize_app(cred, name="cm_custom")


def get_decoded_token(token):
    decoded = auth.verify_id_token(token, app=app)
    if not decoded.get("uid"):
        frappe.throw(frappe._("Invalid token"))
    return decoded

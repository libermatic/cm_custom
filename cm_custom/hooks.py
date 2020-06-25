# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__

app_name = "cm_custom"
app_version = __version__
app_title = "CM Customization"
app_publisher = "Libermatic"
app_description = "Customizations for CM"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@libermatic.com"
app_license = "MIT"

fixtures = [
    {
        "doctype": "Property Setter",
        "filters": {"name": ("in", ["Customer-customer_type-default"])},
    }
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/cm_custom/css/cm_custom.css"
# app_include_js = "/assets/cm_custom/js/cm_custom.js"

# include js, css files in header of web template
# web_include_css = "/assets/cm_custom/css/cm_custom.css"
# web_include_js = "/assets/cm_custom/js/cm_custom.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "cm_custom.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "cm_custom.install.before_install"
# after_install = "cm_custom.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "cm_custom.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"cm_custom.tasks.all"
# 	],
# 	"daily": [
# 		"cm_custom.tasks.daily"
# 	],
# 	"hourly": [
# 		"cm_custom.tasks.hourly"
# 	],
# 	"weekly": [
# 		"cm_custom.tasks.weekly"
# 	]
# 	"monthly": [
# 		"cm_custom.tasks.monthly"
# 	]
# }

after_migrate = ["cm_custom.install.after_migrate"]

# Testing
# -------

# before_tests = "cm_custom.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "cm_custom.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "cm_custom.task.get_dashboard_data"
# }


// Copyright (c) 2020, Libermatic and contributors
// For license information, please see license.txt

frappe.ui.form.on('Ahong eCommerce Settings', {
  setup(frm) {
    frm.set_query('item_group', 'home_item_groups', {
      filters: { show_in_website: 1 },
    });
  },
});

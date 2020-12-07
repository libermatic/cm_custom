export function stock_entry_detail() {
  return {
    form_render: set_batch_field_props,
  };
}

function set_batch_field_props(frm, cdt, cdn) {
  if (['Material Receipt', 'Repack'].includes(frm.doc.stock_entry_type)) {
    const { t_warehouse } = frappe.get_doc(cdt, cdn) || {};
    const fields = ['cm_mfg_date', 'cm_exp_date', 'cm_batch_price_list_rate'];
    const grid_row = frm.fields_dict.items.grid.grid_rows_by_docname[cdn];
    fields.forEach((field) => {
      const fieldIdx = grid_row.docfields.findIndex(
        (x) => x.fieldname === field
      );
      if (fieldIdx > 0) {
        grid_row.docfields[fieldIdx].hidden = t_warehouse ? 0 : 1;
      }
    });
    grid_row.refresh();
  }
}

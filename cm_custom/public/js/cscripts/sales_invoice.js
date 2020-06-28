export default function sales_invoice() {
  return {
    is_pos: async function (frm) {
      const { is_pos, company } = frm.doc;
      if (is_pos && company && !frm.doc.pos_profile) {
        const { message: { branch } = {} } = await frappe.call({
          method: 'erpnext.stock.get_item_details.get_pos_profile',
          args: { company },
        });
        frm.set_value({ branch });
      }
    },
    pos_profile: async function (frm) {
      const { pos_profile } = frm.doc;
      if (pos_profile) {
        const { message: { branch } = {} } = await frappe.db.get_value(
          'POS Profile',
          pos_profile,
          'branch'
        );
        frm.set_value({ branch });
      }
    },
  };
}

async function set_branch(frm) {
  const { pos_profile } = frm.doc;
  if (pos_profile) {
    const { message: { branch } = {} } = await frappe.db.get_value(
      'POS Profile',
      pos_profile,
      'branch'
    );
    frm.set_value({ branch });
  }
}

export default function sales_invoice() {
  return {
    setup: function (frm) {
      frm.cscript['is_pos'] = async function () {
        await frm.cscript.set_pos_data();
        set_branch(frm);
      };
    },
    pos_profile: set_branch,
  };
}

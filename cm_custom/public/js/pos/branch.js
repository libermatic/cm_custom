import makeExtension from '../../../../../posx/posx/public/js/pos/factory';

export default function branch(Pos) {
  return makeExtension(
    'branch',
    class PosWithBranch extends Pos {
      set_pos_profile_data() {
        return super.set_pos_profile_data().then(
          async function () {
            const { message: { branch } = {} } = await frappe.db.get_value(
              'POS Profile',
              this.frm.doc.pos_profile,
              'branch'
            );
            this.frm.set_value({ branch });
          }.bind(this)
        );
      }
    },
    'cm' /* namespace */
  );
}

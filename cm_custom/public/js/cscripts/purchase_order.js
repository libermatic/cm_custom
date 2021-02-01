export function purchase_order() {
  return {
    onload: function (frm) {
      frm.fields_dict.scan_barcode.$input.on('keydown', function (e) {
        if (e.keyCode === 9 || e.keyCode === 13) {
          frm
            .set_value('scan_barcode', e.target.value)
            .then(() => frm.trigger('scan_barcode'));
          e.preventDefault();
          return false;
        }
      });
    },
  };
}

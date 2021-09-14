// import * as scripts from './scripts';
import * as reports from './reports';
import * as extensions from './extensions';
import * as cscripts from './cscripts';

function get_doctype(import_name) {
  return import_name
    .split('_')
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(' ');
}

const __version__ = '0.3.5';

frappe.provide('cm_custom');
cm_custom = { __version__, reports, extensions };

Object.keys(cscripts).forEach((import_name) => {
  const get_handler = cscripts[import_name];
  frappe.ui.form.on(get_doctype(import_name), get_handler());
});

$(document).ajaxError(function (_event, jqXHR, ajaxSettings, thrownError) {
  if (
    jqXHR.status === 400 &&
    jqXHR.responseJSON &&
    jqXHR.responseJSON.exc_type === 'CSRFTokenError'
  ) {
    frappe.msgprint(
      __(`
        CSRF Token not invalid.
        Subsequent requests will fail.
        Manually browser <strong>REFRESH</strong> required to recover.
      `)
    );
  }
});

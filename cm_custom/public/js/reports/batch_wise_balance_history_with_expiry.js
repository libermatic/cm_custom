function load_filters_on_load(report_name, filter_fn) {
  return async function (report) {
    if (!frappe.query_reports[report_name]) {
      const base = new frappe.views.QueryReport();
      base.report_name = report_name;
      await base.get_report_doc();
      await base.get_report_settings();
    }
    const filters = frappe.query_reports[report_name].filters;
    report.report_settings.filters = filter_fn(filters);
    report.setup_filters();
  };
}

export default function batch_wise_balance_history_with_expiry() {
  return {
    onload: load_filters_on_load('Batch-Wise Balance History', (filters) => [
      ...filters,
      {
        fieldtype: 'Check',
        fieldname: 'hide_zero_stock',
        label: __('Hide Zero Stock'),
      },
    ]),
    filters: [],
  };
}

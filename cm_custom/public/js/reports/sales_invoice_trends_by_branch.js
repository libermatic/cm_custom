import { load_filters_on_load } from './utils';

export default function sales_invoice_trends_by_branch() {
  return {
    onload: load_filters_on_load('Sales Invoice Trends', (filters) => [
      ...filters,
      ...erpnext.dimension_filters.map(
        ({ fieldname, label, document_type }) => ({
          fieldname,
          label: __(label),
          fieldtype: 'Link',
          options: document_type,
        })
      ),
    ]),
    filters: [],
  };
}

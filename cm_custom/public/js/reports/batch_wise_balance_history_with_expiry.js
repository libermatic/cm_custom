import { load_filters_on_load } from './utils';

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

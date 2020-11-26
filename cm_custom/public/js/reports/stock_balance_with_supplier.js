export default function stock_balance_with_supplier() {
  const today = frappe.datetime.get_today();
  return {
    filters: [
      {
        fieldtype: 'Link',
        fieldname: 'item_group',
        label: 'Item Group',
        options: 'Item Group',
      },
      {
        fieldtype: 'Link',
        fieldname: 'warehouse',
        label: 'Warehouse',
        options: 'Warehouse',
      },
      {
        fieldtype: 'Link',
        fieldname: 'supplier',
        label: 'Supplier',
        options: 'Supplier',
      },
    ],
  };
}

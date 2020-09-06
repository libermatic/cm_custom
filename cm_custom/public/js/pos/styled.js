import { makeExtension } from './utils';

export default function styled(Pos) {
  return makeExtension(
    'styled',
    class PosWithStyled extends Pos {
      async make() {
        const result = await super.make();
        frappe.require(['assets/cm_custom/css/pos.css']);
        return result;
      }
    }
  );
}

export function styledItems(Items) {
  return makeExtension(
    'styledItems',
    class ItemsWithStyled extends Items {
      render_items(items) {
        const all_items = Object.values(items || this.items).map((item) =>
          this.get_item_html(item)
        );
        this.clusterize.update(all_items);
      }
    }
  );
}

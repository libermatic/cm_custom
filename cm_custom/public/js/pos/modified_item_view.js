import { makeExtension } from './utils';

export default function modified_item_view(ItemSelector) {
  return makeExtension(
    'modified_item_view',
    class ItemSelectorWithModifiedItemView extends ItemSelector {
      resize_selector(minimize) {
        super.resize_selector(minimize);
        minimize
          ? this.$component.css('grid-column', 'span 2 / span 2')
          : this.$component.css('grid-column', 'span 5 / span 5');

        const $cart = this.$component.siblings('.customer-cart-container');
        minimize
          ? $cart.css('grid-column', 'span 4 / span 4')
          : $cart.css('grid-column', 'span 5 / span 5');

        minimize
          ? this.$items_container.css(
              'grid-template-columns',
              'repeat(1, minmax(0, 1fr))'
            )
          : this.$items_container.css(
              'grid-template-columns',
              'repeat(3, minmax(0, 1fr))'
            );
      }
    }
  );
}

import { compose } from 'ramda';

import { selectorOverrides } from '../pos';

frappe.provide('cm_custom.pos');

cm_custom.pos.override = function (ns) {
  if (ns.ItemSelector) {
    ns.ItemSelector = compose(...selectorOverrides)(ns.ItemSelector);
  }
};

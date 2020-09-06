import { compose } from 'ramda';

import { pageOverrides, itemsOverrides } from '../pos';

const pos = {
  page: compose(...pageOverrides),
  items: compose(...itemsOverrides),
};

export default pos;

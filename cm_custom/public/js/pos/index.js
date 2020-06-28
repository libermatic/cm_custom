import { compose } from 'ramda';
import branch from './branch';

export const pageOverrides = [branch];

export const extensions = {
  pos: compose(...pageOverrides),
};

import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import Page from './generated/Page';

// Pre-render: the hosted site is plain HTML and CSS; no script is shipped.
export function render(): string {
  return renderToStaticMarkup(<Page />);
}

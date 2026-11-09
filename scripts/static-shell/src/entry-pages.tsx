import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { PAGES } from './generated/Pages';

// Multi-page pre-render: one generated component per URL path; the hosted site ships no script.
export function render(path: string): string {
  const Page = PAGES[path];
  if (!Page) {
    throw new Error('no generated page for ' + path);
  }
  return renderToStaticMarkup(<Page />);
}

export const paths = Object.keys(PAGES);

import React from 'react';
import { createRoot } from 'react-dom/client';
import './generated/theme.css';
import './generated/site.css';
import Page from './generated/Page';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Page />
  </React.StrictMode>
);

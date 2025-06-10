import React from 'react';
import { BrowserRouter } from 'react-router-dom';

import routes, { renderRoutes } from './routes';

// Import mobile-responsive styles
import './styles/mobile-responsive.css';

const App = () => {
  return (
    <BrowserRouter>
      {renderRoutes(routes)}
    </BrowserRouter>
  );
};

export default App;

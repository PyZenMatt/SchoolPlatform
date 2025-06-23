import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { loadStripe } from '@stripe/stripe-js';
import { Elements } from '@stripe/react-stripe-js';

import routes, { renderRoutes } from './routes';
import NotificationDisplay from './components/ui/NotificationDisplay';

// Import mobile-responsive styles
import './styles/mobile-responsive.css';

// Initialize Stripe
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY);

const App = () => {
  return (
    <BrowserRouter>
      <Elements stripe={stripePromise}>
        {renderRoutes(routes)}
        <NotificationDisplay />
      </Elements>
    </BrowserRouter>
  );
};

export default App;

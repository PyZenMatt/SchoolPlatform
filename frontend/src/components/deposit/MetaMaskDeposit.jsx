/**
 * 🔄 MetaMask Deposit Component
 * 
 * Handles MetaMask → Platform balance transfers
 * Uses existing BurnDepositInterface
 */

import React, { useState } from 'react';
import { Card, Alert } from 'react-bootstrap';
import BurnDepositInterface from '../blockchain/BurnDepositInterface';

const MetaMaskDeposit = ({ onDepositComplete }) => {
  const [success, setSuccess] = useState('');

  const handleDepositComplete = () => {
    setSuccess('Deposit completed! Your platform balance has been updated.');
    if (onDepositComplete) {
      onDepositComplete();
    }
  };

  return (
    <>
      {success && (
        <Alert variant="success" dismissible onClose={() => setSuccess('')}>
          <i className="feather icon-check-circle me-2"></i>
          {success}
        </Alert>
      )}

      {/* Use existing BurnDepositInterface */}
      <BurnDepositInterface onTransactionComplete={handleDepositComplete} />
    </>
  );
};

export default MetaMaskDeposit;

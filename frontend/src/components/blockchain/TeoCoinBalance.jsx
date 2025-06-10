import React, { useState, useEffect } from 'react';
import { Card, Spinner, Badge, Button } from 'react-bootstrap';
import { blockchainAPI } from '../../services/api/blockchainAPI';
import { web3Service } from '../../services/api/web3Service';
import { useAuth } from '../../contexts/AuthContext';

const TeoCoinBalance = ({ title = "Saldo TeoCoin", showDetails = false }) => {
  const { user: currentUser } = useAuth();
  const [balance, setBalance] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [walletConnected, setWalletConnected] = useState(false);
  const [walletAddress, setWalletAddress] = useState('');

  // Check wallet connection on component mount
  useEffect(() => {
    checkWalletConnection();
  }, []);

  // Fetch balance when both user and wallet are ready
  useEffect(() => {
    if (currentUser && walletConnected) {
      fetchBalance();
    }
  }, [currentUser, walletConnected]);

  const fetchCurrentUser = async () => {
    try {
      const response = await fetchUserProfile();
      setCurrentUser(response.data);
    } catch (err) {
      console.error('Error fetching current user:', err);
      setError('Errore nel caricamento profilo utente');
    }
  };

  const checkWalletConnection = async () => {
    try {
      const connected = await web3Service.isConnected();
      setWalletConnected(connected);
      
      if (connected) {
        const address = await web3Service.getCurrentAccount();
        setWalletAddress(address);
        // fetchBalance will be called by the useEffect when both user and wallet are ready
      }
    } catch (err) {
      console.error('Error checking wallet connection:', err);
    }
  };

  const fetchBalance = async () => {
    if (!walletConnected || !currentUser) return;
    
    setLoading(true);
    setError('');
    
    try {
      // Get blockchain balance from backend
      const balanceRes = await blockchainAPI.getWalletBalance();
      
      // Verify data belongs to current user
      if (balanceRes.data.user_id && balanceRes.data.user_id !== currentUser.id) {
        console.warn('Blockchain data mismatch - clearing cache');
        console.log('Expected user ID:', currentUser.id, 'Received user ID:', balanceRes.data.user_id);
        setBalance(0);
        setError('Dati non corrispondenti all\'utente corrente - ricarica la pagina');
        return;
      }
      
      setBalance(parseFloat(balanceRes.data.balance) || 0);
    } catch (err) {
      console.error('Error fetching balance:', err);
      setError('Errore nel caricamento saldo blockchain');
      setBalance(0);
    } finally {
      setLoading(false);
    }
  };

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  };

  const getBalanceDisplay = () => {
    if (!walletConnected) {
      return {
        value: 0,
        subtitle: 'Wallet non connesso'
      };
    }

    return {
      value: balance,
      subtitle: 'Blockchain'
    };
  };

  const balanceDisplay = getBalanceDisplay();

  return (
    <Card className="h-100">
      <Card.Body>
        <div className="d-flex justify-content-between align-items-start mb-3">
          <Card.Title className="h6 text-muted mb-0">
            {title}
          </Card.Title>
          
          {walletConnected && (
            <Badge bg="success" className="d-flex align-items-center">
              <i className="feather icon-check me-1" style={{ fontSize: '12px' }}></i>
              Web3
            </Badge>
          )}
        </div>

        <div className="mb-3">
          <div className="h3 fw-bold text-primary d-flex align-items-baseline">
            {loading ? (
              <Spinner animation="border" size="sm" className="text-primary" />
            ) : (
              <>
                {balanceDisplay.value}
                <span className="text-muted ms-2">
                  TEO
                </span>
              </>
            )}
          </div>
          
          <small className="text-muted">
            Fonte: {balanceDisplay.subtitle}
          </small>
        </div>

        {showDetails && walletConnected && (
          <div className="small text-muted">
            <div className="mb-2">
              <strong>Wallet:</strong> {formatAddress(walletAddress)}
            </div>
            <div className="mb-2">
              <strong>Saldo Blockchain:</strong> {balance} TEO
            </div>
          </div>
        )}

        {!walletConnected && (
          <div className="small text-warning mt-2">
            <i className="feather icon-alert-triangle me-1"></i>
            Connetti il wallet per vedere il saldo TeoCoin
          </div>
        )}

        {error && (
          <div className="small text-danger mt-2">
            {error}
          </div>
        )}

        {walletConnected && (
          <Button 
            variant="outline-primary" 
            size="sm" 
            className="mt-2 w-100"
            onClick={fetchBalance}
            disabled={loading}
          >
            <i className="feather icon-refresh-cw me-1"></i>
            Aggiorna
          </Button>
        )}
      </Card.Body>
    </Card>
  );
};

export default TeoCoinBalance;

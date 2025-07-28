import React, { useState, useEffect, useCallback } from 'react';
import { 
  Modal, 
  Button as BootstrapButton,
  Form,
  Alert,
  Badge,
  Spinner,
  Card,
  Row,
  Col,
  InputGroup
} from 'react-bootstrap';
import { BrowserProvider, Contract, formatEther, parseEther } from 'ethers';
import './TeoCoinWithdrawal.scss';

// TeoCoin contract configuration
const TEOCOIN_CONTRACT = '0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8';
const POLYGON_AMOY_CHAIN_ID = '0x13882'; // 80002 in hex
const TEOCOIN_ABI = [
  {
    "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "decimals",
    "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
    "stateMutability": "view",
    "type": "function"
  }
];

const TeoCoinWithdrawal = ({ open, onClose, userBalance = 0 }) => {
  // State management
  const [walletConnected, setWalletConnected] = useState(false);
  const [walletAddress, setWalletAddress] = useState('');
  const [withdrawalAmount, setWithdrawalAmount] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [alert, setAlert] = useState(null);
  const [dbBalance, setDbBalance] = useState(userBalance);
  const [metamaskBalance, setMetamaskBalance] = useState(0);
  const [withdrawalHistory, setWithdrawalHistory] = useState([]);
  const [provider, setProvider] = useState(null);
  const [contract, setContract] = useState(null);

  // Utility functions
  const showAlert = useCallback((message, severity = 'info', duration = 5000) => {
    setAlert({ message, severity });
    setTimeout(() => setAlert(null), duration);
  }, []);

  const getCsrfToken = useCallback(() => {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') {
        return decodeURIComponent(value);
      }
    }
    return null;
  }, []);

  // MetaMask connection functions
  const connectWallet = useCallback(async () => {
    if (!window.ethereum) {
      showAlert('MetaMask is not installed. Please install MetaMask to continue.', 'error');
      return;
    }

    try {
      setIsProcessing(true);
      
      // Request account access
      const accounts = await window.ethereum.request({ 
        method: 'eth_requestAccounts' 
      });
      
      const address = accounts[0];
      setWalletAddress(address);
      setWalletConnected(true);
      
      // Initialize provider and contract
      const provider = new BrowserProvider(window.ethereum);
      setProvider(provider);
      
      // Check and switch to Polygon Amoy if needed
      await switchToPolygonAmoy();
      
      showAlert('Wallet connected successfully!', 'success');
      
      // Link wallet address with user account
      await linkWalletAddress(address);
      
    } catch (error) {
      console.error('Wallet connection failed:', error);
      showAlert('Failed to connect wallet. Please try again.', 'error');
    } finally {
      setIsProcessing(false);
    }
  }, [showAlert]);

  const switchToPolygonAmoy = useCallback(async () => {
    try {
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: POLYGON_AMOY_CHAIN_ID }]
      });
    } catch (error) {
      if (error.code === 4902) {
        // Network not added, add it
        try {
          await window.ethereum.request({
            method: 'wallet_addEthereumChain',
            params: [{
              chainId: POLYGON_AMOY_CHAIN_ID,
              chainName: 'Polygon Amoy Testnet',
              nativeCurrency: {
                name: 'MATIC',
                symbol: 'MATIC',
                decimals: 18
              },
              rpcUrls: ['https://rpc-amoy.polygon.technology/'],
              blockExplorerUrls: ['https://amoy.polygonscan.com/']
            }]
          });
        } catch (addError) {
          throw new Error('Failed to add Polygon Amoy network');
        }
      } else {
        throw error;
      }
    }
  }, []);

  const linkWalletAddress = useCallback(async (address) => {
    try {
      // For now, we'll store the wallet address locally
      // In the future, this can be sent to the backend
      console.log('Wallet linked:', address);
      showAlert('Wallet address linked successfully!', 'success');
    } catch (error) {
      console.error('Failed to link wallet:', error);
      showAlert('Failed to link wallet address. Please try again.', 'warning');
    }
  }, [showAlert]);

  // Balance functions
  const refreshBalances = useCallback(async () => {
    try {
      // Refresh DB balance using the withdrawal API balance endpoint
      const token = localStorage.getItem('accessToken');
      const dbResponse = await fetch('/api/v1/teocoin/withdrawals/balance/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!dbResponse.ok) {
        throw new Error(`Balance API error! status: ${dbResponse.status}`);
      }
      
      const dbData = await dbResponse.json();
      if (dbData.success && dbData.balance) {
        // Use the correct field names from the API response
        setDbBalance(parseFloat(dbData.balance.available || 0));
      } else {
        console.warn('Balance API returned no data or error:', dbData);
        showAlert('Failed to load balance. Using cached data.', 'warning');
      }

      // Refresh MetaMask balance if connected
      if (walletConnected && walletAddress && provider) {
        try {
          const contract = new Contract(TEOCOIN_CONTRACT, TEOCOIN_ABI, provider);
          const balance = await contract.balanceOf(walletAddress);
          const decimals = await contract.decimals();
          const formattedBalance = parseFloat(formatEther(balance));
          setMetamaskBalance(formattedBalance);
        } catch (error) {
          console.error('Failed to fetch MetaMask balance:', error);
          showAlert('Failed to refresh MetaMask balance', 'warning');
        }
      }
    } catch (error) {
      console.error('Failed to refresh balances:', error);
      showAlert('Failed to refresh balance. Please check your connection.', 'error');
    }
  }, [walletConnected, walletAddress, provider, showAlert]);

  // Withdrawal functions
  const handleWithdrawal = useCallback(async () => {
    if (!withdrawalAmount || parseFloat(withdrawalAmount) <= 0) {
      showAlert('Please enter a valid withdrawal amount', 'error');
      return;
    }

    if (parseFloat(withdrawalAmount) > dbBalance) {
      showAlert('Insufficient balance for withdrawal', 'error');
      return;
    }

    if (!walletConnected || !walletAddress) {
      showAlert('Please connect your MetaMask wallet first', 'error');
      return;
    }

    try {
      setIsProcessing(true);
      
      const token = localStorage.getItem('accessToken');
      
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      // Use the correct field name that the API expects
      const requestData = {
        amount: parseFloat(withdrawalAmount),
        metamask_address: walletAddress  // Changed from wallet_address to metamask_address
      };

      console.log('Sending withdrawal request:', requestData);

      const response = await fetch('/api/v1/teocoin/withdrawals/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(requestData)
      });

      const data = await response.json();
      console.log('Withdrawal response:', data);

      if (!response.ok) {
        // Handle different types of HTTP errors
        if (response.status === 400) {
          const errorMessage = data.error || data.message || 'Invalid request data. Please check your inputs.';
          throw new Error(errorMessage);
        } else if (response.status === 401) {
          throw new Error('Authentication failed. Please log in again.');
        } else if (response.status === 403) {
          throw new Error('You do not have permission to perform this action.');
        } else if (response.status === 404) {
          throw new Error('Withdrawal service not found. Please contact support.');
        } else if (response.status === 429) {
          throw new Error('Too many requests. Please wait and try again.');
        } else if (response.status >= 500) {
          throw new Error('Server error. Please try again later or contact support.');
        } else {
          throw new Error(`Request failed with status ${response.status}. Please try again.`);
        }
      }
      
      if (data.success) {
        showAlert(`Withdrawal request submitted successfully! Request ID: ${data.withdrawal_id}`, 'success');
        setWithdrawalAmount('');
        
        // Wait a moment before refreshing to allow backend to update
        setTimeout(async () => {
          await refreshBalances();
          await loadWithdrawalHistory();
        }, 1000);
      } else {
        // Handle API-level errors (when response is 200 but success is false)
        const errorMessage = data.error || data.message || 'Withdrawal failed for unknown reason';
        throw new Error(errorMessage);
      }
      
    } catch (error) {
      console.error('Withdrawal failed:', error);
      
      // Provide specific error messages for common issues
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        showAlert('Network error. Please check your internet connection and try again.', 'error');
      } else if (error.message.includes('Authentication')) {
        showAlert('Authentication failed. Please log in again.', 'error');
      } else if (error.message.includes('Insufficient balance')) {
        showAlert('Insufficient balance for this withdrawal.', 'error');
      } else {
        showAlert(`Withdrawal failed: ${error.message}`, 'error');
      }
    } finally {
      setIsProcessing(false);
    }
  }, [withdrawalAmount, dbBalance, walletConnected, walletAddress, getCsrfToken, showAlert, refreshBalances]);

  const loadWithdrawalHistory = useCallback(async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('/api/v1/teocoin/withdrawals/history/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        console.warn(`Withdrawal history API error: ${response.status}`);
        return; // Don't throw error, just return
      }
      
      const data = await response.json();
      if (data.success) {
        setWithdrawalHistory(data.withdrawals || []);
      }
    } catch (error) {
      console.error('Failed to load withdrawal history:', error);
    }
  }, []);

  // Effects
  useEffect(() => {
    if (open) {
      refreshBalances();
      loadWithdrawalHistory();
    }
  }, [open, refreshBalances, loadWithdrawalHistory]);

  useEffect(() => {
    setDbBalance(userBalance);
  }, [userBalance]);

  // Event handlers
  const handleClose = () => {
    setAlert(null);
    onClose();
  };

  return (
    <Modal 
      show={open} 
      onHide={handleClose} 
      size="lg"
      centered
      className="teocoin-withdrawal-modal"
    >
      <Modal.Header closeButton className="bg-gradient-success text-white border-0">
        <Modal.Title>
          <i className="feather icon-send me-2"></i>
          Prelievo TeoCoin
        </Modal.Title>
      </Modal.Header>

      <Modal.Body>
        {alert && (
          <Alert variant={alert.severity === 'error' ? 'danger' : alert.severity === 'success' ? 'success' : 'info'} 
                 dismissible 
                 onClose={() => setAlert(null)}>
            <i className="feather icon-info me-2"></i>
            {alert.message}
          </Alert>
        )}

        {/* Balance Overview */}
        <Row className="mb-4">
          <Col md={6}>
            <Card className="border-0 shadow-sm">
              <Card.Header className="bg-gradient-primary text-white border-0">
                <h6 className="mb-0">
                  <i className="feather icon-database me-2"></i>
                  Saldo Piattaforma
                </h6>
              </Card.Header>
              <Card.Body className="text-center">
                <h3 className="text-primary mb-0">{dbBalance.toFixed(2)} TEO</h3>
              </Card.Body>
            </Card>
          </Col>
          <Col md={6}>
            <Card className="border-0 shadow-sm">
              <Card.Header className="bg-gradient-secondary text-white border-0">
                <div className="d-flex justify-content-between align-items-center">
                  <h6 className="mb-0">
                    <i className="feather icon-credit-card me-2"></i>
                    Saldo MetaMask
                  </h6>
                  <BootstrapButton 
                    variant="outline-light" 
                    size="sm" 
                    onClick={refreshBalances}
                    title="Aggiorna saldi"
                  >
                    <i className="feather icon-refresh-cw"></i>
                  </BootstrapButton>
                </div>
              </Card.Header>
              <Card.Body className="text-center">
                <h3 className="text-secondary mb-0">{metamaskBalance.toFixed(2)} TEO</h3>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Wallet Connection */}
        {!walletConnected ? (
          <div className="text-center mb-4">
            <p className="mb-3">Connetti il tuo wallet MetaMask per iniziare il prelievo di TeoCoin</p>
            <BootstrapButton
              variant="primary"
              size="lg"
              onClick={connectWallet}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <>
                  <Spinner animation="border" size="sm" className="me-2" />
                  Connessione in corso...
                </>
              ) : (
                <>
                  <i className="feather icon-link me-2"></i>
                  Connetti MetaMask
                </>
              )}
            </BootstrapButton>
          </div>
        ) : (
          <div className="mb-4">
            <div className="d-flex align-items-center mb-3">
              <i className="feather icon-check-circle text-success me-2"></i>
              <span className="me-2">
                Wallet connesso: {`${walletAddress.slice(0, 6)}...${walletAddress.slice(-4)}`}
              </span>
              <Badge bg="success">Connesso</Badge>
            </div>

            {/* Withdrawal Form */}
            <Card className="border-0 bg-light mb-3">
              <Card.Body>
                <Card.Title>
                  <i className="fas fa-paper-plane me-2"></i>
                  Richiedi Prelievo
                </Card.Title>
                
                <Form.Group className="mb-3">
                  <Form.Label>Importo Prelievo (TEO)</Form.Label>
                  <InputGroup>
                    <Form.Control
                      type="number"
                      value={withdrawalAmount}
                      onChange={(e) => setWithdrawalAmount(e.target.value)}
                      min="0.01"
                      max={dbBalance}
                      step="0.01"
                      placeholder="Inserisci importo"
                    />
                    <InputGroup.Text>TEO</InputGroup.Text>
                  </InputGroup>
                  <Form.Text className="text-muted">
                    Disponibile: {dbBalance.toFixed(2)} TEO
                  </Form.Text>
                </Form.Group>

                <BootstrapButton
                  variant="primary"
                  onClick={handleWithdrawal}
                  disabled={isProcessing || !withdrawalAmount || parseFloat(withdrawalAmount) <= 0}
                  className="w-100"
                >
                  {isProcessing ? (
                    <>
                      <Spinner animation="border" size="sm" className="me-2" />
                      Elaborazione...
                    </>
                  ) : (
                    <>
                      <i className="fas fa-paper-plane me-2"></i>
                      Richiedi Prelievo
                    </>
                  )}
                </BootstrapButton>
              </Card.Body>
            </Card>

            {/* Withdrawal History */}
            {withdrawalHistory.length > 0 && (
              <Card>
                <Card.Header>
                  <i className="fas fa-history me-2"></i>
                  Prelievi Recenti
                </Card.Header>
                <Card.Body>
                  {withdrawalHistory.slice(0, 3).map((withdrawal, index) => (
                    <div 
                      key={index}
                      className={`d-flex justify-content-between align-items-center py-2 ${
                        index < 2 ? 'border-bottom' : ''
                      }`}
                    >
                      <div>
                        <div className="fw-bold">{withdrawal.amount} TEO</div>
                        <small className="text-muted">
                          {new Date(withdrawal.created_at).toLocaleDateString('it-IT')}
                        </small>
                      </div>
                      <Badge 
                        bg={
                          withdrawal.status === 'completed' ? 'success' :
                          withdrawal.status === 'pending' ? 'warning' : 'secondary'
                        }
                      >
                        {withdrawal.status}
                      </Badge>
                    </div>
                  ))}
                </Card.Body>
              </Card>
            )}
          </div>
        )}

        {/* Information */}
        <Alert variant="info">
          <i className="feather icon-info me-2"></i>
          I prelievi vengono processati sulla rete Polygon Amoy testnet. 
          Assicurati che MetaMask sia connesso alla rete corretta.
        </Alert>
      </Modal.Body>

      <Modal.Footer className="border-0">
        <BootstrapButton variant="outline-secondary" onClick={handleClose}>
          <i className="feather icon-x me-2"></i>
          Chiudi
        </BootstrapButton>
      </Modal.Footer>
    </Modal>
  );
};

export default TeoCoinWithdrawal;

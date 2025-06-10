import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Button, Badge, Alert, Spinner } from 'react-bootstrap';
import { web3Service } from '../../services/api/web3Service';
import { blockchainAPI } from '../../services/api/blockchainAPI';

const WalletConnection = ({ user, onWalletConnected }) => {
  const [isConnecting, setIsConnecting] = useState(false);
  const [walletAddress, setWalletAddress] = useState(null);
  const [balance, setBalance] = useState('0');
  const [tokenInfo, setTokenInfo] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [addressCopied, setAddressCopied] = useState(false);
  const [isCheckingConnection, setIsCheckingConnection] = useState(true);
  const [lastBalanceUpdate, setLastBalanceUpdate] = useState(null);

  // Cache duration in milliseconds (5 minutes)
  const BALANCE_CACHE_DURATION = 5 * 60 * 1000;

  // Cache management functions
  const getCachedBalance = (walletAddress) => {
    if (!walletAddress) return null;
    
    const cacheKey = `balance_${walletAddress}`;
    const cached = localStorage.getItem(cacheKey);
    
    if (cached) {
      const { balance, timestamp } = JSON.parse(cached);
      const now = Date.now();
      
      if (now - timestamp < BALANCE_CACHE_DURATION) {
        console.log('Usando saldo dalla cache:', balance);
        setLastBalanceUpdate(new Date(timestamp));
        return balance;
      } else {
        console.log('Cache del saldo scaduta, ricaricamento necessario');
        localStorage.removeItem(cacheKey);
      }
    }
    
    return null;
  };

  const setCachedBalance = (walletAddress, balance) => {
    if (!walletAddress) return;
    
    const cacheKey = `balance_${walletAddress}`;
    const cacheData = {
      balance,
      timestamp: Date.now()
    };
    
    localStorage.setItem(cacheKey, JSON.stringify(cacheData));
    setLastBalanceUpdate(new Date());
    console.log('Saldo salvato nella cache:', balance);
  };

  useEffect(() => {
    loadTokenInfo();
    checkExistingConnection();
    
    // Setup MetaMask event listeners
    if (window.ethereum) {
      const handleAccountsChanged = async (accounts) => {
        console.log('MetaMask accounts changed:', accounts);
        if (accounts.length === 0) {
          // User disconnected all accounts from MetaMask
          console.log('Tutti gli account MetaMask disconnessi, mantengo il wallet collegato');
          // Do NOT disconnect - keep the wallet linked to the user
        } else {
          // User switched to a different account in MetaMask
          console.log('Account MetaMask cambiato, ma mantengo il wallet collegato all\'indirizzo:', walletAddress);
          // Do NOT change the connected wallet address
        }
      };

      const handleChainChanged = (chainId) => {
        console.log('MetaMask chain changed:', chainId);
        // Optionally reload balance when chain changes
        if (walletAddress) {
          loadBalance();
        }
      };

      window.ethereum.on('accountsChanged', handleAccountsChanged);
      window.ethereum.on('chainChanged', handleChainChanged);

      // Cleanup event listeners
      return () => {
        if (window.ethereum) {
          window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
          window.ethereum.removeListener('chainChanged', handleChainChanged);
        }
      };
    }
  }, []);

  useEffect(() => {
    if (walletAddress) {
      loadBalance(); // This will use cache if available
      // Save wallet address to localStorage for persistence
      localStorage.setItem('connectedWalletAddress', walletAddress);
      console.log('Wallet address aggiornato e salvato:', walletAddress);
    }
  }, [walletAddress]);

  const checkExistingConnection = async () => {
    try {
      setIsCheckingConnection(true);
      
      // Check if MetaMask is installed
      if (!web3Service.isMetamaskInstalled()) {
        setIsCheckingConnection(false);
        return;
      }

      // Check localStorage for previous connection - this takes PRIORITY
      const savedWalletAddress = localStorage.getItem('connectedWalletAddress');
      
      if (savedWalletAddress) {
        // If we have a saved address, use it regardless of MetaMask's current account
        console.log('Ripristino wallet salvato:', savedWalletAddress);
        setWalletAddress(savedWalletAddress);
        
        // Optionally try to re-link with backend to ensure sync
        try {
          await blockchainAPI.linkWallet(savedWalletAddress);
          console.log('Wallet salvato re-linkato con successo al backend');
        } catch (error) {
          console.warn('Warning: Could not re-link saved wallet with backend:', error.message);
          // If there's a 400 error, the wallet might be invalid or linked to another account
          if (error.response && error.response.status === 400) {
            console.error('Il wallet salvato non è più valido o è stato collegato ad un altro account');
            localStorage.removeItem('connectedWalletAddress');
            setWalletAddress(null);
            setError('Il wallet precedentemente salvato non è più disponibile. Riconnetti il tuo wallet.');
            return;
          }
        }
        
        if (onWalletConnected) {
          onWalletConnected(savedWalletAddress);
        }
      } else {
        // No saved wallet, check if MetaMask has any connected accounts
        const connectedAddress = await web3Service.checkConnection();
        
        if (connectedAddress) {
          // MetaMask has a connected account, but no saved wallet
          // This means it's a fresh connection
          console.log('Nessun wallet salvato, ma MetaMask è connesso:', connectedAddress);
          // Do NOT auto-connect - let user explicitly connect
        }
      }
      
    } catch (error) {
      console.error('Error checking existing wallet connection:', error);
      // Keep saved address even on error - don't clear it unnecessarily
    } finally {
      setIsCheckingConnection(false);
    }
  };

  const loadTokenInfo = async () => {
    try {
      const info = await web3Service.getTokenInfo();
      setTokenInfo(info);
    } catch (error) {
      console.error('Error loading token info:', error);
    }
  };

  const loadBalance = async (forceRefresh = false) => {
    if (!walletAddress) return;
    
    // Check cache first (unless force refresh)
    if (!forceRefresh) {
      const cachedBalance = getCachedBalance(walletAddress);
      if (cachedBalance !== null) {
        setBalance(cachedBalance);
        return;
      }
    }
    
    try {
      setIsLoading(true);
      console.log('Caricamento saldo dal network per:', walletAddress);
      
      let fetchedBalance = '0';
      
      // Try to get balance from backend first
      try {
        const balanceData = await blockchainAPI.getWalletBalance();
        fetchedBalance = balanceData.balance || '0';
        console.log('Saldo dal backend:', fetchedBalance);
      } catch (backendError) {
        console.warn('Could not get balance from backend, trying web3:', backendError);
        
        // Fallback to web3 direct balance check
        try {
          fetchedBalance = await web3Service.getBalanceOf(walletAddress);
          console.log('Saldo da web3:', fetchedBalance);
        } catch (web3Error) {
          console.error('Failed to get balance from web3:', web3Error);
          // Keep last known balance
          return;
        }
      }
      
      // Update balance and cache it
      setBalance(fetchedBalance);
      setCachedBalance(walletAddress, fetchedBalance);
    } catch (error) {
      console.error('Error loading balance:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const connectWallet = async () => {
    setIsConnecting(true);
    setError(null);
    
    try {
      // Connect to MetaMask
      const address = await web3Service.connectWallet();
      
      if (!address) {
        throw new Error('Non è stato possibile ottenere l\'indirizzo del wallet');
      }
      
      console.log('Wallet connesso via MetaMask:', address);
      
      try {
        // Link wallet to user in backend
        await blockchainAPI.linkWallet(address);
        console.log('Wallet collegato con successo al backend');
        
        // Set wallet address ONLY after successful backend linking
        setWalletAddress(address);
        
        if (onWalletConnected) {
          onWalletConnected(address);
        }
      } catch (linkError) {
        console.error('Error linking wallet to backend:', linkError);
        
        if (linkError.response && linkError.response.status === 400) {
          // This is likely a validation error from the backend
          const errorMessage = linkError.response.data.detail || 
                               linkError.response.data.error || 
                               'Questo wallet non può essere collegato. Potrebbe essere già associato ad un altro account.';
          setError(errorMessage);
        } else {
          setError('Errore nel collegamento del wallet al tuo account. Riprova più tardi.');
        }
        
        // Reset connection state
        localStorage.removeItem('connectedWalletAddress');
      }
    } catch (error) {
      setError(error.message);
      console.error('Errore connessione wallet:', error);
      // Clear any saved address on connection error
      localStorage.removeItem('connectedWalletAddress');
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnectWallet = () => {
    console.log('Disconnessione wallet manuale per indirizzo:', walletAddress);
    
    // Clear cache for this wallet address
    if (walletAddress) {
      const cacheKey = `balance_${walletAddress}`;
      localStorage.removeItem(cacheKey);
    }
    
    setWalletAddress(null);
    setBalance('0');
    setLastBalanceUpdate(null);
    localStorage.removeItem('connectedWalletAddress');
    web3Service.disconnect();
    console.log('Wallet disconnesso, localStorage e cache puliti');
  };

  const refreshBalance = async () => {
    console.log('Aggiornamento manuale del saldo richiesto');
    await loadBalance(true); // Force refresh = true
  };

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.slice(0, 8)}...${address.slice(-6)}`;
  };

  const copyAddressToClipboard = async (address) => {
    try {
      await navigator.clipboard.writeText(address);
      setAddressCopied(true);
      setTimeout(() => setAddressCopied(false), 2000);
      console.log('Address copied to clipboard');
    } catch (error) {
      console.error('Failed to copy address:', error);
    }
  };

  if (!web3Service.isMetamaskInstalled()) {
    return (
      <Card className="bg-light">
        <Card.Body>
          <div className="d-flex align-items-center">
            <i className="feather icon-alert-circle text-warning me-2 f-20"></i>
            <div>
              <h6 className="mb-1">Metamask richiesto</h6>
              <p className="mb-0 text-muted">Installa Metamask per utilizzare i TeoCoins</p>
              <a
                href="https://metamask.io/download/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary d-inline-flex align-items-center mt-2"
              >
                Scarica Metamask
                <i className="feather icon-external-link ms-1 f-12"></i>
              </a>
            </div>
          </div>
        </Card.Body>
      </Card>
    );
  }

  return (
    <Card className="widget-primary-card">
      <Card.Header>
        <Card.Title as="h5" className="text-white">
          <i className="feather icon-credit-card me-2"></i>
          Wallet TeoCoins
        </Card.Title>
      </Card.Header>
      <Card.Body>
        {tokenInfo && (
          <div className="bg-white rounded p-3 mb-3 shadow-sm">
            <div className="d-flex justify-content-between align-items-center">
              <div>
                <h6 className="mb-1">{tokenInfo.name}</h6>
                <p className="text-muted mb-0 f-12">
                  {tokenInfo.symbol} • Polygon Amoy
                </p>
              </div>
              <Badge bg="primary" pill>{tokenInfo.symbol}</Badge>
            </div>
          </div>
        )}

        {walletAddress ? (
          <div className="wallet-connected">
            {/* Connected Wallet Address Display */}
            <div className="bg-white rounded p-3 mb-3 border-left-success border-3 shadow-sm">
              <div className="d-flex align-items-center mb-2">
                <i className="feather icon-check-circle text-success me-2"></i>
                <h6 className="mb-0 text-success">Wallet Collegato</h6>
              </div>
              
              <div className="bg-light rounded p-3 mt-2">
                <div className="d-flex justify-content-between align-items-center">
                  <div>
                    <small className="text-muted d-block">Indirizzo Wallet</small>
                    <p className="mb-0 text-break f-12 text-monospace">{walletAddress}</p>
                  </div>
                  <Button
                    variant="light"
                    size="sm"
                    onClick={() => copyAddressToClipboard(walletAddress)}
                    title="Copia indirizzo"
                  >
                    {addressCopied ? (
                      <><i className="feather icon-check text-success me-1"></i> Copiato</>
                    ) : (
                      <><i className="feather icon-copy me-1"></i> Copia</>
                    )}
                  </Button>
                </div>
              </div>
            </div>

            {/* Balance Display */}
            <div className="bg-white rounded p-3 mb-3 shadow-sm">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <small className="text-muted">Saldo TEO</small>
                  <h3 className="text-primary fw-bold mb-0">
                    {isLoading ? <Spinner animation="border" size="sm" /> : parseFloat(balance).toFixed(2)}
                  </h3>
                  <small className="text-muted">TeoCoins</small>
                  {lastBalanceUpdate && (
                    <small className="text-muted d-block mt-1">
                      Aggiornato: {lastBalanceUpdate.toLocaleTimeString()}
                    </small>
                  )}
                </div>
                <div className="d-flex flex-column gap-2">
                  <Button
                    variant="outline-primary"
                    size="sm"
                    onClick={refreshBalance}
                    disabled={isLoading}
                  >
                    <i className="feather icon-refresh-cw me-1"></i>
                    {isLoading ? 'Aggiornando...' : 'Aggiorna'}
                  </Button>
                  <Button
                    variant="outline-danger"
                    size="sm"
                    onClick={disconnectWallet}
                  >
                    <i className="feather icon-log-out me-1"></i>
                    Disconnetti
                  </Button>
                </div>
              </div>
            </div>

            <div className="bg-light rounded p-3">
              <p className="mb-2 f-12"><i className="feather icon-info me-1"></i> I TeoCoins vengono automaticamente assegnati per:</p>
              <ul className="ps-4 mb-0 f-12">
                <li>Completamento corsi: 10 TEO</li>
                <li>Sblocco achievements: 5 TEO</li>
                <li>Partecipazione attiva: vari importi</li>
              </ul>
              <Alert variant="info" className="mt-2 py-2 px-3 mb-0">
                <p className="mb-0 f-12">
                  <i className="feather icon-zap me-1"></i>
                  <strong>Tip:</strong> Il tuo wallet rimane collegato anche se cambi account su MetaMask. 
                  Per cambiare wallet, usa il pulsante "Disconnetti" e riconnetti con un altro account.
                </p>
              </Alert>
            </div>
          </div>
        ) : isCheckingConnection ? (
          <div className="text-center py-4">
            <Spinner animation="border" variant="primary" />
            <p className="text-muted mt-3 mb-0">Controllo connessione wallet...</p>
          </div>
        ) : (
          <div>
            <p className="text-white mb-3">
              Collega il tuo wallet Metamask per iniziare a guadagnare TeoCoins. 
              Una volta collegato, rimarrà associato al tuo account anche se cambi wallet su MetaMask.
            </p>
            
            <Button
              onClick={connectWallet}
              disabled={isConnecting}
              variant="light"
              className="d-block w-100 mb-3"
            >
              {isConnecting ? (
                <>
                  <Spinner animation="border" size="sm" className="me-2" />
                  Connettendo...
                </>
              ) : (
                <>
                  <i className="feather icon-credit-card me-2"></i>
                  Connetti Wallet
                </>
              )}
            </Button>

            <p className="text-center text-white-50 mb-0 f-12">
              Assicurati di essere sulla rete Polygon Amoy
            </p>
          </div>
        )}

        {error && (
          <Alert variant="danger" className="mt-3 mb-0">
            <div className="d-flex align-items-center">
              <i className="feather icon-alert-circle me-2"></i>
              <p className="mb-0">{error}</p>
            </div>
          </Alert>
        )}
      </Card.Body>
    </Card>
  );
};

export default WalletConnection;

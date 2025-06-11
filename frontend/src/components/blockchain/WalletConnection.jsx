import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { AlertCircle, Wallet, CheckCircle, ExternalLink, Copy, Check } from 'lucide-react';
import { web3Service } from '../../services/api/web3Service';
import { blockchainAPI } from '../../services/api/blockchainAPI';

const WalletConnection = ({ user, onWalletConnected }) => {
  const [isConnecting, setIsConnecting] = useState(false);
  const [walletAddress, setWalletAddress] = useState(null); // Start with null, will be set by checkExistingConnection
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
    
    // Set wallet address from user prop instead of localStorage
    if (user && user.wallet_address) {
      console.log('Setting wallet address from user:', user.wallet_address);
      setWalletAddress(user.wallet_address);
    } else {
      console.log('No wallet address found in user data');
      setWalletAddress(null);
    }
    
    setIsCheckingConnection(false);
  }, [user]);

  useEffect(() => {
    if (walletAddress) {
      loadBalance(); // Load balance when wallet address is set
      console.log('Wallet address set:', walletAddress);
    }
  }, [walletAddress]);

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
        console.log('Saldo ottenuto dal backend:', fetchedBalance);
      } catch (backendError) {
        console.warn('Errore backend, usando Web3 fallback:', backendError.message);
        
        // Fallback to Web3 direct call using the linked wallet address
        const web3Balance = await web3Service.getBalance(walletAddress);
        fetchedBalance = web3Balance;
        console.log('Saldo ottenuto tramite Web3 per indirizzo:', walletAddress);
      }
      
      // Update state and cache
      setBalance(fetchedBalance);
      setCachedBalance(walletAddress, fetchedBalance);
      
    } catch (error) {
      console.error('Error loading balance:', error);
      setError('Impossibile caricare il saldo. Verifica la connessione di rete.');
    } finally {
      setIsLoading(false);
    }
  };

  const connectWallet = async () => {
    setIsConnecting(true);
    setError(null);

    try {
      // Connect to Metamask to get wallet address
      const address = await web3Service.connectWallet();
      
      try {
        // Link wallet to user account in backend
        const linkResult = await blockchainAPI.linkWallet(address);
        
        setWalletAddress(address);
        setBalance(linkResult.balance || '0');
        
        if (onWalletConnected) {
          onWalletConnected(address);
        }

        console.log('Wallet connesso e collegato al backend:', address);
      } catch (linkError) {
        // Handle specific backend errors
        console.error('Error linking wallet:', linkError);
        
        if (linkError.response && linkError.response.status === 400) {
          // This is likely a validation error from the backend
          const errorMessage = linkError.response.data.detail || 
                               linkError.response.data.error || 
                               'Questo wallet non può essere collegato. Potrebbe essere già associato ad un altro account.';
          setError(errorMessage);
        } else {
          setError('Errore nel collegamento del wallet al tuo account. Riprova più tardi.');
        }
      }
    } catch (error) {
      setError(error.message);
      console.error('Errore connessione wallet:', error);
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
    web3Service.disconnect();
    console.log('Wallet disconnesso');
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
      <Card className="border-orange-200 bg-orange-50">
        <CardContent className="pt-6">
          <div className="flex items-center space-x-3">
            <AlertCircle className="h-5 w-5 text-orange-600" />
            <div>
              <p className="text-sm font-medium text-orange-800">
                Metamask richiesto
              </p>
              <p className="text-sm text-orange-600">
                Installa Metamask per utilizzare i TeoCoins
              </p>
              <a
                href="https://metamask.io/download/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-orange-700 underline hover:text-orange-900 inline-flex items-center mt-1"
              >
                Scarica Metamask
                <ExternalLink className="h-3 w-3 ml-1" />
              </a>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center space-x-2 text-purple-800">
          <Wallet className="h-5 w-5" />
          <span>Wallet TeoCoins</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {tokenInfo && (
          <div className="bg-white rounded-lg p-3 border border-purple-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">{tokenInfo.name}</p>
                <p className="text-xs text-gray-500">
                  {tokenInfo.symbol} • Polygon Amoy
                </p>
              </div>
              <Badge variant="outline" className="text-purple-700 border-purple-300">
                {tokenInfo.symbol}
              </Badge>
            </div>
          </div>
        )}

        {walletAddress ? (
          <div className="space-y-4">
            {/* Connected Wallet Address Display */}
            <div className="bg-white rounded-lg p-4 border-2 border-green-200 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="text-sm font-semibold text-green-800">
                    Wallet Collegato
                  </span>
                </div>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-xs text-gray-500 mb-1">Indirizzo Wallet</p>
                    <p className="font-mono text-sm text-gray-800 break-all">
                      {walletAddress}
                    </p>
                  </div>
                  <button
                    onClick={() => copyAddressToClipboard(walletAddress)}
                    className="ml-3 p-2 hover:bg-gray-200 rounded-lg transition-colors flex items-center space-x-1"
                    title="Copia indirizzo"
                  >
                    {addressCopied ? (
                      <>
                        <Check className="h-4 w-4 text-green-600" />
                        <span className="text-xs text-green-600">Copiato!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4 text-gray-600" />
                        <span className="text-xs text-gray-600">Copia</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Balance Display */}
            <div className="bg-white rounded-lg p-4 border border-purple-100">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Saldo TEO</p>
                  <p className="text-2xl font-bold text-purple-800">
                    {isLoading ? '...' : parseFloat(balance).toFixed(2)}
                  </p>
                  <p className="text-xs text-gray-500">TeoCoins</p>
                  {lastBalanceUpdate && (
                    <p className="text-xs text-gray-400 mt-1">
                      Aggiornato: {lastBalanceUpdate.toLocaleTimeString()}
                    </p>
                  )}
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={refreshBalance}
                    disabled={isLoading}
                  >
                    {isLoading ? 'Aggiornando...' : 'Aggiorna'}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={disconnectWallet}
                    className="text-red-600 border-red-300 hover:bg-red-50"
                  >
                    Disconnetti
                  </Button>
                </div>
              </div>
            </div>

            <div className="text-xs text-gray-500 space-y-1">
              <p>• I TeoCoins vengono automaticamente assegnati per:</p>
              <p className="ml-2">- Completamento corsi: 10 TEO</p>
              <p className="ml-2">- Sblocco achievements: 5 TEO</p>
              <p className="ml-2">- Partecipazione attiva: vari importi</p>
              <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded">
                <p className="text-xs text-blue-700">
                  💡 <strong>Tip:</strong> Il tuo wallet rimane collegato anche se cambi account su MetaMask. 
                  Per cambiare wallet, usa il pulsante "Disconnetti" e riconnetti con un altro account.
                </p>
              </div>
            </div>
          </div>
        ) : isCheckingConnection ? (
          <div className="space-y-3 text-center">
            <div className="flex items-center justify-center space-x-2">
              <div className="w-5 h-5 border-2 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-sm text-gray-600">Controllo connessione wallet...</span>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">
              Collega il tuo wallet Metamask per iniziare a guadagnare TeoCoins. 
              Una volta collegato, rimarrà associato al tuo account anche se cambi wallet su MetaMask.
            </p>
            
            <Button
              onClick={connectWallet}
              disabled={isConnecting}
              className="w-full bg-purple-600 hover:bg-purple-700"
            >
              {isConnecting ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Connettendo...</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <Wallet className="h-4 w-4" />
                  <span>Connetti Wallet</span>
                </div>
              )}
            </Button>

            <p className="text-xs text-gray-500 text-center">
              Assicurati di essere sulla rete Polygon Amoy
            </p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default WalletConnection;

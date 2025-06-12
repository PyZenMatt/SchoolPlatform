import React, { useState, useEffect } from 'react';
import { Card, Badge, Spinner, Alert, Button, Row, Col } from 'react-bootstrap';
import { blockchainAPI } from '../../services/api/blockchainAPI';
import { web3Service } from '../../services/api/web3Service';
import { useAuth } from '../../contexts/AuthContext';
import './StudentTeoCoinDashboard.scss';

const StudentTeoCoinDashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState({
    balance: 0,
    maticBalance: 0,
    recentTransactions: [],
    rewards: [],
    networkStatus: 'disconnected',
    gasPrice: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [walletConnected, setWalletConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [showNewRewardAlert, setShowNewRewardAlert] = useState(false);
  const [newReward, setNewReward] = useState(null);

  // Auto-refresh interval (30 seconds)
  const REFRESH_INTERVAL = 30000;

  useEffect(() => {
    loadDashboardData();
    
    // Set up auto-refresh
    const interval = setInterval(loadDashboardData, REFRESH_INTERVAL);
    
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    checkWalletConnection();
  }, []);

  const checkWalletConnection = async () => {
    try {
      const connected = await web3Service.isConnected();
      setWalletConnected(connected);
    } catch (error) {
      console.error('Error checking wallet connection:', error);
    }
  };

  const loadDashboardData = async () => {
    try {
      setError(null);
      setLoading(true);
      
      if (!user?.wallet_address) {
        setDashboardData(prev => ({
          ...prev,
          networkStatus: 'disconnected'
        }));
        setLoading(false);
        return;
      }

      // Load wallet balance using web3Service (same as WalletBalanceDisplay)
      const [teoBalance, maticBalance] = await Promise.all([
        web3Service.getBalance(user.wallet_address),
        web3Service.getMaticBalance(user.wallet_address)
      ]);

      // Load transaction history
      let transactions = [];
      let rewards = [];
      try {
        const transactionsResponse = await blockchainAPI.getTransactionHistory();
        transactions = transactionsResponse?.transactions || [];
        rewards = transactions.filter(tx => 
          tx.transaction_type?.includes('reward') || tx.type === 'reward'
        ) || [];
      } catch (txError) {
        console.warn('Could not load transaction history:', txError);
      }

      // Check for new rewards since last check
      const currentBalance = parseFloat(dashboardData.balance);
      const newBalance = parseFloat(teoBalance);
      if (currentBalance > 0 && newBalance > currentBalance) {
        const newRewardAmount = newBalance - currentBalance;
        setNewReward(newRewardAmount);
        setShowNewRewardAlert(true);
        
        // Auto-hide alert after 10 seconds
        setTimeout(() => {
          setShowNewRewardAlert(false);
        }, 10000);
      }

      // Determine network status based on successful API calls
      let networkStatus = 'disconnected';
      let gasPrice = 'Sconosciuto';
      
      if (teoBalance !== null && maticBalance !== null) {
        networkStatus = 'connected';
        gasPrice = 'Basso'; // Default when connected
      }

      // Filter transactions for rewards only
      const rewardTransactions = transactions.filter(tx => 
        tx.transaction_type && (
          tx.transaction_type.includes('reward') || 
          tx.transaction_type.includes('exercise') ||
          tx.transaction_type === 'lesson_completion' ||
          tx.transaction_type === 'course_completion'
        )
      );

      // Calculate reward statistics
      const totalRewardAmount = rewardTransactions
        .filter(tx => parseFloat(tx.amount) > 0)
        .reduce((sum, tx) => sum + parseFloat(tx.amount), 0);

      const totalRewardCount = rewardTransactions.filter(tx => parseFloat(tx.amount) > 0).length;
      
      setDashboardData({
        balance: parseFloat(teoBalance),
        maticBalance: parseFloat(maticBalance),
        recentTransactions: transactions.slice(0, 5).map(tx => ({
          ...tx,
          // Ensure transaction hash has 0x prefix
          transaction_hash: tx.transaction_hash && !tx.transaction_hash.startsWith('0x') 
            ? `0x${tx.transaction_hash}` 
            : tx.transaction_hash
        })),
        rewards: {
          total_count: totalRewardCount,
          total_amount: totalRewardAmount,
          recent: rewardTransactions.slice(0, 3)
        },
        networkStatus: networkStatus,
        gasPrice: gasPrice
      });

      setLastUpdate(new Date());
      
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setError('Errore nel caricamento dei dati dashboard');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  };

  const openTransaction = (txHash) => {
    if (txHash) {
      // Ensure hash has 0x prefix for blockchain explorer
      const formattedHash = txHash.startsWith('0x') ? txHash : `0x${txHash}`;
      window.open(`https://amoy.polygonscan.com/tx/${formattedHash}`, '_blank');
    }
  };

  const formatTransactionHash = (hash) => {
    if (!hash) return null;
    // Ensure hash has 0x prefix for display
    return hash.startsWith('0x') ? hash : `0x${hash}`;
  };

  const getNetworkStatusBadge = () => {
    switch (dashboardData.networkStatus) {
      case 'connected':
        return <Badge bg="success">Connesso</Badge>;
      case 'connecting':
        return <Badge bg="warning">Connessione...</Badge>;
      default:
        return <Badge bg="danger">Disconnesso</Badge>;
    }
  };

  const getGasPriceBadge = () => {
    switch (dashboardData.gasPrice) {
      case 'Low':
        return <Badge bg="success">Basso</Badge>;
      case 'Medium':
        return <Badge bg="warning">Medio</Badge>;
      case 'High':
        return <Badge bg="danger">Alto</Badge>;
      default:
        return <Badge bg="secondary">Sconosciuto</Badge>;
    }
  };

  return (
    <div className="student-teocoin-dashboard">
      {/* New Reward Alert */}
      {showNewRewardAlert && newReward && (
        <Alert 
          variant="success" 
          className="new-reward-alert mb-4"
          dismissible
          onClose={() => setShowNewRewardAlert(false)}
        >
          <div className="d-flex align-items-center">
            <div className="reward-icon me-3">
              <i className="feather icon-gift"></i>
            </div>
            <div>
              <Alert.Heading className="h6 mb-1">
                🎉 Nuovo Reward Ricevuto!
              </Alert.Heading>
              <p className="mb-0">
                Hai ricevuto <strong>{newReward.toFixed(2)} TEO</strong> coins!
              </p>
            </div>
          </div>
        </Alert>
      )}

      <Row>
        {/* Balance Card - Enhanced with TEO and MATIC */}
        <Col md={6} lg={4} className="mb-4">
          <Card className="balance-card h-100 wallet-style">
            <Card.Body>
              <div className="d-flex justify-content-between align-items-start mb-3">
                <Card.Title className="h6 text-muted mb-0">
                  Saldi Wallet
                </Card.Title>
                {walletConnected && (
                  <Badge bg="success">
                    <i className="feather icon-check me-1"></i>
                    Web3
                  </Badge>
                )}
              </div>

              {loading ? (
                <div className="text-center py-3">
                  <Spinner animation="border" size="sm" className="text-primary" />
                </div>
              ) : (
                <div className="balances-display mb-3">
                  {/* TEO Balance */}
                  <div className="balance-row mb-3">
                    <div className="balance-amount">
                      <span className="amount">{dashboardData.balance.toFixed(2)}</span>
                      <span className="currency">TEO</span>
                    </div>
                  </div>
                  
                  {/* MATIC Balance */}
                  <div className="balance-row">
                    <div className="balance-amount-secondary">
                      <span className="amount-secondary">{dashboardData.maticBalance?.toFixed(4) || '0.0000'}</span>
                      <span className="currency-secondary">MATIC</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="balance-details">
                <small className="text-muted d-block">
                  Network: Polygon Amoy
                </small>
                {lastUpdate && (
                  <small className="text-muted">
                    Ultimo aggiornamento: {formatDate(lastUpdate)}
                  </small>
                )}
              </div>

              <Button 
                variant="outline-primary" 
                size="sm" 
                className="refresh-btn mt-3 w-100"
                onClick={loadDashboardData}
                disabled={loading}
              >
                <i className="feather icon-refresh-cw me-1"></i>
                Aggiorna
              </Button>
            </Card.Body>
          </Card>
        </Col>

        {/* Network Status Card */}
        <Col md={6} lg={4} className="mb-4">
          <Card className="network-card h-100">
            <Card.Body>
              <Card.Title className="h6 text-muted mb-3">
                Stato Network
              </Card.Title>

              <div className="network-info">
                <div className="info-row mb-2">
                  <span className="label">Connessione:</span>
                  {getNetworkStatusBadge()}
                </div>
                
                <div className="info-row mb-2">
                  <span className="label">Gas Price:</span>
                  {getGasPriceBadge()}
                </div>
                
                <div className="info-row">
                  <span className="label">Rete:</span>
                  <span className="value">Polygon Amoy</span>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        {/* Rewards Summary */}
        <Col md={6} lg={4} className="mb-4">
          <Card className="rewards-card h-100">
            <Card.Body>
              <Card.Title className="h6 text-muted mb-3">
                Rewards Ricevuti
              </Card.Title>

              <div className="rewards-stats">
                <div className="stat-item mb-2">
                  <div className="stat-value">{dashboardData.rewards.total_count || 0}</div>
                  <div className="stat-label">Totale Rewards</div>
                </div>
                
                <div className="stat-item">
                  <div className="stat-value">
                    {(dashboardData.rewards.total_amount || 0).toFixed(2)}
                  </div>
                  <div className="stat-label">TEO Totali</div>
                </div>
              </div>

              {dashboardData.rewards.recent && dashboardData.rewards.recent.length > 0 && (
                <div className="recent-rewards mt-3">
                  <small className="text-muted d-block mb-2">Ultimi rewards:</small>
                  {dashboardData.rewards.recent.map((reward, index) => (
                    <div key={index} className="reward-item small d-flex justify-content-between">
                      <span>{reward.transaction_type?.replace('_', ' ') || 'Reward'}</span>
                      <span className="text-success">+{parseFloat(reward.amount).toFixed(2)} TEO</span>
                    </div>
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Recent Transactions */}
      <Row>
        <Col lg={12}>
          <Card className="transactions-card wallet-style">
            <Card.Header>
              <div className="d-flex justify-content-between align-items-center">
                <Card.Title className="mb-0">
                  <i className="feather icon-list me-2"></i>
                  Transazioni Recenti
                </Card.Title>
                <small className="text-muted">
                  Ultime {dashboardData.recentTransactions.length} transazioni
                </small>
              </div>
            </Card.Header>
            
            <Card.Body>
              {loading ? (
                <div className="text-center">
                  <Spinner animation="border" size="sm" />
                  <p className="mt-2 mb-0 text-muted">Caricamento transazioni...</p>
                </div>
              ) : dashboardData.recentTransactions.length === 0 ? (
                <div className="text-center text-muted">
                  <i className="feather icon-inbox" style={{ fontSize: '2rem', opacity: 0.5 }}></i>
                  <p className="mt-2 mb-0">Nessuna transazione trovata</p>
                </div>
              ) : (
                <div className="transactions-list">
                  {dashboardData.recentTransactions.slice(0, 10).map((transaction, index) => (
                    <div key={index} className="transaction-item border-bottom pb-3 mb-3">
                      <div className="d-flex align-items-start">
                        <div className="transaction-icon me-3">
                          {transaction.transaction_type?.includes('reward') || transaction.transaction_type?.includes('exercise') ? (
                            <div className="icon-wrapper bg-success text-white rounded-circle p-2">
                              <i className="feather icon-gift"></i>
                            </div>
                          ) : transaction.amount > 0 ? (
                            <div className="icon-wrapper bg-success text-white rounded-circle p-2">
                              <i className="feather icon-arrow-down-left"></i>
                            </div>
                          ) : (
                            <div className="icon-wrapper bg-danger text-white rounded-circle p-2">
                              <i className="feather icon-arrow-up-right"></i>
                            </div>
                          )}
                        </div>
                        
                        <div className="transaction-details flex-grow-1">
                          <div className="d-flex justify-content-between align-items-start">
                            <div>
                              <div className="transaction-title fw-bold">
                                {transaction.transaction_type ? 
                                  transaction.transaction_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 
                                  'Transazione'
                                }
                              </div>
                              <div className="transaction-meta small text-muted">
                                {(transaction.transaction_hash || transaction.tx_hash) && (
                                  <div className="hash mb-1">
                                    <strong style={{ color: '#ecf0f1' }}>Hash:</strong> 
                                    <code className="ms-1 small" style={{ color: '#bdc3c7', backgroundColor: 'rgba(255,255,255,0.1)', padding: '2px 4px', borderRadius: '3px' }}>
                                      {formatTransactionHash(transaction.transaction_hash || transaction.tx_hash)}
                                    </code>
                                    <Button
                                      variant="link"
                                      size="sm"
                                      className="p-0 ms-2 text-decoration-none"
                                      style={{ color: '#3498db' }}
                                      onClick={() => openTransaction(transaction.transaction_hash || transaction.tx_hash)}
                                      title="Vedi su Polygonscan"
                                    >
                                      <i className="feather icon-external-link" style={{ fontSize: '0.8rem' }}></i>
                                    </Button>
                                  </div>
                                )}
                                {transaction.created_at && (
                                  <div className="date">
                                    {formatDate(transaction.created_at)}
                                  </div>
                                )}
                              </div>
                            </div>
                            
                            <div className="transaction-amount text-end">
                              <span className={`amount fw-bold ${parseFloat(transaction.amount) >= 0 ? 'text-success' : 'text-danger'}`}>
                                {parseFloat(transaction.amount) >= 0 ? '+' : ''}{parseFloat(transaction.amount || 0).toFixed(4)} TEO
                              </span>
                              {(transaction.transaction_hash || transaction.tx_hash) && (
                                <div className="mt-1">
                                  <Button
                                    variant="outline-light"
                                    size="sm"
                                    className="p-1"
                                    onClick={() => openTransaction(transaction.transaction_hash || transaction.tx_hash)}
                                    title="Vedi su Blockchain"
                                    style={{ minWidth: 'auto', borderColor: 'rgba(255,255,255,0.3)' }}
                                  >
                                    <i className="feather icon-external-link"></i>
                                  </Button>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Error Display */}
      {error && (
        <Alert variant="danger" className="mt-3">
          <i className="feather icon-alert-triangle me-2"></i>
          {error}
        </Alert>
      )}
    </div>
  );
};

export default StudentTeoCoinDashboard;

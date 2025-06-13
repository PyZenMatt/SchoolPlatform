import React, { useState, useEffect } from 'react';
import { Badge, Spinner, Alert, Row, Col } from 'react-bootstrap';
import { blockchainAPI } from '../../services/api/blockchainAPI';
import { web3Service } from '../../services/api/web3Service';
import { apiClient } from '../../services/core/apiClient';
import { useAuth } from '../../contexts/AuthContext';
import './AdminTeoCoinDashboard.scss';

const AdminTeoCoinDashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState({
    balance: 0,
    maticBalance: 0,
    recentTransactions: [],
    networkStatus: 'disconnected',
    gasPrice: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError('');
      
      if (!user?.wallet_address) {
        setDashboardData(prev => ({
          ...prev,
          networkStatus: 'disconnected'
        }));
        setLoading(false);
        return;
      }

      // Load wallet balance using web3Service (same as StudentTeoCoinDashboard)
      const [teoBalance, maticBalance] = await Promise.all([
        web3Service.getBalance(user.wallet_address),
        web3Service.getMaticBalance(user.wallet_address)
      ]);

      console.log('💰 Admin saldi caricati - TEO:', teoBalance, 'MATIC:', maticBalance);

      // Load ALL platform transactions (admin global view)
      let transactions = [];
      try {
        const transactionsResponse = await apiClient.get('/admin/transactions/');
        transactions = transactionsResponse.data || [];
        
        console.log('📋 Admin transazioni globali caricate:', transactions.length, 'transazioni di tutta la piattaforma');
      } catch (txError) {
        console.warn('Could not load platform transaction history:', txError);
      }
      
      setDashboardData({
        balance: parseFloat(teoBalance) || 0,
        maticBalance: parseFloat(maticBalance) || 0,
        recentTransactions: transactions,
        networkStatus: 'connected',
        gasPrice: 'Medium'
      });
      
      setLastUpdate(new Date().toISOString());
      
    } catch (err) {
      console.error('Error loading admin data:', err);
      setError('Errore nel caricamento dei dati admin blockchain');
      setDashboardData(prev => ({
        ...prev,
        networkStatus: 'disconnected'
      }));
    } finally {
      setLoading(false);
    }
  };

  // Helper functions for transaction display (from AdminTransactionMonitor)
  const getStatusBadge = (status) => {
    const statusMap = {
      'completed': { variant: 'success', text: 'Completata' },
      'pending': { variant: 'warning', text: 'In Attesa' },
      'failed': { variant: 'danger', text: 'Fallita' }
    };
    const config = statusMap[status] || { variant: 'secondary', text: status };
    return <Badge bg={config.variant}>{config.text}</Badge>;
  };

  const getTypeIcon = (type) => {
    const typeMap = {
      'course_purchase': 'icon-shopping-cart',
      'exercise_reward': 'icon-award',
      'review_reward': 'icon-star',
      'achievement_reward': 'icon-trophy',
      'course_earned': 'icon-circle',
      'mint': 'icon-circle',
      'transfer': 'icon-circle',
      'reward': 'icon-circle'
    };
    return typeMap[type] || 'icon-circle';
  };

  const formatAmount = (amount) => {
    return `${parseFloat(amount).toFixed(2)} TEO`;
  };

  const formatTransactionHash = (hash) => {
    if (!hash) return 'N/A';
    return hash.length > 10 ? `${hash.substring(0, 10)}...` : hash;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT');
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('it-IT');
  };

  const openTransaction = (hash) => {
    if (hash) {
      window.open(`https://amoy.polygonscan.com/tx/${hash}`, '_blank');
    }
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
    <div className="admin-teocoin-dashboard">
      <Row>
        {/* Balance Card - Enhanced with TEO and MATIC */}
        <Col md={6} lg={6} className="mb-4">
          <div className="card balance-card h-100 wallet-style">
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-start mb-3">
                <h6 className="text-muted mb-0">
                  Saldi Admin
                </h6>
                <Badge bg="primary">
                  <i className="feather icon-shield me-1"></i>
                  Admin
                </Badge>
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

              <button 
                type="button"
                className="btn btn-outline-primary btn-sm refresh-btn mt-3 w-100"
                onClick={loadDashboardData}
                disabled={loading}
              >
                <i className="feather icon-refresh-cw me-1"></i>
                Aggiorna
              </button>
            </div>
          </div>
        </Col>

        {/* Network Status Card */}
        <Col md={6} lg={6} className="mb-4">
          <div className="card network-card h-100 wallet-style">
            <div className="card-body">
              <h6 className="text-muted mb-3">
                Stato Network
              </h6>

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
            </div>
          </div>
        </Col>


      </Row>

      {/* Recent Transactions */}
      <Row>
        <Col lg={12}>
          <div className="card transactions-card wallet-style">
            <div className="card-header">
              <div className="d-flex justify-content-between align-items-center">
                <h5 className="mb-0">
                  <i className="feather icon-list me-2"></i>
                  Transazioni Piattaforma ({dashboardData.recentTransactions.length})
                </h5>
                <button 
                  type="button" 
                  className="btn btn-outline-primary btn-sm"
                  onClick={loadDashboardData}
                  disabled={loading}
                >
                  <i className="feather icon-refresh-cw me-1"></i>
                  Aggiorna
                </button>
              </div>
            </div>
            
            <div className="card-body p-0">{loading ? (
                <div className="text-center py-4">
                  <Spinner animation="border" size="sm" />
                  <p className="mt-2 mb-0 text-muted">Caricamento transazioni...</p>
                </div>
              ) : dashboardData.recentTransactions.length === 0 ? (
                <div className="text-center text-muted py-4">
                  <i className="feather icon-activity" style={{ fontSize: '2rem', opacity: 0.5 }}></i>
                  <p className="mt-2 mb-0">Nessuna transazione sulla piattaforma</p>
                  <small>Le transazioni degli utenti appariranno qui</small>
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="table table-hover">
                    <thead className="bg-light">
                      <tr>
                        <th>Data/Ora</th>
                        <th>Tipo</th>
                        <th>Utente</th>
                        <th>Importo</th>
                        <th>Status</th>
                        <th>TX Hash</th>
                        <th>Azioni</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboardData.recentTransactions.slice(0, 20).map((transaction, index) => (
                        <tr key={index}>
                          <td className="small">
                            {formatDate(transaction.created_at)}
                            <br />
                            <span className="text-muted">
                              {formatTime(transaction.created_at)}
                            </span>
                          </td>
                          <td>
                            <div className="d-flex align-items-center">
                              <i className={`feather ${getTypeIcon(transaction.transaction_type)} me-2`}></i>
                              <span className="small ms-2">
                                {transaction.transaction_type ? 
                                  transaction.transaction_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 
                                  'Transazione'
                                }
                              </span>
                            </div>
                          </td>
                          <td>
                            <div>
                              <strong>{transaction.user?.username || ''}</strong>
                              <br />
                              <span className="text-muted small">
                                {transaction.user?.email || ''}
                              </span>
                            </div>
                          </td>
                          <td>
                            <strong className={parseFloat(transaction.amount) >= 0 ? 'text-success' : 'text-danger'}>
                              {parseFloat(transaction.amount) >= 0 ? '+' : ''}{parseFloat(transaction.amount || 0).toFixed(2)} TEO
                            </strong>
                          </td>
                          <td>
                            {getStatusBadge(transaction.status)}
                          </td>
                          <td>
                            {transaction.tx_hash ? (
                              <div>
                                <code className="small">
                                  {formatTransactionHash(transaction.tx_hash)}
                                </code>
                                <br />
                                <a 
                                  href={`https://amoy.polygonscan.com/tx/${transaction.tx_hash}`}
                                  target="_blank" 
                                  rel="noopener noreferrer" 
                                  className="small text-primary"
                                >
                                  <i className="feather icon-external-link me-1"></i>Blockchain
                                </a>
                              </div>
                            ) : (
                              <span className="text-muted small">N/A</span>
                            )}
                          </td>
                          <td>
                            <div className="btn-group-vertical btn-group-sm">
                              <button 
                                type="button" 
                                className="btn btn-outline-info btn-sm"
                                title="Visualizza dettagli"
                              >
                                <i className="feather icon-eye"></i>
                              </button>
                              {transaction.status === 'failed' && (
                                <button 
                                  type="button" 
                                  className="btn btn-outline-warning btn-sm"
                                  title="Riprova transazione"
                                >
                                  <i className="feather icon-refresh-cw"></i>
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </Col>
      </Row>
    </div>
  );
};

export default AdminTeoCoinDashboard;

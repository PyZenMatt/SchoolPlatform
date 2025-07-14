import React, { useState, useEffect } from 'react';
import { Card, Badge, Spinner, Alert, Button, Row, Col } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';
import PendingWithdrawals from './PendingWithdrawals';
import BurnDepositInterface from './BurnDepositInterface';
import './StudentTeoCoinDashboard.scss';

/**
 * StudentTeoCoinDashboard - DB-based TeoCoin dashboard for students
 * Uses instant database operations instead of blockchain transactions
 */
const DBStudentTeoCoinDashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState({
    balance: {
      available_balance: '0.00',
      staked_balance: '0.00',
      pending_withdrawal: '0.00',
      total_balance: '0.00'
    },
    recentTransactions: [],
    statistics: {}
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Auto-refresh interval (10 seconds for instant updates)
  const REFRESH_INTERVAL = 10000;

  useEffect(() => {
    loadDashboardData();
    
    // Set up auto-refresh
    const interval = setInterval(loadDashboardData, REFRESH_INTERVAL);
    
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }

      // Load balance using withdrawal API for consistency
      const balanceResponse = await fetch('/api/v1/teocoin/withdrawals/balance/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!balanceResponse.ok) {
        throw new Error(`Balance API error! status: ${balanceResponse.status}`);
      }

      const balanceData = await balanceResponse.json();
      console.log('🔍 Balance API Response:', balanceData);

      // Extract balance data correctly from withdrawal API format
      const balance = balanceData.success && balanceData.balance 
        ? {
            available_balance: parseFloat(balanceData.balance.available || 0).toFixed(2),
            staked_balance: parseFloat(balanceData.balance.staked || 0).toFixed(2),
            pending_withdrawal: parseFloat(balanceData.balance.pending_withdrawal || 0).toFixed(2),
            total_balance: parseFloat(balanceData.balance.total || 0).toFixed(2)
          }
        : {
            available_balance: '0.00',
            staked_balance: '0.00', 
            pending_withdrawal: '0.00',
            total_balance: '0.00'
          };

      // Load recent transactions
      const transactionsResponse = await fetch('/api/v1/teocoin/transactions/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const transactionsData = transactionsResponse.ok 
        ? await transactionsResponse.json() 
        : [];

      // Load platform statistics
      const statsResponse = await fetch('/api/v1/teocoin/statistics/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const statsData = statsResponse.ok 
        ? await statsResponse.json() 
        : {};

      setDashboardData({
        balance: balance,
        recentTransactions: Array.isArray(transactionsData) ? transactionsData.slice(0, 5) : [],
        statistics: statsData
      });

      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTransactionIcon = (type) => {
    switch (type) {
      case 'credit':
      case 'reward':
        return '💰';
      case 'discount':
      case 'course_purchase':
        return '🛒';
      case 'stake':
        return '🔒';
      case 'unstake':
        return '🔓';
      case 'withdrawal':
        return '📤';
      default:
        return '📊';
    }
  };

  const getTransactionColor = (type) => {
    switch (type) {
      case 'credit':
      case 'reward':
        return 'success';
      case 'discount':
      case 'course_purchase':
        return 'primary';
      case 'stake':
        return 'warning';
      case 'unstake':
        return 'info';
      case 'withdrawal':
        return 'secondary';
      default:
        return 'light';
    }
  };

  if (loading && !dashboardData.balance.total_balance) {
    return (
      <Card className="teocoin-dashboard-card">
        <Card.Body className="text-center">
          <Spinner animation="border" variant="primary" />
          <p className="mt-2">Caricamento dashboard TeoCoin...</p>
        </Card.Body>
      </Card>
    );
  }

  return (
    <div className="student-teocoin-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <h4>
          <i className="fas fa-coins"></i>
          Dashboard TeoCoin
          <Badge bg="success" className="ms-2">DB-Based</Badge>
        </h4>
        {lastUpdate && (
          <small className="text-muted">
            Ultimo aggiornamento: {formatDate(lastUpdate)}
          </small>
        )}
      </div>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          <Alert.Heading>Errore</Alert.Heading>
          {error}
        </Alert>
      )}

      <Row>
        {/* Balance Cards */}
        <Col lg={6}>
          <Card className="balance-card mb-3">
            <Card.Body>
              <div className="balance-header">
                <h5>💰 Saldo Disponibile</h5>
                <Badge bg="success">Istantaneo</Badge>
              </div>
              <div className="balance-amount">
                {parseFloat(dashboardData.balance.available_balance).toFixed(2)} TEO
              </div>
              <div className="balance-details">
                <small className="text-muted">
                  Utilizzabile per sconti sui corsi
                </small>
              </div>
            </Card.Body>
          </Card>
        </Col>

        {/* Staking Card - Only for Teachers */}
        {user?.role === 'teacher' && (
          <Col lg={6}>
            <Card className="balance-card mb-3">
              <Card.Body>
                <div className="balance-header">
                  <h5>🔒 Saldo in Staking</h5>
                  <Badge bg="warning">Solo Insegnanti</Badge>
                </div>
                <div className="balance-amount">
                  {parseFloat(dashboardData.balance.staked_balance).toFixed(2)} TEO
                </div>
                <div className="balance-details">
                  <small className="text-muted">
                    Riduce commissioni piattaforma
                  </small>
                </div>
              </Card.Body>
            </Card>
          </Col>
        )}
      </Row>

      <Row>
        {/* Total Balance */}
        <Col lg={8}>
          <Card className="total-balance-card mb-3">
            <Card.Body>
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h5>💎 {user?.role === 'student' ? 'Saldo Disponibile' : 'Saldo Totale'}</h5>
                  <div className="total-balance">
                    {user?.role === 'student' 
                      ? parseFloat(dashboardData.balance.available_balance).toFixed(2)
                      : parseFloat(dashboardData.balance.total_balance).toFixed(2)
                    } TEO
                  </div>
                </div>
                <div className="text-end">
                  <div className="conversion-rate">
                    <small className="text-muted">1 TEO = 1 EUR</small>
                  </div>
                  <div className="eur-equivalent">
                    ≈ {user?.role === 'student' 
                        ? parseFloat(dashboardData.balance.available_balance).toFixed(2)
                        : parseFloat(dashboardData.balance.total_balance).toFixed(2)
                      } €
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        {/* Quick Stats */}
        <Col lg={4}>
          <Card className="stats-card mb-3">
            <Card.Body>
              <h6>📊 Statistiche Piattaforma</h6>
              <div className="stats-grid">
                <div className="stat-item">
                  <div className="stat-value">
                    {dashboardData.statistics.total_users_with_balance || 0}
                  </div>
                  <div className="stat-label">Utenti Attivi</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">
                    {dashboardData.statistics.total_transactions || 0}
                  </div>
                  <div className="stat-label">Transazioni</div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Pending Withdrawals Section */}
      {parseFloat(dashboardData.balance.pending_withdrawal) > 0 && (
        <Row className="mb-3">
          <Col>
            <PendingWithdrawals 
              onTransactionComplete={(data) => {
                // Refresh dashboard when transaction completes
                loadDashboardData();
              }}
            />
          </Col>
        </Row>
      )}

      {/* Burn Deposit Interface */}
      <Row className="mb-3">
        <Col>
          <Card className="burn-deposit-card">
            <Card.Header>
              <h5>🔥 Add TEOcoins</h5>
              <small className="text-muted">Burn tokens from MetaMask to increase your platform balance</small>
            </Card.Header>
            <Card.Body>
              <BurnDepositInterface 
                onTransactionComplete={(data) => {
                  // Refresh dashboard when burn deposit completes
                  loadDashboardData();
                }}
              />
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Recent Transactions */}
      <Card className="transactions-card">
        <Card.Header>
          <h5>📈 Transazioni Recenti</h5>
          <Button 
            variant="outline-primary" 
            size="sm"
            onClick={loadDashboardData}
            disabled={loading}
          >
            {loading ? (
              <Spinner animation="border" size="sm" />
            ) : (
              <i className="fas fa-sync-alt"></i>
            )}
            Aggiorna
          </Button>
        </Card.Header>
        <Card.Body>
          {dashboardData.recentTransactions.length === 0 ? (
            <div className="text-center py-4">
              <i className="fas fa-history fa-3x text-muted mb-3"></i>
              <p className="text-muted">Nessuna transazione recente</p>
              <small>Le tue transazioni appariranno qui</small>
            </div>
          ) : (
            <div className="transactions-list">
              {dashboardData.recentTransactions
                .filter(transaction => {
                  // Filter out staking transactions for students
                  if (user?.role === 'student') {
                    return !['stake', 'unstake'].includes(transaction.type);
                  }
                  return true;
                })
                .map((transaction, index) => (
                <div key={transaction.id || index} className="transaction-item">
                  <div className="transaction-icon">
                    {getTransactionIcon(transaction.type)}
                  </div>
                  <div className="transaction-details">
                    <div className="transaction-type">
                      <Badge bg={getTransactionColor(transaction.type)}>
                        {transaction.type}
                      </Badge>
                    </div>
                    <div className="transaction-description">
                      {transaction.description || 'Transazione TeoCoin'}
                    </div>
                    <div className="transaction-date">
                      {formatDate(transaction.created_at)}
                    </div>
                  </div>
                  <div className="transaction-amount">
                    <span className={`amount ${parseFloat(transaction.amount) >= 0 ? 'positive' : 'negative'}`}>
                      {parseFloat(transaction.amount) >= 0 ? '+' : ''}
                      {parseFloat(transaction.amount).toFixed(2)} TEO
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card.Body>
      </Card>
    </div>
  );
};

export default DBStudentTeoCoinDashboard;

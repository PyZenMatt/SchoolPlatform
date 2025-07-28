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

      // Load balance using student API for consistency
      const balanceResponse = await fetch('/api/v1/teocoin/student/balance/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!balanceResponse.ok) {
        throw new Error(`Student balance API error! status: ${balanceResponse.status}`);
      }

      const balanceData = await balanceResponse.json();
      console.log('🔍 Student Balance API Response:', balanceData);

      // Extract balance data correctly from student API format
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

      // Load recent transactions - handle errors gracefully
      let transactionsData = [];
      try {
        const transactionsResponse = await fetch('/api/v1/teocoin/transactions/', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (transactionsResponse.ok) {
          transactionsData = await transactionsResponse.json();
        } else {
          console.warn('Transactions API error:', transactionsResponse.status);
        }
      } catch (transactionError) {
        console.warn('Failed to load transactions:', transactionError);
      }

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

      {/* Deposit and Withdrawal Components - Better Layout */}
      <Row className="mb-3 justify-content-center">
        <Col lg={5} md={6} className="mb-3">
          <BurnDepositInterface 
            onTransactionComplete={(data) => {
              loadDashboardData();
            }}
          />
        </Col>
        <Col lg={5} md={6} className="mb-3">
          <PendingWithdrawals 
            onTransactionComplete={(data) => {
              loadDashboardData();
            }}
          />
        </Col>
      </Row>

    </div>
  );
};

export default DBStudentTeoCoinDashboard;

import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Alert, Spinner, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import PendingTeachersCard from '../../components/PendingTeachersCard';
import PendingCoursesCard from '../../components/PendingCoursesCard';
import ApprovalStats from '../../components/ApprovalStats';
import AdminTransactionMonitor from '../../components/admin/AdminTransactionMonitor';
import AdminTeoCoinDashboard from '../../components/blockchain/DBAdminTeoCoinDashboard';
import TeoCoinBalanceWidget from '../../components/TeoCoinBalanceWidget';
import RevenueAnalytics from '../../components/admin/RevenueAnalytics';
import { fetchAdminDashboard } from '../../services/api/admin';
import { fetchUserProfile } from '../../services/api/dashboard';
import { getRewardPoolInfo } from '../../services/api/blockchain';

// Placeholder avatar
import avatar1 from '../../assets/images/user/avatar-1.jpg';

const AdminDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [userProfile, setUserProfile] = useState(null);
  const [rewardPoolStatus, setRewardPoolStatus] = useState(null);
  const [dashboardData, setDashboardData] = useState({
    totalUsers: 0,
    totalCourses: 0,
    pendingApprovals: 0,
    monthlyRevenue: 0
  });

  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      setError('');
      try {
        // Fetch user profile
        const profileRes = await fetchUserProfile();
        setUserProfile(profileRes.data);
        
        const res = await fetchAdminDashboard();
        setDashboardData(res.data);
        
        // Fetch reward pool status
        try {
          const poolRes = await getRewardPoolInfo();
          setRewardPoolStatus(poolRes.data);
        } catch (poolErr) {
          console.error('Error fetching reward pool info:', poolErr);
          // Don't show error for this, just show in console
        }
      } catch (err) {
        console.error('Errore API admin dashboard:', err);
        setError('Errore nel caricamento della dashboard admin');
        // Fallback data for demo
        setDashboardData({
          totalUsers: 150,
          totalCourses: 25,
          pendingApprovals: 8,
          monthlyRevenue: 2450
        });
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="pcoded-content">
        <div className="card">
          <div className="card-body text-center py-5">
            <Spinner animation="border" variant="primary" />
            <p className="mt-3 text-muted">Caricamento dashboard admin...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Welcome Card */}
      <Card className="bg-primary text-white mb-4 shadow-sm welcome-card">
        <Card.Body className="p-4">
          <Row className="align-items-center">
            <Col xs="auto">
              <div className="avatar-lg">
                <img
                  src={avatar1}
                  alt="Avatar"
                  className="rounded-circle"
                  style={{ width: '70px', height: '70px', objectFit: 'cover' }}
                />
              </div>
            </Col>
            <Col>
              <h3 className="text-white mb-1 fw-bold">
                Benvenuto{userProfile?.first_name ? `, ${userProfile.first_name}` : ''}!
              </h3>
              <p className="text-white-50 mb-0 fs-5">
                Gestisci la piattaforma e approva nuovi contenuti
              </p>
            </Col>
            <Col xs="auto" className="d-none d-md-block">
              <div className="text-end">
                <h4 className="text-white mb-1">
                  <i className="feather icon-shield me-2"></i>
                  Amministratore
                </h4>
                <p className="text-white-50 mb-0">Accesso completo</p>
              </div>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {error && (
        <Alert variant="warning" className="mb-4">
          <i className="feather icon-alert-circle me-2"></i>
          {error}
        </Alert>
      )}
      
      {/* Reward Pool Status Alert */}
      {rewardPoolStatus && rewardPoolStatus.status === 'critical' && (
        <Alert variant="danger" className="mb-4">
          <Row className="align-items-center">
            <Col>
              <i className="feather icon-alert-triangle me-2"></i>
              <strong>Critical:</strong> Reward Pool MATIC balance is critically low ({rewardPoolStatus.matic_balance} MATIC). 
              Transactions may fail!
            </Col>
            <Col xs="auto">
              <Link to="/admin/reward-pool" className="btn btn-light btn-sm">
                Manage Reward Pool
              </Link>
            </Col>
          </Row>
        </Alert>
      )}
      
      {rewardPoolStatus && rewardPoolStatus.status === 'warning' && (
        <Alert variant="warning" className="mb-4">
          <Row className="align-items-center">
            <Col>
              <i className="feather icon-alert-circle me-2"></i>
              <strong>Warning:</strong> Reward Pool MATIC balance is low ({rewardPoolStatus.matic_balance} MATIC). 
              Consider refilling soon.
            </Col>
            <Col xs="auto">
              <Link to="/admin/reward-pool" className="btn btn-light btn-sm">
                Manage Reward Pool
              </Link>
            </Col>
          </Row>
        </Alert>
      )}

      {/* Quick Actions */}
      <Row className="g-3 mb-4">
        <Col lg={12}>
          <Card>
            <Card.Header>
              <Card.Title as="h5">
                <i className="feather icon-command me-2"></i>
                Quick Actions
              </Card.Title>
            </Card.Header>
            <Card.Body>
              <Row className="g-3">
                <Col md={3} sm={6}>
                  <Link to="/admin/reward-pool" className="btn btn-outline-primary w-100 py-3">
                    <i className="feather icon-database d-block mb-2" style={{ fontSize: '1.5rem' }}></i>
                    Manage Reward Pool
                  </Link>
                </Col>
                <Col md={3} sm={6}>
                  <Button variant="outline-success" className="w-100 py-3" onClick={() => {
                    const revenueSection = document.getElementById('revenue-analytics');
                    if (revenueSection) {
                      revenueSection.scrollIntoView({ behavior: 'smooth' });
                    }
                  }}>
                    <i className="feather icon-bar-chart-2 d-block mb-2" style={{ fontSize: '1.5rem' }}></i>
                    Revenue Analytics
                  </Button>
                </Col>
                <Col md={3} sm={6}>
                  <Link to="/admin/pending-courses" className="btn btn-outline-info w-100 py-3">
                    <i className="feather icon-book-open d-block mb-2" style={{ fontSize: '1.5rem' }}></i>
                    Pending Courses
                  </Link>
                </Col>
                <Col md={3} sm={6}>
                  <Button variant="outline-warning" className="w-100 py-3">
                    <i className="feather icon-users d-block mb-2" style={{ fontSize: '1.5rem' }}></i>
                    User Management
                  </Button>
                </Col>
                <Col md={3} sm={6}>
                  <Button variant="outline-secondary" className="w-100 py-3" onClick={() => {
                    const transactionSection = document.getElementById('transaction-monitor');
                    if (transactionSection) {
                      transactionSection.scrollIntoView({ behavior: 'smooth' });
                    }
                  }}>
                    <i className="feather icon-activity d-block mb-2" style={{ fontSize: '1.5rem' }}></i>
                    Transaction Monitor
                  </Button>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Admin Actions */}
      <Row className="g-3 mb-4">
        <Col lg={6} md={12}>
          <PendingTeachersCard />
        </Col>
        <Col lg={6} md={12}>
          <PendingCoursesCard />
        </Col>
      </Row>

      {/* Approval Stats */}
      <Row className="g-3 mb-4">
        <Col lg={12}>
          <Card className="h-100">
            <Card.Header>
              <Card.Title as="h5">
                <i className="feather icon-bar-chart-2 me-2"></i>
                Statistiche Approvazioni
              </Card.Title>
            </Card.Header>
            <Card.Body className="approval-stats">
              <ApprovalStats />
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Revenue Analytics */}
      <Row className="g-3 mb-4" id="revenue-analytics">
        <Col lg={12}>
          <Card className="h-100">
            <Card.Header>
              <Card.Title as="h5">
                <i className="feather icon-trending-up me-2"></i>
                Revenue Analytics
              </Card.Title>
              <p className="text-muted mb-0 small">
                Comprehensive revenue tracking, course performance, and TEO economics
              </p>
            </Card.Header>
            <Card.Body>
              <RevenueAnalytics />
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Transaction Monitor */}
      <Row className="g-3" id="transaction-monitor">
        <Col lg={12}>
          <Card className="h-100">
            <Card.Header>
              <Card.Title as="h5">
                <i className="feather icon-activity me-2"></i>
                Monitoraggio Transazioni Blockchain
              </Card.Title>
              <p className="text-muted mb-0 small">
                Monitor delle transazioni TEO per reward, acquisti e pagamenti degli utenti
              </p>
            </Card.Header>
            <Card.Body>
              <AdminTransactionMonitor />
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* TeoCoin Dashboard and Withdrawal */}
      <Row className="mt-4">
        <Col lg={8}>
          <AdminTeoCoinDashboard />
        </Col>
        <Col lg={4}>
          <TeoCoinBalanceWidget variant="compact" />
        </Col>
      </Row>
    </div>
  );
};

export default AdminDashboard;

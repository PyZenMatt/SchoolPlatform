/**
 * Gas-Free Operations Dashboard
 * Unified interface for gas-free discount and staking operations
 */
import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Nav, Badge, Alert, Button } from 'react-bootstrap';
import GasFreeDiscountInterface from './GasFreeDiscountInterface';
import GasFreeStakingInterface from './GasFreeStakingInterface';
import './GasFreeOperationsDashboard.scss';

const GasFreeOperationsDashboard = ({ 
  userAddress,
  onConnect,
  className = ""
}) => {
  const [activeTab, setActiveTab] = useState('discounts');
  const [userStats, setUserStats] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [walletConnected, setWalletConnected] = useState(false);

  useEffect(() => {
    if (userAddress) {
      setWalletConnected(true);
      fetchUserStats();
      fetchSystemStatus();
    } else {
      setWalletConnected(false);
    }
  }, [userAddress]);

  const fetchUserStats = async () => {
    try {
      const response = await fetch(`/api/v1/services/gas-free/user-stats/${userAddress}/`, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUserStats(data.data);
      }
    } catch (error) {
      console.error('Error fetching user stats:', error);
    }
  };

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('/api/v1/services/gas-free/system-status/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSystemStatus(data.data);
      }
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  };

  const handleOperationUpdate = (data) => {
    // Refresh stats when operations complete
    setTimeout(() => {
      fetchUserStats();
    }, 2000);
  };

  const connectWallet = async () => {
    if (onConnect) {
      await onConnect();
    }
  };

  const formatCurrency = (amount) => {
    return amount ? `$${amount.toFixed(4)}` : '$0.0000';
  };

  return (
    <div className={`gas-free-operations-dashboard ${className}`}>
      <Container fluid>
        {/* Header Section */}
        <div className="dashboard-header mb-4">
          <Row className="align-items-center">
            <Col md={8}>
              <div className="header-content">
                <h2 className="dashboard-title">
                  <i className="fas fa-rocket me-3"></i>
                  Gas-Free Operations Center
                </h2>
                <p className="dashboard-subtitle">
                  Perform blockchain operations without MATIC gas fees
                </p>
              </div>
            </Col>
            <Col md={4} className="text-end">
              <div className="system-status">
                {systemStatus && (
                  <div className="status-indicators">
                    <Badge 
                      bg={systemStatus.contracts_healthy ? 'success' : 'danger'}
                      className="me-2"
                    >
                      <i className="fas fa-server me-1"></i>
                      Contracts {systemStatus.contracts_healthy ? 'Online' : 'Offline'}
                    </Badge>
                    <Badge 
                      bg={systemStatus.gas_fee_coverage ? 'success' : 'warning'}
                    >
                      <i className="fas fa-gas-pump me-1"></i>
                      Gas Coverage {systemStatus.gas_fee_coverage ? 'Active' : 'Limited'}
                    </Badge>
                  </div>
                )}
              </div>
            </Col>
          </Row>
        </div>

        {/* Wallet Connection */}
        {!walletConnected && (
          <Alert variant="warning" className="wallet-connect-alert">
            <Row className="align-items-center">
              <Col md={8}>
                <div>
                  <i className="fas fa-wallet me-2"></i>
                  <strong>Wallet Not Connected</strong>
                  <p className="mb-0 mt-1">
                    Connect your MetaMask wallet to access gas-free operations
                  </p>
                </div>
              </Col>
              <Col md={4} className="text-end">
                <Button variant="primary" onClick={connectWallet}>
                  <i className="fas fa-plug me-2"></i>
                  Connect Wallet
                </Button>
              </Col>
            </Row>
          </Alert>
        )}

        {/* User Stats Overview */}
        {walletConnected && userStats && (
          <Card className="user-stats-card mb-4">
            <Card.Body>
              <Row>
                <Col md={3}>
                  <div className="stat-item">
                    <div className="stat-icon">
                      <i className="fas fa-percentage"></i>
                    </div>
                    <div className="stat-content">
                      <div className="stat-value">{userStats.total_discounts || 0}</div>
                      <div className="stat-label">Total Discounts</div>
                    </div>
                  </div>
                </Col>
                <Col md={3}>
                  <div className="stat-item">
                    <div className="stat-icon">
                      <i className="fas fa-coins"></i>
                    </div>
                    <div className="stat-content">
                      <div className="stat-value">{userStats.staked_amount?.toLocaleString() || 0}</div>
                      <div className="stat-label">TEO Staked</div>
                    </div>
                  </div>
                </Col>
                <Col md={3}>
                  <div className="stat-item">
                    <div className="stat-icon">
                      <i className="fas fa-gas-pump"></i>
                    </div>
                    <div className="stat-content">
                      <div className="stat-value">{formatCurrency(userStats.gas_saved)}</div>
                      <div className="stat-label">Gas Saved</div>
                    </div>
                  </div>
                </Col>
                <Col md={3}>
                  <div className="stat-item">
                    <div className="stat-icon">
                      <i className="fas fa-trophy"></i>
                    </div>
                    <div className="stat-content">
                      <div className="stat-value">{userStats.current_tier || 'Bronze'}</div>
                      <div className="stat-label">Current Tier</div>
                    </div>
                  </div>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        )}

        {/* Navigation Tabs */}
        <Card className="operations-card">
          <Card.Header className="operations-header">
            <Nav variant="tabs" className="operation-tabs">
              <Nav.Item>
                <Nav.Link
                  active={activeTab === 'discounts'}
                  onClick={() => setActiveTab('discounts')}
                  className="operation-tab"
                >
                  <i className="fas fa-percentage me-2"></i>
                  Discount Requests
                  <Badge bg="secondary" className="ms-2">Gas-Free</Badge>
                </Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link
                  active={activeTab === 'staking'}
                  onClick={() => setActiveTab('staking')}
                  className="operation-tab"
                >
                  <i className="fas fa-coins me-2"></i>
                  TEO Staking
                  <Badge bg="secondary" className="ms-2">Gas-Free</Badge>
                </Nav.Link>
              </Nav.Item>
            </Nav>
          </Card.Header>

          <Card.Body className="operations-body">
            {/* Discount Operations Tab */}
            {activeTab === 'discounts' && (
              <div className="operation-content">
                <div className="operation-description mb-4">
                  <h5>
                    <i className="fas fa-info-circle me-2 text-info"></i>
                    Gas-Free Discount Requests
                  </h5>
                  <p className="text-muted">
                    Request discounts from teachers without paying MATIC gas fees. 
                    The platform covers all blockchain transaction costs.
                  </p>
                </div>
                
                <GasFreeDiscountInterface
                  userAddress={userAddress}
                  onDiscountUpdate={handleOperationUpdate}
                  className="operation-interface"
                />
              </div>
            )}

            {/* Staking Operations Tab */}
            {activeTab === 'staking' && (
              <div className="operation-content">
                <div className="operation-description mb-4">
                  <h5>
                    <i className="fas fa-info-circle me-2 text-info"></i>
                    Gas-Free TEO Staking
                  </h5>
                  <p className="text-muted">
                    Stake your TEO tokens to earn higher commission rates without 
                    paying MATIC gas fees. All blockchain costs are covered by the platform.
                  </p>
                </div>
                
                <GasFreeStakingInterface
                  userAddress={userAddress}
                  onStakingUpdate={handleOperationUpdate}
                  className="operation-interface"
                />
              </div>
            )}
          </Card.Body>
        </Card>

        {/* System Information */}
        {systemStatus && (
          <Card className="system-info-card mt-4">
            <Card.Body>
              <Row>
                <Col md={6}>
                  <h6 className="text-muted mb-3">
                    <i className="fas fa-info-circle me-2"></i>
                    System Information
                  </h6>
                  <div className="info-list">
                    <div className="info-item">
                      <span className="info-label">Network:</span>
                      <span className="info-value">Polygon Amoy Testnet</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Gas Coverage:</span>
                      <span className="info-value">
                        Platform Funded
                        <Badge bg="success" className="ms-2">Active</Badge>
                      </span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Average Gas Cost:</span>
                      <span className="info-value">{formatCurrency(systemStatus.avg_gas_cost)} per operation</span>
                    </div>
                  </div>
                </Col>
                <Col md={6}>
                  <h6 className="text-muted mb-3">
                    <i className="fas fa-chart-line me-2"></i>
                    Platform Statistics
                  </h6>
                  <div className="info-list">
                    <div className="info-item">
                      <span className="info-label">Total Operations:</span>
                      <span className="info-value">{systemStatus.total_operations?.toLocaleString() || 0}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Gas Fees Covered:</span>
                      <span className="info-value">{formatCurrency(systemStatus.total_gas_covered)}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Active Users:</span>
                      <span className="info-value">{systemStatus.active_users?.toLocaleString() || 0}</span>
                    </div>
                  </div>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        )}
      </Container>
    </div>
  );
};

export default GasFreeOperationsDashboard;

/**
 * Gas-Free System Status Component
 * Shows platform statistics, student allowances, and system health
 */

import React, { useState, useEffect } from 'react';
import { Card, Badge, Alert, Row, Col, ProgressBar, Spinner } from 'react-bootstrap';
import { getPlatformStats, getStudentAllowance } from '../services/api/gasFreeV2';
import web3Provider from '../services/web3ProviderService';

const GasFreeSystemStatus = ({ userRole, walletAddress }) => {
    const [systemStats, setSystemStats] = useState(null);
    const [studentAllowance, setStudentAllowance] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        checkConnection();
        loadSystemData();
    }, [walletAddress, userRole]);

    const checkConnection = async () => {
        const connected = await web3Provider.isConnected();
        setIsConnected(connected);
    };

    const loadSystemData = async () => {
        setLoading(true);
        setError(null);

        try {
            // Load platform statistics for all users
            const statsData = await getPlatformStats();
            setSystemStats(statsData);

            // Load student allowance if user is a student and has wallet
            if (userRole === 'student' && walletAddress) {
                try {
                    const allowanceData = await getStudentAllowance(walletAddress);
                    setStudentAllowance(allowanceData);
                } catch (allowanceError) {
                    console.warn('Could not load student allowance:', allowanceError.message);
                    // Don't fail the whole component for allowance errors
                }
            }

        } catch (error) {
            console.error('Error loading gas-free system data:', error);
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    const connectWallet = async () => {
        try {
            await web3Provider.connectMetaMask();
            await checkConnection();
            await loadSystemData();
        } catch (error) {
            setError(error.message);
        }
    };

    if (loading) {
        return (
            <Card className="gas-free-status">
                <Card.Body className="text-center">
                    <Spinner animation="border" />
                    <p className="mt-2">Loading Gas-Free System Status...</p>
                </Card.Body>
            </Card>
        );
    }

    return (
        <div className="gas-free-system-status">
            {/* System Health Status */}
            <Card className="mb-3">
                <Card.Header>
                    <h5>
                        ⛽ Gas-Free System Status
                        <Badge 
                            bg={systemStats?.platform_operational ? 'success' : 'danger'} 
                            className="ms-2"
                        >
                            {systemStats?.platform_operational ? 'Operational' : 'Issues Detected'}
                        </Badge>
                    </h5>
                </Card.Header>
                <Card.Body>
                    {error && (
                        <Alert variant="danger">
                            <strong>Error:</strong> {error}
                        </Alert>
                    )}

                    <Row>
                        <Col md={6}>
                            <div className="status-item mb-3">
                                <h6>💰 Platform MATIC Balance</h6>
                                <div className="d-flex justify-content-between">
                                    <span>{systemStats?.platform_balance || '0.0000'} MATIC</span>
                                    <Badge bg={
                                        parseFloat(systemStats?.platform_balance || 0) > 1 ? 'success' : 
                                        parseFloat(systemStats?.platform_balance || 0) > 0.1 ? 'warning' : 'danger'
                                    }>
                                        {parseFloat(systemStats?.platform_balance || 0) > 1 ? 'Good' : 
                                         parseFloat(systemStats?.platform_balance || 0) > 0.1 ? 'Low' : 'Critical'}
                                    </Badge>
                                </div>
                                <ProgressBar 
                                    variant={
                                        parseFloat(systemStats?.platform_balance || 0) > 1 ? 'success' : 
                                        parseFloat(systemStats?.platform_balance || 0) > 0.1 ? 'warning' : 'danger'
                                    }
                                    now={Math.min(parseFloat(systemStats?.platform_balance || 0) * 50, 100)} 
                                    className="mt-1"
                                />
                            </div>
                        </Col>
                        <Col md={6}>
                            <div className="status-item mb-3">
                                <h6>📊 Today's Operations</h6>
                                <div className="operation-stats">
                                    <div>Discounts: <strong>{systemStats?.today_discounts || 0}</strong></div>
                                    <div>Staking Ops: <strong>{systemStats?.today_staking || 0}</strong></div>
                                    <div>Gas Cost: <strong>${systemStats?.today_gas_cost || '0.00'}</strong></div>
                                </div>
                            </div>
                        </Col>
                    </Row>

                    {/* Contract Addresses */}
                    <Row>
                        <Col>
                            <div className="contract-info">
                                <h6>📋 Contract Addresses</h6>
                                <div className="contract-list">
                                    <div>
                                        <small>Discount Contract:</small>
                                        <code>{process.env.REACT_APP_DISCOUNT_CONTRACT_V2_ADDRESS}</code>
                                    </div>
                                    <div>
                                        <small>Staking Contract:</small>
                                        <code>{process.env.REACT_APP_STAKING_CONTRACT_V2_ADDRESS}</code>
                                    </div>
                                    <div>
                                        <small>TEO Token:</small>
                                        <code>{process.env.REACT_APP_TEO_TOKEN_ADDRESS}</code>
                                    </div>
                                </div>
                            </div>
                        </Col>
                    </Row>
                </Card.Body>
            </Card>

            {/* Student-Specific Information */}
            {userRole === 'student' && (
                <Card className="mb-3">
                    <Card.Header>
                        <h5>🎓 Student Gas-Free Account</h5>
                    </Card.Header>
                    <Card.Body>
                        {!isConnected ? (
                            <div className="text-center">
                                <p>Connect your wallet to view your gas-free allowance</p>
                                <button 
                                    className="btn btn-primary"
                                    onClick={connectWallet}
                                >
                                    Connect MetaMask
                                </button>
                            </div>
                        ) : walletAddress ? (
                            <div>
                                <div className="wallet-info mb-3">
                                    <h6>👛 Connected Wallet</h6>
                                    <code>{walletAddress}</code>
                                </div>

                                {studentAllowance ? (
                                    <div className="allowance-info">
                                        <h6>💳 Platform Allowance</h6>
                                        <Row>
                                            <Col md={4}>
                                                <div className="allowance-stat">
                                                    <div className="stat-value">{studentAllowance.remaining_allowance || 0}</div>
                                                    <div className="stat-label">TEO Available</div>
                                                </div>
                                            </Col>
                                            <Col md={4}>
                                                <div className="allowance-stat">
                                                    <div className="stat-value">{studentAllowance.used_allowance || 0}</div>
                                                    <div className="stat-label">TEO Used</div>
                                                </div>
                                            </Col>
                                            <Col md={4}>
                                                <div className="allowance-stat">
                                                    <div className="stat-value">{studentAllowance.total_allowance || 0}</div>
                                                    <div className="stat-label">Total Allowance</div>
                                                </div>
                                            </Col>
                                        </Row>
                                        <ProgressBar 
                                            variant="info"
                                            now={(studentAllowance.used_allowance / studentAllowance.total_allowance) * 100} 
                                            label={`${Math.round((studentAllowance.used_allowance / studentAllowance.total_allowance) * 100)}% used`}
                                            className="mt-2"
                                        />
                                        
                                        {studentAllowance.remaining_allowance < 10 && (
                                            <Alert variant="warning" className="mt-2">
                                                <strong>Low Allowance:</strong> You have less than 10 TEO remaining. 
                                                Contact support if you need more allowance.
                                            </Alert>
                                        )}
                                    </div>
                                ) : (
                                    <Alert variant="info">
                                        No gas-free allowance found for this wallet. 
                                        You may need to register for the gas-free system.
                                    </Alert>
                                )}
                            </div>
                        ) : (
                            <Alert variant="warning">
                                Please connect your wallet to view gas-free account details.
                            </Alert>
                        )}
                    </Card.Body>
                </Card>
            )}

            {/* Teacher-Specific Information */}
            {userRole === 'teacher' && (
                <Card className="mb-3">
                    <Card.Header>
                        <h5>👨‍🏫 Teacher Gas-Free Benefits</h5>
                    </Card.Header>
                    <Card.Body>
                        <Alert variant="success">
                            <strong>Zero Gas Fees:</strong> All your staking operations are completely free! 
                            The platform pays all MATIC gas fees for you.
                        </Alert>
                        
                        <div className="teacher-benefits">
                            <h6>✨ Benefits</h6>
                            <ul>
                                <li>🚀 Zero-MATIC staking and unstaking</li>
                                <li>📈 5-tier commission system (Bronze 25% → Diamond 15%)</li>
                                <li>⚡ Instant tier updates with gas-free transactions</li>
                                <li>💰 Keep 100% of your staking rewards</li>
                            </ul>
                        </div>
                    </Card.Body>
                </Card>
            )}

            {/* System Performance Metrics */}
            <Card>
                <Card.Header>
                    <h5>📈 System Performance</h5>
                </Card.Header>
                <Card.Body>
                    <Row>
                        <Col md={3}>
                            <div className="metric">
                                <div className="metric-value">{systemStats?.total_transactions || 0}</div>
                                <div className="metric-label">Total Transactions</div>
                            </div>
                        </Col>
                        <Col md={3}>
                            <div className="metric">
                                <div className="metric-value">{systemStats?.total_gas_saved || '0.0000'}</div>
                                <div className="metric-label">MATIC Saved for Users</div>
                            </div>
                        </Col>
                        <Col md={3}>
                            <div className="metric">
                                <div className="metric-value">{systemStats?.active_students || 0}</div>
                                <div className="metric-label">Active Students</div>
                            </div>
                        </Col>
                        <Col md={3}>
                            <div className="metric">
                                <div className="metric-value">{systemStats?.active_teachers || 0}</div>
                                <div className="metric-label">Active Teachers</div>
                            </div>
                        </Col>
                    </Row>
                </Card.Body>
            </Card>
        </div>
    );
};

export default GasFreeSystemStatus;

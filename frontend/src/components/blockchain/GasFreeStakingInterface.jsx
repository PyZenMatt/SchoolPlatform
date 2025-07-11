/**
 * Gas-Free Staking Interface
 * Allows users to stake/unstake TEO tokens without MATIC gas fees
 */
import React, { useState, useEffect } from 'react';
import { Card, Button, Alert, Form, Badge, Spinner, Row, Col, ProgressBar } from 'react-bootstrap';
import { ethers } from 'ethers';
import './GasFreeStakingInterface.scss';

const GasFreeStakingInterface = ({ 
  userAddress, 
  onStakingUpdate,
  className = ""
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [stakeAmount, setStakeAmount] = useState(1000);
  const [unstakeAmount, setUnstakeAmount] = useState(500);
  const [activeTab, setActiveTab] = useState('stake');
  const [stakingInfo, setStakingInfo] = useState(null);
  const [gasCostEstimate, setGasCostEstimate] = useState(null);
  const [walletConnected, setWalletConnected] = useState(false);

  // Tier information
  const tiers = [
    { name: 'Bronze', min: 0, max: 999, commission: 2.5, color: '#cd7f32' },
    { name: 'Silver', min: 1000, max: 4999, commission: 5.0, color: '#c0c0c0' },
    { name: 'Gold', min: 5000, max: 9999, commission: 7.5, color: '#ffd700' },
    { name: 'Platinum', min: 10000, max: 24999, commission: 10.0, color: '#e5e4e2' },
    { name: 'Diamond', min: 25000, max: Infinity, commission: 15.0, color: '#b9f2ff' }
  ];

  useEffect(() => {
    if (userAddress) {
      checkWalletConnection();
      fetchStakingInfo();
      fetchGasCostEstimate();
    }
  }, [userAddress]);

  const checkWalletConnection = async () => {
    try {
      if (window.ethereum && userAddress) {
        setWalletConnected(true);
      }
    } catch (error) {
      console.error('Error checking wallet connection:', error);
    }
  };

  const fetchStakingInfo = async () => {
    try {
      const response = await fetch(`/api/v1/services/gas-free/staking/info/${userAddress}/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setStakingInfo(data.data);
      }
    } catch (error) {
      console.error('Error fetching staking info:', error);
    }
  };

  const fetchGasCostEstimate = async () => {
    try {
      const response = await fetch('/api/v1/services/gas-free/gas-estimates/', {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setGasCostEstimate(data.data.staking_operations);
      }
    } catch (error) {
      console.error('Error fetching gas estimates:', error);
    }
  };

  const getCurrentTier = (stakedAmount) => {
    return tiers.find(tier => stakedAmount >= tier.min && stakedAmount <= tier.max) || tiers[0];
  };

  const getNextTier = (stakedAmount) => {
    const currentTierIndex = tiers.findIndex(tier => stakedAmount >= tier.min && stakedAmount <= tier.max);
    return currentTierIndex < tiers.length - 1 ? tiers[currentTierIndex + 1] : null;
  };

  const createStakeSignature = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v1/services/gas-free/staking/stake-signature/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_address: userAddress,
          teo_amount: stakeAmount
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create stake signature');
      }

      const signatureResponse = await response.json();
      await requestUserSignature(signatureResponse.data, 'stake');
      
    } catch (error) {
      console.error('Error creating stake signature:', error);
      setError(error.message);
      setIsLoading(false);
    }
  };

  const createUnstakeSignature = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v1/services/gas-free/staking/unstake-signature/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_address: userAddress,
          teo_amount: unstakeAmount
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create unstake signature');
      }

      const signatureResponse = await response.json();
      await requestUserSignature(signatureResponse.data, 'unstake');
      
    } catch (error) {
      console.error('Error creating unstake signature:', error);
      setError(error.message);
      setIsLoading(false);
    }
  };

  const requestUserSignature = async (signatureInfo, action) => {
    try {
      if (!window.ethereum) {
        throw new Error('MetaMask not found. Please install MetaMask.');
      }

      const provider = new ethers.BrowserProvider(window.ethereum);
      const signer = await provider.getSigner();
      
      const signature = await signer.signMessage(ethers.getBytes(signatureInfo.message_hash));
      
      await executeStakingRequest(signatureInfo, signature, action);
      
    } catch (error) {
      if (error.code === 4001) {
        setError('Transaction cancelled by user');
      } else {
        console.error('Error requesting signature:', error);
        setError('Failed to sign message: ' + error.message);
      }
      setIsLoading(false);
    }
  };

  const executeStakingRequest = async (signatureInfo, signature, action) => {
    try {
      const endpoint = action === 'stake' ? 'stake' : 'unstake';
      const response = await fetch(`/api/v1/services/gas-free/staking/${endpoint}/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_address: signatureInfo.user_address,
          signature: signature,
          teo_amount: signatureInfo.teo_amount,
          nonce: signatureInfo.nonce
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Failed to execute ${action} request`);
      }

      const result = await response.json();
      
      // Handle response structure - V2 API returns data directly  
      const responseData = result.data || result; // Fallback for different response structures
      
      setSuccess({
        message: `${action.charAt(0).toUpperCase() + action.slice(1)} completed successfully!`,
        transactionHash: responseData.transaction_hash || result.transaction_hash || 'processing',
        action: action,
        amount: responseData.teo_amount || result.teo_amount || amount,
        gasCost: responseData.gas_cost || result.gas_cost || '0.00'
      });
      
      // Refresh staking info
      setTimeout(() => {
        fetchStakingInfo();
      }, 2000);
      
      if (onStakingUpdate) {
        onStakingUpdate(result.data);
      }
      
    } catch (error) {
      console.error(`Error executing ${action} request:`, error);
      setError(`Failed to execute ${action} request: ` + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const formatGasCost = (costInWei) => {
    if (!costInWei) return 'N/A';
    const costInEther = ethers.formatEther(costInWei.toString());
    const costInUSD = parseFloat(costInEther) * 0.5;
    return `$${costInUSD.toFixed(4)} USD`;
  };

  const currentTier = stakingInfo ? getCurrentTier(stakingInfo.staked_amount) : tiers[0];
  const nextTier = stakingInfo ? getNextTier(stakingInfo.staked_amount) : tiers[1];
  const progressToNextTier = nextTier ? 
    ((stakingInfo?.staked_amount || 0) - currentTier.min) / (nextTier.min - currentTier.min) * 100 : 100;

  return (
    <Card className={`gas-free-staking-interface ${className}`}>
      <Card.Header className="bg-gradient-primary text-white">
        <div className="d-flex justify-content-between align-items-center">
          <h5 className="mb-0">
            <i className="fas fa-coins me-2"></i>
            Gas-Free TEO Staking
          </h5>
          <Badge bg="success">No MATIC Required</Badge>
        </div>
      </Card.Header>
      
      <Card.Body>
        {/* Current Staking Info */}
        {stakingInfo && (
          <div className="staking-overview mb-4">
            <Row>
              <Col md={4}>
                <div className="stat-card">
                  <div className="stat-label">Staked Amount</div>
                  <div className="stat-value">{stakingInfo.staked_amount.toLocaleString()} TEO</div>
                </div>
              </Col>
              <Col md={4}>
                <div className="stat-card">
                  <div className="stat-label">Current Tier</div>
                  <div className="stat-value" style={{ color: currentTier.color }}>
                    {currentTier.name}
                  </div>
                </div>
              </Col>
              <Col md={4}>
                <div className="stat-card">
                  <div className="stat-label">Commission Rate</div>
                  <div className="stat-value">{currentTier.commission}%</div>
                </div>
              </Col>
            </Row>
            
            {/* Progress to Next Tier */}
            {nextTier && (
              <div className="tier-progress mt-3">
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="small">Progress to {nextTier.name} Tier</span>
                  <span className="small">{Math.round(progressToNextTier)}%</span>
                </div>
                <ProgressBar 
                  now={progressToNextTier} 
                  variant="info"
                  className="tier-progress-bar"
                />
                <div className="small text-muted mt-1">
                  Need {nextTier.min - stakingInfo.staked_amount} more TEO to reach {nextTier.name} tier
                </div>
              </div>
            )}
          </div>
        )}

        {/* Action Tabs */}
        <div className="action-tabs mb-3">
          <div className="btn-group w-100" role="group">
            <Button
              variant={activeTab === 'stake' ? 'primary' : 'outline-primary'}
              onClick={() => setActiveTab('stake')}
              className="flex-fill"
            >
              <i className="fas fa-plus me-2"></i>Stake TEO
            </Button>
            <Button
              variant={activeTab === 'unstake' ? 'primary' : 'outline-primary'}
              onClick={() => setActiveTab('unstake')}
              className="flex-fill"
              disabled={!stakingInfo?.staked_amount}
            >
              <i className="fas fa-minus me-2"></i>Unstake TEO
            </Button>
          </div>
        </div>

        {/* Stake Form */}
        {activeTab === 'stake' && (
          <div className="stake-form">
            <Form.Group className="mb-3">
              <Form.Label>Amount to Stake</Form.Label>
              <div className="input-group">
                <Form.Control
                  type="number"
                  value={stakeAmount}
                  onChange={(e) => setStakeAmount(parseInt(e.target.value) || 0)}
                  min="1"
                  max="100000"
                  disabled={isLoading}
                />
                <span className="input-group-text">TEO</span>
              </div>
              <Form.Text className="text-muted">
                Minimum: 1 TEO | Recommended: 1,000+ TEO for better tier
              </Form.Text>
            </Form.Group>

            {gasCostEstimate && (
              <Alert variant="info" className="mb-3">
                <div className="d-flex justify-content-between align-items-center">
                  <span>
                    <i className="fas fa-info-circle me-2"></i>
                    Platform Gas Cost:
                  </span>
                  <Badge bg="info">
                    ${gasCostEstimate.stake_operation?.cost_usd?.toFixed(4) || '0.003'} USD
                  </Badge>
                </div>
              </Alert>
            )}

            <Button
              variant="success"
              size="lg"
              onClick={createStakeSignature}
              disabled={isLoading || !walletConnected || !stakeAmount}
              className="w-100 gas-free-btn"
            >
              {isLoading && activeTab === 'stake' ? (
                <>
                  <Spinner animation="border" size="sm" className="me-2" />
                  Staking...
                </>
              ) : (
                <>
                  <i className="fas fa-signature me-2"></i>
                  Stake {stakeAmount} TEO (Gas-Free)
                </>
              )}
            </Button>
          </div>
        )}

        {/* Unstake Form */}
        {activeTab === 'unstake' && (
          <div className="unstake-form">
            <Form.Group className="mb-3">
              <Form.Label>Amount to Unstake</Form.Label>
              <div className="input-group">
                <Form.Control
                  type="number"
                  value={unstakeAmount}
                  onChange={(e) => setUnstakeAmount(parseInt(e.target.value) || 0)}
                  min="1"
                  max={stakingInfo?.staked_amount || 0}
                  disabled={isLoading}
                />
                <span className="input-group-text">TEO</span>
              </div>
              <Form.Text className="text-muted">
                Available: {stakingInfo?.staked_amount?.toLocaleString() || 0} TEO
              </Form.Text>
            </Form.Group>

            {gasCostEstimate && (
              <Alert variant="info" className="mb-3">
                <div className="d-flex justify-content-between align-items-center">
                  <span>
                    <i className="fas fa-info-circle me-2"></i>
                    Platform Gas Cost:
                  </span>
                  <Badge bg="info">
                    ${gasCostEstimate.unstake_operation?.cost_usd?.toFixed(4) || '0.002'} USD
                  </Badge>
                </div>
              </Alert>
            )}

            <Button
              variant="warning"
              size="lg"
              onClick={createUnstakeSignature}
              disabled={isLoading || !walletConnected || !unstakeAmount}
              className="w-100 gas-free-btn"
            >
              {isLoading && activeTab === 'unstake' ? (
                <>
                  <Spinner animation="border" size="sm" className="me-2" />
                  Unstaking...
                </>
              ) : (
                <>
                  <i className="fas fa-signature me-2"></i>
                  Unstake {unstakeAmount} TEO (Gas-Free)
                </>
              )}
            </Button>
          </div>
        )}

        {/* Wallet Connection Warning */}
        {!walletConnected && (
          <Alert variant="warning" className="mb-3">
            <i className="fas fa-wallet me-2"></i>
            Please connect your wallet to continue
          </Alert>
        )}

        {/* Error Display */}
        {error && (
          <Alert variant="danger" className="mb-3">
            <i className="fas fa-exclamation-triangle me-2"></i>
            {error}
          </Alert>
        )}

        {/* Success Display */}
        {success && (
          <Alert variant="success" className="mb-3">
            <div className="d-flex flex-column">
              <div>
                <i className="fas fa-check-circle me-2"></i>
                {success.message}
              </div>
              <small className="text-muted mt-1">
                Amount: {success.amount} TEO
              </small>
              {success.transactionHash && (
                <small className="text-muted">
                  <a 
                    href={`https://amoy.polygonscan.com/tx/${success.transactionHash}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-decoration-none"
                  >
                    View on PolygonScan <i className="fas fa-external-link-alt"></i>
                  </a>
                </small>
              )}
              {success.gasCost && (
                <small className="text-muted">
                  Platform Gas Cost: {formatGasCost(success.gasCost)}
                </small>
              )}
            </div>
          </Alert>
        )}

        {/* Staking Benefits */}
        <div className="staking-benefits mt-4">
          <h6 className="text-muted mb-3">
            <i className="fas fa-star me-2"></i>Staking Benefits
          </h6>
          <Row>
            {tiers.map((tier, index) => (
              <Col md={6} lg={4} key={index} className="mb-2">
                <div className={`tier-card ${currentTier.name === tier.name ? 'active' : ''}`}>
                  <div className="tier-name" style={{ color: tier.color }}>
                    {tier.name}
                  </div>
                  <div className="tier-amount">
                    {tier.min.toLocaleString()}+ TEO
                  </div>
                  <div className="tier-commission">
                    {tier.commission}% Commission
                  </div>
                </div>
              </Col>
            ))}
          </Row>
        </div>
      </Card.Body>
    </Card>
  );
};

export default GasFreeStakingInterface;

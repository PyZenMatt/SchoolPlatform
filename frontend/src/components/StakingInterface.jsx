import React, { useState, useEffect } from 'react';
import {
  Card,
  Badge,
  Button,
  Form,
  Alert,
  Spinner,
  ProgressBar,
  Table
} from 'react-bootstrap';
import { useAuth } from '../contexts/AuthContext';
import { stakingService } from '../services/stakingService';
import './StakingInterface.scss';

const StakingInterface = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stakingData, setStakingData] = useState(null);
  const [platformStats, setPlatformStats] = useState(null);
  const [tierConfig, setTierConfig] = useState(null);
  const [stakeAmount, setStakeAmount] = useState('');
  const [unstakeAmount, setUnstakeAmount] = useState('');
  const [isStaking, setIsStaking] = useState(false);
  const [isUnstaking, setIsUnstaking] = useState(false);
  const [alert, setAlert] = useState(null);

  useEffect(() => {
    fetchStakingData();
  }, []);

  const fetchStakingData = async () => {
    try {
      setLoading(true);
      const response = await stakingService.getStakingInfo();
      setStakingData(response.user_staking);
      setPlatformStats(response.platform_stats);
      setTierConfig(response.tier_config);
    } catch (error) {
      setAlert({ type: 'error', message: 'Failed to fetch staking data' });
    } finally {
      setLoading(false);
    }
  };

  const handleStake = async () => {
    if (!stakeAmount || parseFloat(stakeAmount) <= 0) {
      setAlert({ type: 'error', message: 'Please enter a valid amount' });
      return;
    }

    try {
      setIsStaking(true);
      const response = await stakingService.stakeTokens(parseFloat(stakeAmount));
      
      if (response.success) {
        setAlert({ 
          type: 'success', 
          message: `Successfully staked ${stakeAmount} TEO! New tier: ${getTierName(response.new_tier)}` 
        });
        setStakeAmount('');
        fetchStakingData();
      } else {
        setAlert({ type: 'error', message: response.error });
      }
    } catch (error) {
      setAlert({ type: 'error', message: 'Failed to stake tokens' });
    } finally {
      setIsStaking(false);
    }
  };

  const handleUnstake = async () => {
    if (!unstakeAmount || parseFloat(unstakeAmount) <= 0) {
      setAlert({ type: 'error', message: 'Please enter a valid amount' });
      return;
    }

    try {
      setIsUnstaking(true);
      const response = await stakingService.unstakeTokens(parseFloat(unstakeAmount));
      
      if (response.success) {
        setAlert({ 
          type: 'success', 
          message: `Successfully unstaked ${unstakeAmount} TEO!` 
        });
        setUnstakeAmount('');
        fetchStakingData();
      } else {
        setAlert({ type: 'error', message: response.error });
      }
    } catch (error) {
      setAlert({ type: 'error', message: 'Failed to unstake tokens' });
    } finally {
      setIsUnstaking(false);
    }
  };

  const getTierName = (tierIndex) => {
    return tierConfig?.[tierIndex]?.name || 'Unknown';
  };

  const getTierColor = (tierIndex) => {
    const colors = ['secondary', 'info', 'warning', 'primary', 'success'];
    return colors[tierIndex] || 'secondary';
  };

  const calculateProgress = (currentStake, targetTier) => {
    if (!tierConfig || targetTier >= 4) return 100;
    
    const currentTierMin = tierConfig[targetTier - 1]?.min_stake || 0;
    const nextTierMin = tierConfig[targetTier]?.min_stake || 0;
    
    if (nextTierMin === currentTierMin) return 100;
    
    const progress = ((currentStake - currentTierMin) / (nextTierMin - currentTierMin)) * 100;
    return Math.min(Math.max(progress, 0), 100);
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center p-4">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading staking data...</span>
        </Spinner>
      </div>
    );
  }

  return (
    <div className="staking-interface p-4">
      {alert && (
        <Alert 
          variant={alert.type === 'error' ? 'danger' : 'success'}
          onClose={() => setAlert(null)}
          dismissible
          className="mb-4"
        >
          {alert.message}
        </Alert>
      )}

      {/* Current Staking Status */}
      <Card className="mb-4">
        <Card.Header>
          <h3>Your Staking Status</h3>
        </Card.Header>
        <Card.Body>
          <div className="row">
            <div className="col-md-4 text-center">
              <h2 className="text-primary">
                {stakingData?.staked_amount?.toFixed(2) || '0.00'} TEO
              </h2>
              <small className="text-muted">Staked Amount</small>
            </div>
            
            <div className="col-md-4 text-center">
              <Badge bg={getTierColor(stakingData?.tier)} className="fs-6">
                {stakingData?.tier_name || 'Bronze'}
              </Badge>
              <div><small className="text-muted">Current Tier</small></div>
            </div>
            
            <div className="col-md-4 text-center">
              <h2 className="text-success">
                {stakingData?.commission_percentage?.toFixed(1) || '25.0'}%
              </h2>
              <small className="text-muted">Commission Rate</small>
            </div>
          </div>

          {/* Progress to Next Tier */}
          {stakingData?.tier < 4 && (
            <div className="mt-4">
              <div className="d-flex justify-content-between mb-2">
                <span>Progress to {getTierName(stakingData.tier + 1)}</span>
                <span>
                  {tierConfig?.[stakingData.tier + 1]?.min_stake - stakingData.staked_amount} TEO needed
                </span>
              </div>
              <ProgressBar 
                now={calculateProgress(stakingData.staked_amount, stakingData.tier + 1)}
                variant="primary"
                className="mb-2"
              />
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Staking Actions */}
      <div className="row mb-4">
        {/* Stake Tokens */}
        <div className="col-md-6">
          <Card>
            <Card.Header>
              <h4>Stake TEO Tokens</h4>
            </Card.Header>
            <Card.Body>
              <Form.Group className="mb-3">
                <Form.Label>Amount to Stake</Form.Label>
                <Form.Control
                  type="number"
                  placeholder="Enter TEO amount"
                  value={stakeAmount}
                  onChange={(e) => setStakeAmount(e.target.value)}
                  min="0"
                  step="0.01"
                />
              </Form.Group>
              <Button
                variant="primary"
                onClick={handleStake}
                disabled={isStaking || !stakeAmount}
                className="w-100"
              >
                {isStaking ? (
                  <>
                    <Spinner
                      as="span"
                      animation="border"
                      size="sm"
                      role="status"
                      aria-hidden="true"
                      className="me-2"
                    />
                    Staking...
                  </>
                ) : (
                  'Stake Tokens'
                )}
              </Button>
            </Card.Body>
          </Card>
        </div>

        {/* Unstake Tokens */}
        <div className="col-md-6">
          <Card>
            <Card.Header>
              <h4>Unstake TEO Tokens</h4>
            </Card.Header>
            <Card.Body>
              <Form.Group className="mb-3">
                <Form.Label>Amount to Unstake</Form.Label>
                <Form.Control
                  type="number"
                  placeholder="Enter TEO amount"
                  value={unstakeAmount}
                  onChange={(e) => setUnstakeAmount(e.target.value)}
                  min="0"
                  max={stakingData?.staked_amount || 0}
                  step="0.01"
                />
              </Form.Group>
              <Button
                variant="secondary"
                onClick={handleUnstake}
                disabled={isUnstaking || !unstakeAmount || !stakingData?.active}
                className="w-100"
              >
                {isUnstaking ? (
                  <>
                    <Spinner
                      as="span"
                      animation="border"
                      size="sm"
                      role="status"
                      aria-hidden="true"
                      className="me-2"
                    />
                    Unstaking...
                  </>
                ) : (
                  'Unstake Tokens'
                )}
              </Button>
            </Card.Body>
          </Card>
        </div>
      </div>

      {/* Tier Information */}
      <Card className="mb-4">
        <Card.Header>
          <h4>Staking Tiers & Benefits</h4>
        </Card.Header>
        <Card.Body>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>Tier</th>
                <th>Required TEO</th>
                <th>Commission Rate</th>
                <th>Benefits</th>
              </tr>
            </thead>
            <tbody>
              {tierConfig && Object.entries(tierConfig).map(([tier, config]) => (
                <tr key={tier}>
                  <td>
                    <Badge 
                      bg={getTierColor(parseInt(tier))} 
                      className={stakingData?.tier === parseInt(tier) ? "fw-bold" : ""}
                    >
                      {config.name}
                    </Badge>
                  </td>
                  <td>{config.min_stake} TEO</td>
                  <td>{(config.commission_rate / 100).toFixed(1)}%</td>
                  <td>
                    {config.commission_rate === 1500 ? 'Maximum savings' : 
                     `Save ${((2500 - config.commission_rate) / 100).toFixed(1)}% vs Bronze`}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      {/* Platform Statistics */}
      <Card>
        <Card.Header>
          <h4>Platform Statistics</h4>
        </Card.Header>
        <Card.Body>
          <div className="row text-center">
            <div className="col-md-3 col-6">
              <h3 className="text-primary">
                {platformStats?.total_staked?.toFixed(0) || '0'}
              </h3>
              <small className="text-muted">Total Staked TEO</small>
            </div>
            <div className="col-md-3 col-6">
              <h3 className="text-secondary">
                {platformStats?.total_stakers || '0'}
              </h3>
              <small className="text-muted">Total Stakers</small>
            </div>
            <div className="col-md-3 col-6">
              <h3 className="text-warning">
                {platformStats?.average_stake?.toFixed(1) || '0.0'}
              </h3>
              <small className="text-muted">Average Stake</small>
            </div>
            <div className="col-md-3 col-6">
              <h3 className="text-success">
                {platformStats?.utilization_percentage?.toFixed(1) || '0.0'}%
              </h3>
              <small className="text-muted">Supply Staked</small>
            </div>
          </div>
        </Card.Body>
      </Card>
    </div>
  );
};

export default StakingInterface;

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardBody,
  CardHeader,
  Badge,
  Button,
  Input,
  Alert,
  Spinner,
  Progress,
  Table,
  TableHeader,
  TableBody,
  TableColumn,
  TableRow,
  TableCell
} from '@nextui-org/react';
import { useAuth } from '../../contexts/AuthContext';
import { stakingService } from '../../services/stakingService';
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
    const colors = ['secondary', 'default', 'warning', 'primary', 'success'];
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
      <div className="flex justify-center items-center p-8">
        <Spinner size="lg" label="Loading staking data..." />
      </div>
    );
  }

  return (
    <div className="staking-interface p-6 space-y-6">
      {alert && (
        <Alert 
          color={alert.type === 'error' ? 'danger' : 'success'}
          onClose={() => setAlert(null)}
          className="mb-4"
        >
          {alert.message}
        </Alert>
      )}

      {/* Current Staking Status */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">Your Staking Status</h3>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-primary">
                {stakingData?.staked_amount?.toFixed(2) || '0.00'} TEO
              </p>
              <p className="text-small text-gray-500">Staked Amount</p>
            </div>
            
            <div className="text-center">
              <Badge color={getTierColor(stakingData?.tier)} variant="flat" size="lg">
                {stakingData?.tier_name || 'Bronze'}
              </Badge>
              <p className="text-small text-gray-500 mt-1">Current Tier</p>
            </div>
            
            <div className="text-center">
              <p className="text-2xl font-bold text-success">
                {stakingData?.commission_percentage?.toFixed(1) || '25.0'}%
              </p>
              <p className="text-small text-gray-500">Commission Rate</p>
            </div>
          </div>

          {/* Progress to Next Tier */}
          {stakingData?.tier < 4 && (
            <div className="mt-6">
              <div className="flex justify-between mb-2">
                <span>Progress to {getTierName(stakingData.tier + 1)}</span>
                <span>
                  {tierConfig?.[stakingData.tier + 1]?.min_stake - stakingData.staked_amount} TEO needed
                </span>
              </div>
              <Progress 
                value={calculateProgress(stakingData.staked_amount, stakingData.tier + 1)}
                color="primary"
                className="mb-2"
              />
            </div>
          )}
        </CardBody>
      </Card>

      {/* Staking Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Stake Tokens */}
        <Card>
          <CardHeader>
            <h4 className="font-semibold">Stake TEO Tokens</h4>
          </CardHeader>
          <CardBody className="space-y-4">
            <Input
              label="Amount to Stake"
              placeholder="Enter TEO amount"
              value={stakeAmount}
              onChange={(e) => setStakeAmount(e.target.value)}
              type="number"
              min="0"
              step="0.01"
              endContent={<span className="text-small text-gray-400">TEO</span>}
            />
            <Button
              color="primary"
              onClick={handleStake}
              disabled={isStaking || !stakeAmount}
              className="w-full"
            >
              {isStaking ? <Spinner size="sm" /> : 'Stake Tokens'}
            </Button>
          </CardBody>
        </Card>

        {/* Unstake Tokens */}
        <Card>
          <CardHeader>
            <h4 className="font-semibold">Unstake TEO Tokens</h4>
          </CardHeader>
          <CardBody className="space-y-4">
            <Input
              label="Amount to Unstake"
              placeholder="Enter TEO amount"
              value={unstakeAmount}
              onChange={(e) => setUnstakeAmount(e.target.value)}
              type="number"
              min="0"
              max={stakingData?.staked_amount || 0}
              step="0.01"
              endContent={<span className="text-small text-gray-400">TEO</span>}
            />
            <Button
              color="secondary"
              onClick={handleUnstake}
              disabled={isUnstaking || !unstakeAmount || !stakingData?.active}
              className="w-full"
            >
              {isUnstaking ? <Spinner size="sm" /> : 'Unstake Tokens'}
            </Button>
          </CardBody>
        </Card>
      </div>

      {/* Tier Information */}
      <Card>
        <CardHeader>
          <h4 className="font-semibold">Staking Tiers & Benefits</h4>
        </CardHeader>
        <CardBody>
          <Table aria-label="Staking tiers">
            <TableHeader>
              <TableColumn>Tier</TableColumn>
              <TableColumn>Required TEO</TableColumn>
              <TableColumn>Commission Rate</TableColumn>
              <TableColumn>Benefits</TableColumn>
            </TableHeader>
            <TableBody>
              {tierConfig && Object.entries(tierConfig).map(([tier, config]) => (
                <TableRow key={tier}>
                  <TableCell>
                    <Badge 
                      color={getTierColor(parseInt(tier))} 
                      variant={stakingData?.tier === parseInt(tier) ? "solid" : "flat"}
                    >
                      {config.name}
                    </Badge>
                  </TableCell>
                  <TableCell>{config.min_stake} TEO</TableCell>
                  <TableCell>{(config.commission_rate / 100).toFixed(1)}%</TableCell>
                  <TableCell>
                    {config.commission_rate === 1500 ? 'Maximum savings' : 
                     `Save ${((2500 - config.commission_rate) / 100).toFixed(1)}% vs Bronze`}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardBody>
      </Card>

      {/* Platform Statistics */}
      <Card>
        <CardHeader>
          <h4 className="font-semibold">Platform Statistics</h4>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-xl font-bold text-primary">
                {platformStats?.total_staked?.toFixed(0) || '0'}
              </p>
              <p className="text-small text-gray-500">Total Staked TEO</p>
            </div>
            <div>
              <p className="text-xl font-bold text-secondary">
                {platformStats?.total_stakers || '0'}
              </p>
              <p className="text-small text-gray-500">Total Stakers</p>
            </div>
            <div>
              <p className="text-xl font-bold text-warning">
                {platformStats?.average_stake?.toFixed(1) || '0.0'}
              </p>
              <p className="text-small text-gray-500">Average Stake</p>
            </div>
            <div>
              <p className="text-xl font-bold text-success">
                {platformStats?.utilization_percentage?.toFixed(1) || '0.0'}%
              </p>
              <p className="text-small text-gray-500">Supply Staked</p>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default StakingInterface;

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Chip,
  IconButton,
  Tooltip,
  CircularProgress
} from '@mui/material';
import {
  AccountBalanceWallet,
  Send,
  Refresh,
  TrendingUp
} from '@mui/icons-material';
import TeoCoinWithdrawal from '../TeoCoinWithdrawal';
import './TeoCoinBalanceWidget.scss';

const TeoCoinBalanceWidget = ({ variant = 'default' }) => {
  const [balance, setBalance] = useState(0);
  const [loading, setLoading] = useState(true);
  const [withdrawalOpen, setWithdrawalOpen] = useState(false);
  const [pendingWithdrawals, setPendingWithdrawals] = useState(0);

  const fetchBalance = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('accessToken');
      
      if (!token) {
        console.error('No authentication token found');
        return;
      }

      // Use the withdrawal API balance endpoint
      const response = await fetch('/api/v1/teocoin/withdrawals/balance/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          console.error('Authentication failed. Please log in again.');
        } else if (response.status === 403) {
          console.error('Access denied. Please check your permissions.');
        } else if (response.status >= 500) {
          console.error('Server error. Please try again later.');
        } else {
          console.error(`Balance API error! status: ${response.status}`);
        }
        return;
      }
      
      const data = await response.json();
      console.log('Balance API response:', data);
      
      if (data.success && data.balance) {
        // Use the correct field names from the API response
        setBalance(parseFloat(data.balance.available || 0));
        setPendingWithdrawals(parseFloat(data.balance.pending_withdrawal || 0));
      } else {
        console.warn('Balance API returned no data or error:', data);
      }
    } catch (error) {
      console.error('Failed to fetch balance:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBalance();
    // Refresh balance every 30 seconds
    const interval = setInterval(fetchBalance, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleWithdrawalClose = () => {
    setWithdrawalOpen(false);
    fetchBalance(); // Refresh balance after withdrawal
  };

  if (variant === 'compact') {
    return (
      <>
        <Card className="teocoin-balance-widget compact" elevation={2}>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box display="flex" alignItems="center" gap={1}>
                <AccountBalanceWallet color="primary" />
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    TeoCoin Balance
                  </Typography>
                  {loading ? (
                    <CircularProgress size={16} />
                  ) : (
                    <Typography variant="h6" color="primary">
                      {balance.toFixed(2)} TEO
                    </Typography>
                  )}
                </Box>
              </Box>
              <Button
                variant="contained"
                size="small"
                onClick={() => setWithdrawalOpen(true)}
                startIcon={<Send />}
                disabled={loading || balance <= 0}
              >
                Withdraw
              </Button>
            </Box>
            {pendingWithdrawals > 0 && (
              <Box mt={1}>
                <Chip 
                  label={`${pendingWithdrawals.toFixed(2)} TEO pending`}
                  color="warning"
                  size="small"
                />
              </Box>
            )}
          </CardContent>
        </Card>

        <TeoCoinWithdrawal
          open={withdrawalOpen}
          onClose={handleWithdrawalClose}
          userBalance={balance}
        />
      </>
    );
  }

  return (
    <>
      <Card className="teocoin-balance-widget" elevation={3}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Box display="flex" alignItems="center" gap={1}>
              <AccountBalanceWallet color="primary" fontSize="large" />
              <Typography variant="h6" color="primary">
                TeoCoin Wallet
              </Typography>
            </Box>
            <Tooltip title="Refresh balance">
              <IconButton onClick={fetchBalance} disabled={loading}>
                <Refresh />
              </IconButton>
            </Tooltip>
          </Box>

          <Box mb={3}>
            <Typography variant="subtitle2" color="textSecondary" gutterBottom>
              Available Balance
            </Typography>
            {loading ? (
              <Box display="flex" alignItems="center" gap={1}>
                <CircularProgress size={24} />
                <Typography variant="h4">Loading...</Typography>
              </Box>
            ) : (
              <Typography variant="h4" color="primary" fontWeight="bold">
                {balance.toFixed(2)} TEO
              </Typography>
            )}
          </Box>

          {pendingWithdrawals > 0 && (
            <Box mb={2}>
              <Chip 
                icon={<TrendingUp />}
                label={`${pendingWithdrawals.toFixed(2)} TEO pending withdrawal`}
                color="warning"
                variant="outlined"
              />
            </Box>
          )}

          <Box display="flex" gap={2}>
            <Button
              variant="contained"
              fullWidth
              onClick={() => setWithdrawalOpen(true)}
              startIcon={<Send />}
              disabled={loading || balance <= 0}
              size="large"
            >
              Withdraw to MetaMask
            </Button>
          </Box>

          <Box mt={2}>
            <Typography variant="caption" color="textSecondary">
              Withdraw your TeoCoin earnings to your MetaMask wallet on Polygon Amoy network
            </Typography>
          </Box>
        </CardContent>
      </Card>

      <TeoCoinWithdrawal
        open={withdrawalOpen}
        onClose={handleWithdrawalClose}
        userBalance={balance}
      />
    </>
  );
};

export default TeoCoinBalanceWidget;

import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button, 
  Alert, 
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Chip,
  Paper,
  TextField,
  Tabs,
  Tab,
  Badge,
  Divider
} from '@mui/material';
import { 
  School, 
  CheckCircle, 
  Cancel, 
  HourglassEmpty,
  Timer,
  AccountBalanceWallet,
  TrendingUp,
  Assignment,
  MonetizationOn
} from '@mui/icons-material';
import { useWeb3Context } from '../contexts/Web3Context';
import { useNotification } from '../contexts/NotificationContext';

/**
 * TeacherDiscountDashboard - Manage student discount requests
 * 
 * Features:
 * - View and manage pending discount requests
 * - One-click approval/decline (platform pays gas)
 * - Real-time earnings tracking
 * - Request history and analytics
 */
const TeacherDiscountDashboard = () => {
  const { account, teoBalance, refreshBalance } = useWeb3Context();
  const { showNotification } = useNotification();
  
  // State
  const [teacherRequests, setTeacherRequests] = useState([]);
  const [pendingRequests, setPendingRequests] = useState([]);
  const [completedRequests, setCompletedRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState({});
  const [selectedTab, setSelectedTab] = useState(0);
  
  // Dialog state
  const [approvalDialog, setApprovalDialog] = useState(false);
  const [declineDialog, setDeclineDialog] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [declineReason, setDeclineReason] = useState('');
  
  // Analytics
  const [analytics, setAnalytics] = useState({
    totalEarnings: 0,
    totalRequests: 0,
    approvalRate: 0,
    monthlyEarnings: 0
  });

  useEffect(() => {
    if (account) {
      loadTeacherRequests();
    }
  }, [account]);

  useEffect(() => {
    calculateAnalytics();
  }, [teacherRequests]);

  const loadTeacherRequests = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/discount/teacher/${account}/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        const requests = data.requests || [];
        setTeacherRequests(requests);
        
        // Separate pending and completed requests
        const pending = requests.filter(r => r.status === 0);
        const completed = requests.filter(r => r.status !== 0);
        
        setPendingRequests(pending);
        setCompletedRequests(completed);
      } else {
        console.error('Failed to load teacher requests');
      }
    } catch (error) {
      console.error('Error loading teacher requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateAnalytics = () => {
    const approved = teacherRequests.filter(r => r.status === 1);
    const totalEarnings = approved.reduce((sum, r) => sum + (r.teacher_bonus / 10**18), 0);
    const approvalRate = teacherRequests.length > 0 ? (approved.length / teacherRequests.length) * 100 : 0;
    
    // Calculate monthly earnings (last 30 days)
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    const monthlyApproved = approved.filter(r => 
      new Date(r.created_at) >= thirtyDaysAgo
    );
    const monthlyEarnings = monthlyApproved.reduce((sum, r) => sum + (r.teacher_bonus / 10**18), 0);
    
    setAnalytics({
      totalEarnings,
      totalRequests: teacherRequests.length,
      approvalRate,
      monthlyEarnings
    });
  };

  const handleApprove = async (request) => {
    setSelectedRequest(request);
    setApprovalDialog(true);
  };

  const handleDecline = async (request) => {
    setSelectedRequest(request);
    setDeclineDialog(true);
  };

  const confirmApproval = async () => {
    if (!selectedRequest) return;

    try {
      setActionLoading({ ...actionLoading, [selectedRequest.request_id]: true });

      const response = await fetch('/api/discount/approve/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        },
        body: JSON.stringify({
          request_id: selectedRequest.request_id,
          approver_address: account,
        }),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        showNotification(
          `Discount request approved! You earned ${(selectedRequest.teacher_bonus / 10**18).toFixed(2)} TEO bonus.`,
          'success'
        );
        
        // Refresh data
        await loadTeacherRequests();
        await refreshBalance();
        
      } else {
        throw new Error(result.error || 'Failed to approve request');
      }

    } catch (error) {
      console.error('Error approving request:', error);
      showNotification(error.message || 'Failed to approve request', 'error');
    } finally {
      setActionLoading({ ...actionLoading, [selectedRequest.request_id]: false });
      setApprovalDialog(false);
      setSelectedRequest(null);
    }
  };

  const confirmDecline = async () => {
    if (!selectedRequest || !declineReason.trim()) {
      showNotification('Please provide a reason for declining', 'error');
      return;
    }

    try {
      setActionLoading({ ...actionLoading, [selectedRequest.request_id]: true });

      const response = await fetch('/api/discount/decline/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        },
        body: JSON.stringify({
          request_id: selectedRequest.request_id,
          decliner_address: account,
          reason: declineReason.trim(),
        }),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        showNotification('Discount request declined.', 'info');
        
        // Refresh data
        await loadTeacherRequests();
        
      } else {
        throw new Error(result.error || 'Failed to decline request');
      }

    } catch (error) {
      console.error('Error declining request:', error);
      showNotification(error.message || 'Failed to decline request', 'error');
    } finally {
      setActionLoading({ ...actionLoading, [selectedRequest.request_id]: false });
      setDeclineDialog(false);
      setSelectedRequest(null);
      setDeclineReason('');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 0: return <HourglassEmpty color="warning" />;
      case 1: return <CheckCircle color="success" />;
      case 2: return <Cancel color="error" />;
      case 3: return <Timer color="disabled" />;
      default: return <HourglassEmpty />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 0: return 'Pending';
      case 1: return 'Approved';
      case 2: return 'Declined';
      case 3: return 'Expired';
      default: return 'Unknown';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 0: return 'warning';
      case 1: return 'success';
      case 2: return 'error';
      case 3: return 'default';
      default: return 'default';
    }
  };

  const formatTimeRemaining = (deadline) => {
    const now = new Date();
    const deadlineDate = new Date(deadline);
    const diff = deadlineDate.getTime() - now.getTime();
    
    if (diff <= 0) return 'Expired';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    return `${hours}h ${minutes}m remaining`;
  };

  const renderRequestCard = (request, showActions = false) => (
    <Paper key={request.request_id} sx={{ p: 3, mb: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
        <Box>
          <Typography variant="h6">
            Request #{request.request_id}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Course #{request.course_id}
          </Typography>
        </Box>
        <Chip
          icon={getStatusIcon(request.status)}
          label={getStatusText(request.status)}
          color={getStatusColor(request.status)}
        />
      </Box>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">Student</Typography>
          <Typography variant="body1">
            {`${request.student.slice(0, 6)}...${request.student.slice(-4)}`}
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">Discount</Typography>
          <Typography variant="body1">
            {request.discount_percent}% (€{(request.course_price * request.discount_percent / 10000).toFixed(2)})
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">Student Pays</Typography>
          <Typography variant="body1">
            {(request.teo_cost / 10**18).toFixed(2)} TEO
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">Your Bonus</Typography>
          <Typography variant="body1" color="success.main">
            +{(request.teacher_bonus / 10**18).toFixed(2)} TEO
          </Typography>
        </Grid>
      </Grid>

      {request.status === 0 && (
        <Typography variant="body2" color="warning.main" sx={{ mb: 2 }}>
          ⏰ {formatTimeRemaining(request.deadline)}
        </Typography>
      )}

      {request.decline_reason && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <strong>Decline Reason:</strong> {request.decline_reason}
        </Alert>
      )}

      {showActions && request.status === 0 && (
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            color="success"
            onClick={() => handleApprove(request)}
            disabled={actionLoading[request.request_id]}
            startIcon={actionLoading[request.request_id] ? <CircularProgress size={20} /> : <CheckCircle />}
          >
            Approve
          </Button>
          <Button
            variant="outlined"
            color="error"
            onClick={() => handleDecline(request)}
            disabled={actionLoading[request.request_id]}
            startIcon={<Cancel />}
          >
            Decline
          </Button>
        </Box>
      )}
    </Paper>
  );

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          <School sx={{ mr: 1, verticalAlign: 'middle' }} />
          Teacher Discount Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Manage student discount requests and track your TeoCoin earnings
        </Typography>
      </Box>

      {/* Analytics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <MonetizationOn color="primary" />
                <Box>
                  <Typography variant="h6">{analytics.totalEarnings.toFixed(2)} TEO</Typography>
                  <Typography variant="body2" color="text.secondary">Total Earnings</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Assignment color="primary" />
                <Box>
                  <Typography variant="h6">{analytics.totalRequests}</Typography>
                  <Typography variant="body2" color="text.secondary">Total Requests</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingUp color="primary" />
                <Box>
                  <Typography variant="h6">{analytics.approvalRate.toFixed(1)}%</Typography>
                  <Typography variant="body2" color="text.secondary">Approval Rate</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AccountBalanceWallet color="primary" />
                <Box>
                  <Typography variant="h6">{analytics.monthlyEarnings.toFixed(2)} TEO</Typography>
                  <Typography variant="body2" color="text.secondary">This Month</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Requests Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={selectedTab} onChange={(e, newValue) => setSelectedTab(newValue)}>
            <Tab
              label={
                <Badge badgeContent={pendingRequests.length} color="warning">
                  Pending Requests
                </Badge>
              }
            />
            <Tab label="Request History" />
          </Tabs>
        </Box>

        <CardContent>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              {/* Pending Requests Tab */}
              {selectedTab === 0 && (
                <Box>
                  {pendingRequests.length === 0 ? (
                    <Typography color="text.secondary" sx={{ textAlign: 'center', p: 3 }}>
                      No pending discount requests
                    </Typography>
                  ) : (
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Pending Approval ({pendingRequests.length})
                      </Typography>
                      {pendingRequests.map(request => renderRequestCard(request, true))}
                    </Box>
                  )}
                </Box>
              )}

              {/* History Tab */}
              {selectedTab === 1 && (
                <Box>
                  {completedRequests.length === 0 ? (
                    <Typography color="text.secondary" sx={{ textAlign: 'center', p: 3 }}>
                      No completed requests yet
                    </Typography>
                  ) : (
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Request History ({completedRequests.length})
                      </Typography>
                      {completedRequests.map(request => renderRequestCard(request, false))}
                    </Box>
                  )}
                </Box>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Approval Dialog */}
      <Dialog open={approvalDialog} onClose={() => setApprovalDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Approve Discount Request</DialogTitle>
        <DialogContent>
          {selectedRequest && (
            <Box>
              <Alert severity="success" sx={{ mb: 2 }}>
                You're about to approve this discount request. The platform will automatically:
                <ul>
                  <li>Transfer {(selectedRequest.teo_cost / 10**18).toFixed(2)} TEO from student to you</li>
                  <li>Give you a {(selectedRequest.teacher_bonus / 10**18).toFixed(2)} TEO bonus from the reward pool</li>
                  <li>Pay all gas fees for the transaction</li>
                </ul>
              </Alert>
              
              <Typography variant="body1">
                <strong>Course:</strong> #{selectedRequest.course_id}
              </Typography>
              <Typography variant="body1">
                <strong>Student:</strong> {selectedRequest.student}
              </Typography>
              <Typography variant="body1">
                <strong>Discount:</strong> {selectedRequest.discount_percent}%
              </Typography>
              <Typography variant="body1" color="success.main">
                <strong>Total you'll receive:</strong> {((selectedRequest.teo_cost + selectedRequest.teacher_bonus) / 10**18).toFixed(2)} TEO
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApprovalDialog(false)}>
            Cancel
          </Button>
          <Button
            onClick={confirmApproval}
            variant="contained"
            color="success"
            startIcon={<CheckCircle />}
          >
            Confirm Approval
          </Button>
        </DialogActions>
      </Dialog>

      {/* Decline Dialog */}
      <Dialog open={declineDialog} onClose={() => setDeclineDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Decline Discount Request</DialogTitle>
        <DialogContent>
          {selectedRequest && (
            <Box>
              <Typography variant="body1" gutterBottom>
                <strong>Course:</strong> #{selectedRequest.course_id}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Student:</strong> {selectedRequest.student}
              </Typography>
              
              <TextField
                label="Reason for declining"
                multiline
                rows={3}
                value={declineReason}
                onChange={(e) => setDeclineReason(e.target.value)}
                fullWidth
                required
                sx={{ mt: 2 }}
                placeholder="Please provide a brief explanation for the student..."
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeclineDialog(false)}>
            Cancel
          </Button>
          <Button
            onClick={confirmDecline}
            variant="contained"
            color="error"
            startIcon={<Cancel />}
            disabled={!declineReason.trim()}
          >
            Confirm Decline
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TeacherDiscountDashboard;

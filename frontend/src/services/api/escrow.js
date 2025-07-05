import api from '../core/apiClient';

/**
 * Escrow API Service
 * Handles teacher escrow management for TeoCoin discount system
 */

// Fetch all pending escrows for the teacher
export const fetchTeacherEscrows = async () => {
  return api.get('services/teacher/escrows/');
};

// Get specific escrow details
export const fetchEscrowDetails = async (escrowId) => {
  return api.get(`services/teacher/escrows/${escrowId}/`);
};

// Accept an escrow (teacher gets reduced EUR + TeoCoin)
export const acceptEscrow = async (escrowId) => {
  return api.post(`services/teacher/escrows/${escrowId}/accept/`);
};

// Reject an escrow (student pays standard EUR price)
export const rejectEscrow = async (escrowId) => {
  return api.post(`services/teacher/escrows/${escrowId}/reject/`);
};

// Get escrow statistics for teacher dashboard
export const fetchEscrowStats = async () => {
  return api.get('services/teacher/escrows/stats/');
};

// Utility function to format escrow status for display
export const formatEscrowStatus = (status) => {
  const statusMap = {
    'pending': { text: 'In Attesa', variant: 'warning', icon: 'clock' },
    'accepted': { text: 'Accettato', variant: 'success', icon: 'check-circle' },
    'rejected': { text: 'Rifiutato', variant: 'danger', icon: 'x-circle' },
    'expired': { text: 'Scaduto', variant: 'secondary', icon: 'archive' }
  };
  
  return statusMap[status] || { text: status, variant: 'secondary', icon: 'help-circle' };
};

// Calculate time remaining until escrow expires
export const getTimeRemaining = (expiresAt) => {
  const now = new Date();
  const expiry = new Date(expiresAt);
  const diff = expiry - now;
  
  if (diff <= 0) {
    return { expired: true, text: 'Scaduto' };
  }
  
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  
  if (days > 0) {
    return { expired: false, text: `${days}g ${hours}h rimanenti`, days, hours };
  } else {
    return { expired: false, text: `${hours}h rimanenti`, days: 0, hours };
  }
};

// Format TeoCoin amount for display
export const formatTeoCoinAmount = (amount) => {
  if (!amount) return '0 TCN';
  
  // Convert from Wei to TeoCoin (assuming 18 decimals)
  const tcnAmount = parseFloat(amount) / Math.pow(10, 18);
  
  // Format with appropriate decimal places
  if (tcnAmount >= 1000) {
    return `${(tcnAmount / 1000).toFixed(2)}K TCN`;
  } else if (tcnAmount >= 1) {
    return `${tcnAmount.toFixed(2)} TCN`;
  } else {
    return `${tcnAmount.toFixed(4)} TCN`;
  }
};

export default {
  fetchTeacherEscrows,
  fetchEscrowDetails,
  acceptEscrow,
  rejectEscrow,
  fetchEscrowStats,
  formatEscrowStatus,
  getTimeRemaining,
  formatTeoCoinAmount
};

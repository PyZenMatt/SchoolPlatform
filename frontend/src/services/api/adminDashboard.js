import api from '../core/apiClient';

export const fetchAdminDashboard = async () => {
  return api.get('dashboard/admin/');
};

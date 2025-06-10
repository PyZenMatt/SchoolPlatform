import api from '../core/apiClient';

export const fetchPendingTeachers = async () => {
  return api.get('pending-teachers/');
};

export const approveTeacher = async (userId) => {
  return api.post(`approve-teacher/${userId}/`);
};

export const rejectTeacher = async (userId) => {
  return api.post(`reject-teacher/${userId}/`);
};

export const fetchAdminDashboard = async () => {
  return api.get('dashboard/admin/');
};

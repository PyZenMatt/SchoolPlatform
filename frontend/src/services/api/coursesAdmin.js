import api from '../core/apiClient';

export const fetchPendingCourses = async () => {
  return api.get('pending-courses/');
};

export const approveCourse = async (courseId) => {
  return api.post(`approve-course/${courseId}/`);
};

export const rejectCourse = async (courseId) => {
  return api.post(`reject-course/${courseId}/`);
};

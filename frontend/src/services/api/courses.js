import api from '../core/apiClient';

export const fetchCourses = async (params = {}) => {
  const searchParams = new URLSearchParams();
  
  // Aggiungi parametri di filtro se presenti
  if (params.category && params.category !== 'all') {
    searchParams.append('category', params.category);
  }
  if (params.search) {
    searchParams.append('search', params.search);
  }
  if (params.ordering) {
    searchParams.append('ordering', params.ordering);
  }
  
  const queryString = searchParams.toString();
  const endpoint = queryString ? `courses/?${queryString}` : 'courses/';
  
  return api.get(endpoint);
};

export const purchaseCourse = async (courseId, walletAddress, transactionData = {}) => {
  return api.post(`courses/${courseId}/purchase/`, {
    wallet_address: walletAddress,
    ...transactionData
  });
};

export const createCourse = async (data) => {
  // Se data è FormData, non impostare Content-Type (axios lo gestirà automaticamente)
  const config = {};
  if (data instanceof FormData) {
    config.headers = {
      'Content-Type': 'multipart/form-data',
    };
  }
  return api.post('courses/', data, config);
};

// Crea una lezione associata a un corso
export const createLesson = async (data) => {
  // L'endpoint backend corretto è 'lessons/create/'
  const config = {};
  if (data instanceof FormData) {
    config.headers = {
      'Content-Type': 'multipart/form-data',
    };
  }
  return api.post('lessons/create/', data, config);
};

// Recupera le lezioni di un corso
export const fetchLessonsForCourse = async (courseId) => {
  return api.get(`courses/${courseId}/lessons/`);
};

export const createExercise = async (data) => {
  // L'endpoint backend accetta { title, description, lesson }
  const config = {};
  if (data instanceof FormData) {
    config.headers = {
      'Content-Type': 'multipart/form-data',
    };
  }
  return api.post('exercises/create/', data, config);
};

export const fetchExercisesForLesson = async (lessonId) => {
  return api.get(`lessons/${lessonId}/exercises/`);
};

export const fetchCourseDetail = async (courseId) => {
  const response = await api.get(`courses/${courseId}/`);
  return response.data;
};

export const fetchLessonDetail = async (lessonId) => {
  const response = await api.get(`lessons/${lessonId}/`);
  return response.data;
};

export const fetchExerciseDetail = async (exerciseId) => {
  const response = await api.get(`exercises/${exerciseId}/`);
  return response.data;
};

// Payment endpoints for Stripe integration
export const createPaymentIntent = async (courseId) => {
  return api.post(`courses/${courseId}/create-payment-intent/`);
};

export const confirmPayment = async (courseId, paymentIntentId) => {
  return api.post(`courses/${courseId}/confirm-payment/`, {
    payment_intent_id: paymentIntentId
  });
};

export const getPaymentSummary = async (courseId) => {
  return api.get(`courses/${courseId}/payment-summary/`);
};
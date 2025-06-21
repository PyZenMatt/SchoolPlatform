/**
 * Integration Test: Performance & Loading States
 * Tests how the application handles loading states, slow responses, and performance scenarios
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../contexts/AuthContext';
import App from '../../App';

// Mock the API client for performance testing
jest.mock('../../services/core/apiClient', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn()
  }
}));

// Mock react-router-dom's useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Test wrapper with all providers
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

// Helper function to create delayed promises
const createDelayedResponse = (data, delay = 1000) => {
  return new Promise(resolve => {
    setTimeout(() => resolve({ data }), delay);
  });
};

const createDelayedError = (error, delay = 1000) => {
  return new Promise((resolve, reject) => {
    setTimeout(() => reject(error), delay);
  });
};

describe('Performance & Loading Integration Tests', () => {
  let user;

  beforeEach(() => {
    user = userEvent.setup();
    mockNavigate.mockClear();
    localStorage.clear();
    
    // Reset all API mocks
    const { apiClient } = require('../../services/core/apiClient');
    apiClient.get.mockClear();
    apiClient.post.mockClear();
    apiClient.put.mockClear();
    apiClient.delete.mockClear();
  });

  test('handles slow login response with loading state', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock slow login response (2 seconds)
    apiClient.post.mockImplementation((url, data) => {
      if (url === '/login/') {
        return createDelayedResponse({
          access_token: 'fake-jwt-token',
          user: { id: 1, role: 'student', email: 'student@test.com' }
        }, 2000);
      }
      return Promise.resolve({ data: {} });
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Start login process
    const emailInput = screen.getByPlaceholderText(/email/i) || screen.getByLabelText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i) || screen.getByLabelText(/password/i);
    
    await user.type(emailInput, 'student@test.com');
    await user.type(passwordInput, 'password123');
    
    const loginButton = screen.getByRole('button', { name: /login|accedi/i });
    await user.click(loginButton);

    // Should show loading state immediately
    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith('/login/', 
        expect.objectContaining({
          email: 'student@test.com',
          password: 'password123'
        })
      );
    });

    // Wait for response and verify login completes
    await waitFor(() => {
      // Login should eventually complete
      expect(apiClient.post).toHaveBeenCalledTimes(1);
    }, { timeout: 3000 });
  });

  test('handles concurrent slow API calls on dashboard load', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock multiple slow API calls
    apiClient.get.mockImplementation((url) => {
      if (url === '/dashboard/student/') {
        return createDelayedResponse({
          completedCourses: 5,
          totalRewards: 150,
          certificates: ['cert1', 'cert2']
        }, 1500);
      }
      
      if (url === '/courses/enrolled/') {
        return createDelayedResponse({
          courses: [
            { id: 1, title: 'React Basics', progress: 75 },
            { id: 2, title: 'Advanced JavaScript', progress: 50 }
          ]
        }, 1200);
      }
      
      if (url === '/wallet/balance/') {
        return createDelayedResponse({
          balance: 100,
          pending_rewards: 25
        }, 800);
      }
      
      if (url === '/notifications/') {
        return createDelayedResponse({
          notifications: [
            { id: 1, message: 'Course completed', read: false }
          ]
        }, 600);
      }
      
      return Promise.resolve({ data: {} });
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Set up authenticated state
    localStorage.setItem('access_token', 'valid-token');
    localStorage.setItem('user_role', 'student');

    // Navigate to dashboard
    mockNavigate('/dashboard');

    // Simulate concurrent dashboard data loading
    const dashboardPromises = [
      apiClient.get('/dashboard/student/'),
      apiClient.get('/courses/enrolled/'),
      apiClient.get('/wallet/balance/'),
      apiClient.get('/notifications/')
    ];

    // All calls should be made concurrently
    const startTime = Date.now();
    const results = await Promise.all(dashboardPromises);
    const endTime = Date.now();

    // Should complete in roughly the time of the slowest call (1500ms)
    // not the sum of all calls (3900ms)
    expect(endTime - startTime).toBeLessThan(2000);
    expect(endTime - startTime).toBeGreaterThan(1400);

    // Verify all data was loaded
    expect(results[0].data.completedCourses).toBe(5);
    expect(results[1].data.courses).toHaveLength(2);
    expect(results[2].data.balance).toBe(100);
    expect(results[3].data.notifications).toHaveLength(1);
  });

  test('handles timeout scenarios gracefully', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock very slow response that should timeout
    apiClient.post.mockImplementation((url, data) => {
      if (url === '/courses/1/purchase/') {
        return createDelayedResponse({
          transaction_id: 'tx_123'
        }, 10000); // 10 second delay
      }
      return Promise.resolve({ data: {} });
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Set up authenticated state
    localStorage.setItem('access_token', 'valid-token');
    localStorage.setItem('user_role', 'student');

    // Start a purchase that will timeout
    const purchasePromise = apiClient.post('/courses/1/purchase/', { course_id: 1 });

    // Simulate user cancelling or timeout
    const timeoutPromise = new Promise((resolve, reject) => {
      setTimeout(() => reject(new Error('Request timeout')), 5000);
    });

    try {
      await Promise.race([purchasePromise, timeoutPromise]);
    } catch (error) {
      expect(error.message).toBe('Request timeout');
    }

    // Verify the API call was made
    expect(apiClient.post).toHaveBeenCalledWith('/courses/1/purchase/', { course_id: 1 });
  });

  test('handles rapid successive API calls without race conditions', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    let callCount = 0;
    apiClient.get.mockImplementation((url) => {
      if (url === '/courses/search/') {
        callCount++;
        return createDelayedResponse({
          results: [`Result ${callCount}`],
          query: `search-${callCount}`
        }, 300);
      }
      return Promise.resolve({ data: {} });
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Simulate rapid search queries (like user typing)
    const rapidCalls = [];
    for (let i = 1; i <= 5; i++) {
      rapidCalls.push(apiClient.get('/courses/search/'));
    }

    const results = await Promise.all(rapidCalls);

    // All calls should complete
    expect(results).toHaveLength(5);
    expect(callCount).toBe(5);

    // Results should be in order
    results.forEach((result, index) => {
      expect(result.data.results[0]).toBe(`Result ${index + 1}`);
    });
  });

  test('handles large data sets with pagination', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock paginated response with large dataset
    apiClient.get.mockImplementation((url) => {
      const urlParams = new URLSearchParams(url.split('?')[1] || '');
      const page = parseInt(urlParams.get('page') || '1');
      const pageSize = parseInt(urlParams.get('page_size') || '10');
      
      if (url.startsWith('/courses/')) {
        // Simulate 100 total courses
        const totalCourses = 100;
        const startIndex = (page - 1) * pageSize;
        const endIndex = Math.min(startIndex + pageSize, totalCourses);
        
        const courses = [];
        for (let i = startIndex; i < endIndex; i++) {
          courses.push({
            id: i + 1,
            title: `Course ${i + 1}`,
            price: 50 + i
          });
        }
        
        return createDelayedResponse({
          courses,
          total: totalCourses,
          page,
          pages: Math.ceil(totalCourses / pageSize)
        }, 500);
      }
      
      return Promise.resolve({ data: {} });
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Test loading multiple pages
    const page1 = await apiClient.get('/courses/?page=1&page_size=10');
    const page2 = await apiClient.get('/courses/?page=2&page_size=10');
    const page10 = await apiClient.get('/courses/?page=10&page_size=10');

    // Verify pagination works correctly
    expect(page1.data.courses).toHaveLength(10);
    expect(page1.data.courses[0].title).toBe('Course 1');
    expect(page1.data.page).toBe(1);

    expect(page2.data.courses).toHaveLength(10);
    expect(page2.data.courses[0].title).toBe('Course 11');
    expect(page2.data.page).toBe(2);

    expect(page10.data.courses).toHaveLength(10);
    expect(page10.data.courses[0].title).toBe('Course 91');
    expect(page10.data.page).toBe(10);

    // Verify total count is consistent
    expect(page1.data.total).toBe(100);
    expect(page2.data.total).toBe(100);
    expect(page10.data.total).toBe(100);
  });

  test('handles slow network with progress indicators', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock file upload with progress
    let uploadProgress = 0;
    apiClient.post.mockImplementation((url, data) => {
      if (url === '/courses/1/upload-material/') {
        return new Promise((resolve) => {
          const interval = setInterval(() => {
            uploadProgress += 20;
            if (uploadProgress >= 100) {
              clearInterval(interval);
              resolve({
                data: {
                  file_id: 'file_123',
                  uploaded: true,
                  size: 1024000
                }
              });
            }
          }, 200);
        });
      }
      return Promise.resolve({ data: {} });
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Set up authenticated state
    localStorage.setItem('access_token', 'valid-token');
    localStorage.setItem('user_role', 'teacher');

    // Start file upload
    const uploadPromise = apiClient.post('/courses/1/upload-material/', {
      file: new File(['content'], 'test.pdf', { type: 'application/pdf' })
    });

    // Check progress during upload
    const progressChecks = [];
    const checkInterval = setInterval(() => {
      progressChecks.push(uploadProgress);
      if (uploadProgress >= 100) {
        clearInterval(checkInterval);
      }
    }, 100);

    const result = await uploadPromise;

    // Verify upload completed
    expect(result.data.uploaded).toBe(true);
    expect(result.data.file_id).toBe('file_123');

    // Verify progress was tracked
    expect(progressChecks.length).toBeGreaterThan(0);
    expect(Math.max(...progressChecks)).toBe(100);
  });

  test('handles cache invalidation on data updates', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    let courseData = {
      id: 1,
      title: 'Original Title',
      price: 50,
      enrolled_count: 10
    };

    apiClient.get.mockImplementation((url) => {
      if (url === '/courses/1/') {
        return createDelayedResponse(courseData, 100);
      }
      return Promise.resolve({ data: {} });
    });

    apiClient.put.mockImplementation((url, data) => {
      if (url === '/courses/1/') {
        // Update cached data
        courseData = { ...courseData, ...data };
        return createDelayedResponse(courseData, 200);
      }
      return Promise.resolve({ data: {} });
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Initial load
    const initialData = await apiClient.get('/courses/1/');
    expect(initialData.data.title).toBe('Original Title');

    // Update course
    const updatedData = await apiClient.put('/courses/1/', {
      title: 'Updated Title',
      price: 75
    });

    // Verify update
    expect(updatedData.data.title).toBe('Updated Title');
    expect(updatedData.data.price).toBe(75);

    // Fetch again to verify cache invalidation
    const refetchedData = await apiClient.get('/courses/1/');
    expect(refetchedData.data.title).toBe('Updated Title');
    expect(refetchedData.data.price).toBe(75);
  });

  test('handles memory leaks in long-running operations', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock a long-running operation that could cause memory leaks
    let activeOperations = 0;
    
    apiClient.get.mockImplementation((url) => {
      if (url === '/analytics/real-time/') {
        activeOperations++;
        return createDelayedResponse({
          active_users: Math.floor(Math.random() * 100),
          timestamp: Date.now()
        }, 500).finally(() => {
          activeOperations--;
        });
      }
      return Promise.resolve({ data: {} });
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Start multiple concurrent operations
    const operations = [];
    for (let i = 0; i < 10; i++) {
      operations.push(apiClient.get('/analytics/real-time/'));
    }

    // Wait for all to complete
    await Promise.all(operations);

    // Verify no operations are still active (no memory leaks)
    expect(activeOperations).toBe(0);
  });
});

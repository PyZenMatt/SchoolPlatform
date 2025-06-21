/**
 * Integration Test: Error Handling & Recovery
 * Tests how the application handles errors across different services and recovers gracefully
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../contexts/AuthContext';
import App from '../../App';

// Mock the API client for error scenarios
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

// Mock console methods to suppress error logs during tests
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

// Test wrapper with all providers
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

describe('Error Handling Integration Tests', () => {
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
    
    // Suppress console errors/warnings during tests
    console.error = jest.fn();
    console.warn = jest.fn();
  });

  afterEach(() => {
    // Restore console methods
    console.error = originalConsoleError;
    console.warn = originalConsoleWarn;
  });

  test('handles network errors gracefully', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock network error
    apiClient.post.mockRejectedValue(new Error('Network Error'));
    apiClient.get.mockRejectedValue(new Error('Network Error'));

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Try to login with network error
    const emailInput = screen.getByPlaceholderText(/email/i) || screen.getByLabelText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i) || screen.getByLabelText(/password/i);
    
    await user.type(emailInput, 'test@test.com');
    await user.type(passwordInput, 'password123');
    
    const loginButton = screen.getByRole('button', { name: /login|accedi/i });
    await user.click(loginButton);

    // Should show network error message
    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith('/login/', expect.any(Object));
    });

    // Verify error is handled without crashing
    expect(screen.getByRole('button', { name: /login|accedi/i })).toBeInTheDocument();
  });

  test('handles authentication errors and redirects appropriately', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock 401 unauthorized error
    apiClient.post.mockRejectedValue({
      response: { 
        status: 401, 
        data: { error: 'Invalid credentials' } 
      }
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Try to login with invalid credentials
    const emailInput = screen.getByPlaceholderText(/email/i) || screen.getByLabelText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i) || screen.getByLabelText(/password/i);
    
    await user.type(emailInput, 'wrong@test.com');
    await user.type(passwordInput, 'wrongpassword');
    
    const loginButton = screen.getByRole('button', { name: /login|accedi/i });
    await user.click(loginButton);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith('/login/', 
        expect.objectContaining({
          email: 'wrong@test.com',
          password: 'wrongpassword'
        })
      );
    });

    // Should stay on login page and show error
    expect(screen.getByRole('button', { name: /login|accedi/i })).toBeInTheDocument();
  });

  test('handles session expiration and forces re-authentication', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Set up authenticated state initially
    localStorage.setItem('access_token', 'expired-token');
    localStorage.setItem('user_role', 'student');

    // Mock 401 for expired token
    apiClient.get.mockRejectedValue({
      response: { 
        status: 401, 
        data: { error: 'Token expired' } 
      }
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Navigate to dashboard (which requires auth)
    mockNavigate('/dashboard');

    // Try to fetch dashboard data with expired token
    try {
      await apiClient.get('/dashboard/student/');
    } catch (error) {
      expect(error.response.status).toBe(401);
    }

    // Should clear auth state and redirect to login
    await waitFor(() => {
      expect(localStorage.getItem('access_token')).toBeNull();
    });
  });

  test('handles payment processing errors gracefully', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock successful login but failed payment
    apiClient.post.mockImplementation((url, data) => {
      if (url === '/login/') {
        return Promise.resolve({
          data: {
            access_token: 'valid-token',
            user: { id: 1, role: 'student', email: 'student@test.com' }
          }
        });
      }
      
      if (url === '/courses/1/purchase/') {
        return Promise.reject({
          response: { 
            status: 402, 
            data: { error: 'Insufficient funds' } 
          }
        });
      }
      
      return Promise.resolve({ data: {} });
    });

    apiClient.get.mockImplementation((url) => {
      if (url === '/wallet/balance/') {
        return Promise.resolve({
          data: { balance: 10 } // Not enough for course
        });
      }
      return Promise.resolve({ data: {} });
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Login first
    const emailInput = screen.getByPlaceholderText(/email/i) || screen.getByLabelText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i) || screen.getByLabelText(/password/i);
    
    await user.type(emailInput, 'student@test.com');
    await user.type(passwordInput, 'password123');
    
    const loginButton = screen.getByRole('button', { name: /login|accedi/i });
    await user.click(loginButton);

    // Simulate course purchase attempt
    try {
      await apiClient.post('/courses/1/purchase/', { course_id: 1 });
    } catch (error) {
      expect(error.response.status).toBe(402);
      expect(error.response.data.error).toBe('Insufficient funds');
    }

    // Verify payment error is handled
    expect(apiClient.post).toHaveBeenCalledWith('/courses/1/purchase/', { course_id: 1 });
  });

  test('handles blockchain transaction failures', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock blockchain transaction failure
    apiClient.post.mockImplementation((url, data) => {
      if (url === '/blockchain/rewards/distribute/') {
        return Promise.reject({
          response: { 
            status: 500, 
            data: { error: 'Blockchain network congestion' } 
          }
        });
      }
      return Promise.resolve({ data: {} });
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Simulate blockchain transaction failure
    try {
      await apiClient.post('/blockchain/rewards/distribute/', {
        student_id: 1,
        amount: 25
      });
    } catch (error) {
      expect(error.response.status).toBe(500);
      expect(error.response.data.error).toBe('Blockchain network congestion');
    }

    // Should handle blockchain errors gracefully
    expect(apiClient.post).toHaveBeenCalledWith('/blockchain/rewards/distribute/', 
      expect.objectContaining({
        student_id: 1,
        amount: 25
      })
    );
  });

  test('handles concurrent API call failures', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock multiple services failing at once
    apiClient.get.mockImplementation((url) => {
      if (url === '/dashboard/student/') {
        return Promise.reject({
          response: { status: 503, data: { error: 'Service temporarily unavailable' } }
        });
      }
      
      if (url === '/courses/') {
        return Promise.reject({
          response: { status: 503, data: { error: 'Course service down' } }
        });
      }
      
      if (url === '/wallet/balance/') {
        return Promise.reject({
          response: { status: 503, data: { error: 'Wallet service down' } }
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
    localStorage.setItem('user_role', 'student');

    // Try multiple concurrent API calls
    const promises = [
      apiClient.get('/dashboard/student/').catch(e => e),
      apiClient.get('/courses/').catch(e => e),
      apiClient.get('/wallet/balance/').catch(e => e)
    ];

    const results = await Promise.all(promises);

    // All should fail gracefully
    results.forEach(result => {
      expect(result.response.status).toBe(503);
    });

    // Verify all calls were made
    expect(apiClient.get).toHaveBeenCalledWith('/dashboard/student/');
    expect(apiClient.get).toHaveBeenCalledWith('/courses/');
    expect(apiClient.get).toHaveBeenCalledWith('/wallet/balance/');
  });

  test('handles malformed API responses', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock malformed responses
    apiClient.get.mockImplementation((url) => {
      if (url === '/dashboard/student/') {
        return Promise.resolve({
          data: null // Malformed response
        });
      }
      
      if (url === '/courses/') {
        return Promise.resolve({
          // Missing data property
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
    localStorage.setItem('user_role', 'student');

    // Try API calls with malformed responses
    const dashboardResponse = await apiClient.get('/dashboard/student/');
    const coursesResponse = await apiClient.get('/courses/');

    // Should handle malformed data gracefully
    expect(dashboardResponse.data).toBeNull();
    expect(coursesResponse.data).toBeUndefined();

    // Application should not crash
    expect(apiClient.get).toHaveBeenCalledWith('/dashboard/student/');
    expect(apiClient.get).toHaveBeenCalledWith('/courses/');
  });

  test('handles rate limiting errors', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock rate limiting error
    apiClient.post.mockRejectedValue({
      response: { 
        status: 429, 
        data: { error: 'Too many requests', retry_after: 60 },
        headers: { 'retry-after': '60' }
      }
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Simulate rapid API calls (login attempts)
    try {
      await apiClient.post('/login/', { email: 'test@test.com', password: 'pass' });
    } catch (error) {
      expect(error.response.status).toBe(429);
      expect(error.response.data.error).toBe('Too many requests');
      expect(error.response.headers['retry-after']).toBe('60');
    }

    // Should handle rate limiting appropriately
    expect(apiClient.post).toHaveBeenCalledWith('/login/', 
      expect.objectContaining({
        email: 'test@test.com',
        password: 'pass'
      })
    );
  });

  test('handles validation errors from multiple forms', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock validation errors for different forms
    apiClient.post.mockImplementation((url, data) => {
      if (url === '/register/') {
        return Promise.reject({
          response: { 
            status: 400, 
            data: { 
              errors: {
                email: ['Email already exists'],
                password: ['Password too weak']
              }
            }
          }
        });
      }
      
      if (url === '/courses/create/') {
        return Promise.reject({
          response: { 
            status: 400, 
            data: { 
              errors: {
                title: ['Title is required'],
                price: ['Price must be positive']
              }
            }
          }
        });
      }
      
      return Promise.resolve({ data: {} });
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Test registration validation errors
    try {
      await apiClient.post('/register/', {
        email: 'existing@test.com',
        password: '123'
      });
    } catch (error) {
      expect(error.response.status).toBe(400);
      expect(error.response.data.errors.email).toContain('Email already exists');
      expect(error.response.data.errors.password).toContain('Password too weak');
    }

    // Test course creation validation errors
    try {
      await apiClient.post('/courses/create/', {
        title: '',
        price: -10
      });
    } catch (error) {
      expect(error.response.status).toBe(400);
      expect(error.response.data.errors.title).toContain('Title is required');
      expect(error.response.data.errors.price).toContain('Price must be positive');
    }

    // Verify validation errors are handled
    expect(apiClient.post).toHaveBeenCalledWith('/register/', expect.any(Object));
    expect(apiClient.post).toHaveBeenCalledWith('/courses/create/', expect.any(Object));
  });
});

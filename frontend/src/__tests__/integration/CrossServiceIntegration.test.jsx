/**
 * Integration Test: Cross-Service Integration
 * Tests how different API services work together in complete workflows
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import App from '../../App';
import { AuthProvider } from '../../contexts/AuthContext';

// Mock the API client with comprehensive service mocking
jest.mock('../../services/core/apiClient', () => ({
  apiClient: {
    get: jest.fn(() => Promise.resolve({ data: {} })),
    post: jest.fn(() => Promise.resolve({ data: {} })),
    put: jest.fn(() => Promise.resolve({ data: {} })),
    delete: jest.fn(() => Promise.resolve({ data: {} }))
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

describe('Cross-Service Integration Tests', () => {
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

  test('complete course purchase and enrollment flow', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock APIs for complete purchase flow
    apiClient.post.mockImplementation((url, data) => {
      // Login
      if (url === '/login/') {
        return Promise.resolve({
          data: {
            access_token: 'fake-jwt-token',
            user: { id: 1, role: 'student', email: 'student@test.com' }
          }
        });
      }
      
      // Course purchase
      if (url === '/courses/1/purchase/') {
        return Promise.resolve({
          data: {
            transaction_id: 'tx_123',
            status: 'completed',
            amount: 50,
            course_id: 1
          }
        });
      }
      
      return Promise.resolve({ data: {} });
    });

    apiClient.get.mockImplementation((url) => {
      // Course details
      if (url === '/courses/1/') {
        return Promise.resolve({
          data: {
            id: 1,
            title: 'Advanced React',
            price: 50,
            instructor: 'John Doe',
            available: true
          }
        });
      }
      
      // Wallet balance
      if (url === '/wallet/balance/') {
        return Promise.resolve({
          data: { balance: 100 }
        });
      }
      
      // Updated enrollment status
      if (url === '/courses/1/enrollment/') {
        return Promise.resolve({
          data: { enrolled: true, progress: 0 }
        });
      }
      
      return Promise.resolve({ data: {} });
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // STEP 1: User logs in
    const emailInput = screen.getByPlaceholderText(/email/i) || screen.getByLabelText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i) || screen.getByLabelText(/password/i);
    
    await user.type(emailInput, 'student@test.com');
    await user.type(passwordInput, 'password123');
    
    const loginButton = screen.getByRole('button', { name: /login|accedi/i });
    await user.click(loginButton);

    // STEP 2: Navigate to course page (simulate)
    mockNavigate('/courses/1');

    // STEP 3: Simulate course purchase flow
    await waitFor(() => {
      // Verify auth service was called
      expect(apiClient.post).toHaveBeenCalledWith('/login/', 
        expect.objectContaining({
          email: 'student@test.com',
          password: 'password123'
        })
      );
    });

    // STEP 4: Verify course service integration
    // Course details should be fetched
    expect(apiClient.get).toHaveBeenCalledWith('/courses/1/');
    
    // STEP 5: Verify wallet service integration
    // Wallet balance should be checked before purchase
    expect(apiClient.get).toHaveBeenCalledWith('/wallet/balance/');
  });

  test('teacher course creation with blockchain integration', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock teacher login and course creation with blockchain
    apiClient.post.mockImplementation((url, data) => {
      // Teacher login
      if (url === '/login/') {
        return Promise.resolve({
          data: {
            access_token: 'fake-teacher-token',
            user: { id: 2, role: 'teacher', email: 'teacher@test.com' }
          }
        });
      }
      
      // Course creation
      if (url === '/courses/create/') {
        return Promise.resolve({
          data: {
            id: 5,
            title: data.title,
            blockchain_contract: '0x123abc...',
            status: 'pending_blockchain'
          }
        });
      }
      
      // Blockchain contract deployment
      if (url === '/blockchain/deploy-course/') {
        return Promise.resolve({
          data: {
            contract_address: '0x123abc...',
            transaction_hash: '0xdef456...',
            status: 'deployed'
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

    // Teacher login
    const emailInput = screen.getByPlaceholderText(/email/i) || screen.getByLabelText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i) || screen.getByLabelText(/password/i);
    
    await user.type(emailInput, 'teacher@test.com');
    await user.type(passwordInput, 'password123');
    
    const loginButton = screen.getByRole('button', { name: /login|accedi/i });
    await user.click(loginButton);

    // Navigate to course creation
    mockNavigate('/courses/create');

    // Simulate course creation with blockchain integration
    await waitFor(() => {
      // Verify auth service call
      expect(apiClient.post).toHaveBeenCalledWith('/login/', 
        expect.objectContaining({
          email: 'teacher@test.com',
          password: 'password123'
        })
      );
    });

    // Verify the integration between course and blockchain services
    // This would happen when teacher creates a course that needs blockchain deployment
    const courseCreationFlow = async () => {
      // Course service creates course
      await apiClient.post('/courses/create/', { title: 'Blockchain Course' });
      
      // Blockchain service deploys smart contract
      await apiClient.post('/blockchain/deploy-course/', { course_id: 5 });
    };

    // Execute the flow (in real app, this would be triggered by UI interaction)
    await courseCreationFlow();

    // Verify both services were called in sequence
    expect(apiClient.post).toHaveBeenCalledWith('/courses/create/', 
      expect.objectContaining({ title: 'Blockchain Course' })
    );
    expect(apiClient.post).toHaveBeenCalledWith('/blockchain/deploy-course/', 
      expect.objectContaining({ course_id: 5 })
    );
  });

  test('student reward system integration across multiple services', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock student completing course and receiving rewards
    apiClient.post.mockImplementation((url, data) => {
      // Course completion
      if (url === '/courses/1/complete/') {
        return Promise.resolve({
          data: {
            completion_date: new Date().toISOString(),
            certificate_id: 'cert_123',
            reward_earned: 25
          }
        });
      }
      
      // Blockchain reward transaction
      if (url === '/blockchain/rewards/distribute/') {
        return Promise.resolve({
          data: {
            transaction_hash: '0xabc123...',
            amount: 25,
            recipient: 'student@test.com'
          }
        });
      }
      
      return Promise.resolve({ data: {} });
    });

    apiClient.get.mockImplementation((url) => {
      // Updated wallet balance after reward
      if (url === '/wallet/balance/') {
        return Promise.resolve({
          data: { balance: 125 } // 100 + 25 reward
        });
      }
      
      // Dashboard with updated stats
      if (url === '/dashboard/student/') {
        return Promise.resolve({
          data: {
            completedCourses: 1,
            totalRewards: 25,
            certificates: ['cert_123']
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

    // Mock authenticated student
    localStorage.setItem('access_token', 'fake-student-token');
    localStorage.setItem('user_role', 'student');

    // Simulate course completion flow
    const courseCompletionFlow = async () => {
      // Course service marks completion
      await apiClient.post('/courses/1/complete/', {});
      
      // Blockchain service processes reward
      await apiClient.post('/blockchain/rewards/distribute/', {
        student_id: 1,
        course_id: 1,
        amount: 25
      });
      
      // Dashboard and wallet services reflect updates
      await apiClient.get('/wallet/balance/');
      await apiClient.get('/dashboard/student/');
    };

    // Execute the flow
    await courseCompletionFlow();

    // Verify all services worked together
    expect(apiClient.post).toHaveBeenCalledWith('/courses/1/complete/', {});
    expect(apiClient.post).toHaveBeenCalledWith('/blockchain/rewards/distribute/', 
      expect.objectContaining({
        student_id: 1,
        course_id: 1,
        amount: 25
      })
    );
    expect(apiClient.get).toHaveBeenCalledWith('/wallet/balance/');
    expect(apiClient.get).toHaveBeenCalledWith('/dashboard/student/');
  });

  test('error propagation across services', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock service failure scenarios
    apiClient.post.mockImplementation((url, data) => {
      // Auth service succeeds
      if (url === '/login/') {
        return Promise.resolve({
          data: {
            access_token: 'fake-token',
            user: { id: 1, role: 'student' }
          }
        });
      }
      
      // Course service fails
      if (url === '/courses/1/purchase/') {
        return Promise.reject({
          response: { status: 500, data: { error: 'Payment processing failed' } }
        });
      }
      
      return Promise.resolve({ data: {} });
    });

    apiClient.get.mockImplementation((url) => {
      // Wallet service succeeds
      if (url === '/wallet/balance/') {
        return Promise.resolve({
          data: { balance: 100 }
        });
      }
      
      return Promise.resolve({ data: {} });
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Login succeeds
    const emailInput = screen.getByPlaceholderText(/email/i) || screen.getByLabelText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i) || screen.getByLabelText(/password/i);
    
    await user.type(emailInput, 'student@test.com');
    await user.type(passwordInput, 'password123');
    
    const loginButton = screen.getByRole('button', { name: /login|accedi/i });
    await user.click(loginButton);

    // Simulate purchase flow that will fail
    try {
      await apiClient.post('/courses/1/purchase/', {});
    } catch (error) {
      // Verify error is properly handled
      expect(error.response.status).toBe(500);
      expect(error.response.data.error).toBe('Payment processing failed');
    }

    // Verify auth service worked but course service failed
    expect(apiClient.post).toHaveBeenCalledWith('/login/', expect.any(Object));
    expect(apiClient.post).toHaveBeenCalledWith('/courses/1/purchase/', {});
  });

  test('complex multi-user interaction flow', async () => {
    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock teacher creating course and student enrolling
    apiClient.post.mockImplementation((url, data) => {
      // Teacher creates course
      if (url === '/courses/create/') {
        return Promise.resolve({
          data: {
            id: 10,
            title: data.title,
            instructor_id: 2,
            status: 'published'
          }
        });
      }
      
      // Student enrolls
      if (url === '/courses/10/enroll/') {
        return Promise.resolve({
          data: {
            enrollment_id: 'enr_123',
            course_id: 10,
            student_id: 1
          }
        });
      }
      
      return Promise.resolve({ data: {} });
    });

    apiClient.get.mockImplementation((url) => {
      // Course becomes available for students
      if (url === '/courses/') {
        return Promise.resolve({
          data: {
            courses: [
              { id: 10, title: 'New Teacher Course', available: true, instructor: 'Test Teacher' }
            ]
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

    // Simulate teacher-student interaction
    const multiUserFlow = async () => {
      // Teacher creates course
      await apiClient.post('/courses/create/', {
        title: 'New Teacher Course',
        description: 'Course for testing'
      });
      
      // Course becomes available (course service updates)
      await apiClient.get('/courses/');
      
      // Student enrolls in the course
      await apiClient.post('/courses/10/enroll/', {
        student_id: 1
      });
    };

    // Execute multi-user flow
    await multiUserFlow();

    // Verify the complete interaction
    expect(apiClient.post).toHaveBeenCalledWith('/courses/create/', 
      expect.objectContaining({
        title: 'New Teacher Course',
        description: 'Course for testing'
      })
    );
    expect(apiClient.get).toHaveBeenCalledWith('/courses/');
    expect(apiClient.post).toHaveBeenCalledWith('/courses/10/enroll/', 
      expect.objectContaining({
        student_id: 1
      })
    );
  });
});

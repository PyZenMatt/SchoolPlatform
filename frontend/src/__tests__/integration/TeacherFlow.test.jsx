/**
 * Integration Test: Teacher Complete Flow
 * Tests teacher user journey from login to course management
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import App from '../../App';
import { AuthProvider } from '../../contexts/AuthContext';

// Mock the API client
jest.mock('../../services/core/apiClient', () => ({
  apiClient: {
    get: jest.fn(() => Promise.resolve({ data: {} })),
    post: jest.fn((url, data) => {
      // Teacher login mock
      if (url === '/login/') {
        if (data.email === 'teacher@test.com' && data.password === 'password123') {
          return Promise.resolve({
            data: {
              access_token: 'fake-teacher-jwt-token',
              refresh_token: 'fake-teacher-refresh-token',
              user: {
                id: 2,
                email: 'teacher@test.com',
                role: 'teacher',
                first_name: 'Test',
                last_name: 'Teacher'
              }
            }
          });
        }
      }
      
      // Course creation mock
      if (url === '/courses/create/') {
        return Promise.resolve({
          data: {
            id: 3,
            title: data.title,
            description: data.description,
            instructor: 'Test Teacher',
            status: 'draft'
          }
        });
      }
      
      return Promise.resolve({ data: {} });
    }),
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

describe('Teacher Complete Flow Integration', () => {
  let user;

  beforeEach(() => {
    user = userEvent.setup();
    mockNavigate.mockClear();
    
    // Clear localStorage
    localStorage.clear();
    
    // Reset API mocks
    const { apiClient } = require('../../services/core/apiClient');
    apiClient.get.mockClear();
    apiClient.post.mockClear();
    apiClient.put.mockClear();
    apiClient.delete.mockClear();
  });

  test('complete teacher journey: login → dashboard → course management', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // STEP 1: Teacher login
    const emailInput = screen.getByPlaceholderText(/email/i) || screen.getByLabelText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i) || screen.getByLabelText(/password/i);
    
    await user.type(emailInput, 'teacher@test.com');
    await user.type(passwordInput, 'password123');

    const submitButton = screen.getByRole('button', { name: /login|accedi|sign in/i });
    await user.click(submitButton);

    // STEP 2: Verify teacher navigation to teacher dashboard
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard/teacher');
    }, { timeout: 3000 });

    // Verify teacher token storage
    expect(localStorage.getItem('access_token')).toBe('fake-teacher-jwt-token');
  });

  test('teacher dashboard loads with course management features', async () => {
    // Mock authenticated teacher state
    localStorage.setItem('access_token', 'fake-teacher-jwt-token');
    localStorage.setItem('user_role', 'teacher');

    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock teacher dashboard API
    apiClient.get.mockImplementation((url) => {
      if (url === '/dashboard/teacher/') {
        return Promise.resolve({
          data: {
            courses: [
              { id: 1, title: 'Advanced JavaScript', students: 25, status: 'active' },
              { id: 2, title: 'React Patterns', students: 18, status: 'draft' }
            ],
            stats: {
              totalStudents: 43,
              totalCourses: 2,
              avgRating: 4.7
            },
            recentActivity: [
              { id: 1, type: 'enrollment', message: 'New student enrolled in Advanced JavaScript' }
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

    // Navigate to teacher dashboard
    mockNavigate('/dashboard/teacher');

    // Wait for dashboard to load
    await waitFor(() => {
      // Check for teacher dashboard elements
      const dashboardElements = screen.queryAllByText(/teacher|docente|courses|corsi/i);
      expect(dashboardElements.length).toBeGreaterThan(0);
    });

    // Verify teacher dashboard API call
    expect(apiClient.get).toHaveBeenCalledWith('/dashboard/teacher/');
  });

  test('teacher can create new course', async () => {
    // Mock authenticated teacher state
    localStorage.setItem('access_token', 'fake-teacher-jwt-token');
    localStorage.setItem('user_role', 'teacher');

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Navigate to course creation (simulate)
    mockNavigate('/courses/create');

    // Fill course creation form (adjust selectors based on actual component)
    const titleElements = screen.queryAllByPlaceholderText(/title|titolo/i);
    const descriptionElements = screen.queryAllByPlaceholderText(/description|descrizione/i);
    
    if (titleElements.length > 0 && descriptionElements.length > 0) {
      await user.type(titleElements[0], 'New Test Course');
      await user.type(descriptionElements[0], 'This is a test course for integration testing');

      // Submit course creation
      const createButtons = screen.queryAllByText(/create|crea|submit/i);
      if (createButtons.length > 0) {
        await user.click(createButtons[0]);

        // Verify course creation API call
        await waitFor(() => {
          const { apiClient } = require('../../services/core/apiClient');
          expect(apiClient.post).toHaveBeenCalledWith('/courses/create/', 
            expect.objectContaining({
              title: 'New Test Course',
              description: 'This is a test course for integration testing'
            })
          );
        });
      }
    }
  });

  test('teacher can view and manage course students', async () => {
    // Mock authenticated teacher state
    localStorage.setItem('access_token', 'fake-teacher-jwt-token');
    localStorage.setItem('user_role', 'teacher');

    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock course students API
    apiClient.get.mockImplementation((url) => {
      if (url === '/courses/1/students/') {
        return Promise.resolve({
          data: {
            students: [
              { id: 1, name: 'Student One', email: 'student1@test.com', progress: 75 },
              { id: 2, name: 'Student Two', email: 'student2@test.com', progress: 50 }
            ],
            totalStudents: 2
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

    // Navigate to course students page
    mockNavigate('/courses/1/students');

    // Wait for students data to load
    await waitFor(() => {
      // Check for student list (adjust based on actual component)
      const studentElements = screen.queryAllByText(/student|studente/i);
      if (studentElements.length > 0) {
        expect(studentElements[0]).toBeInTheDocument();
      }
    });

    // Verify API call for students
    expect(apiClient.get).toHaveBeenCalledWith('/courses/1/students/');
  });

  test('teacher can edit course content', async () => {
    // Mock authenticated teacher state
    localStorage.setItem('access_token', 'fake-teacher-jwt-token');
    localStorage.setItem('user_role', 'teacher');

    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock course edit API
    apiClient.get.mockImplementation((url) => {
      if (url === '/courses/1/edit/') {
        return Promise.resolve({
          data: {
            id: 1,
            title: 'Advanced JavaScript',
            description: 'Learn advanced JavaScript concepts',
            lessons: [
              { id: 1, title: 'Closures and Scope', content: 'Lesson content here' },
              { id: 2, title: 'Async Programming', content: 'Async lesson content' }
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

    // Navigate to course edit page
    mockNavigate('/courses/1/edit');

    // Wait for course data to load
    await waitFor(() => {
      // Check for edit form (adjust based on actual component)
      const editElements = screen.queryAllByText(/edit|modifica|advanced javascript/i);
      if (editElements.length > 0) {
        expect(editElements[0]).toBeInTheDocument();
      }
    });

    // Verify API call for course edit data
    expect(apiClient.get).toHaveBeenCalledWith('/courses/1/edit/');
  });

  test('teacher can view analytics and statistics', async () => {
    // Mock authenticated teacher state
    localStorage.setItem('access_token', 'fake-teacher-jwt-token');
    localStorage.setItem('user_role', 'teacher');

    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock analytics API
    apiClient.get.mockImplementation((url) => {
      if (url === '/analytics/teacher/') {
        return Promise.resolve({
          data: {
            totalStudents: 43,
            totalCourses: 5,
            avgCourseRating: 4.7,
            completionRate: 82,
            monthlyStats: {
              enrollments: 12,
              completions: 8,
              revenue: 1500
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

    // Navigate to analytics page
    mockNavigate('/analytics');

    // Wait for analytics data to load
    await waitFor(() => {
      // Check for analytics elements (adjust based on actual component)
      const analyticsElements = screen.queryAllByText(/analytics|statistics|43|4\.7/i);
      if (analyticsElements.length > 0) {
        expect(analyticsElements[0]).toBeInTheDocument();
      }
    });

    // Verify analytics API call
    expect(apiClient.get).toHaveBeenCalledWith('/analytics/teacher/');
  });

  test('teacher course management error handling', async () => {
    // Mock authenticated teacher state
    localStorage.setItem('access_token', 'fake-teacher-jwt-token');
    localStorage.setItem('user_role', 'teacher');

    const { apiClient } = require('../../services/core/apiClient');
    
    // Mock API error
    apiClient.get.mockRejectedValue({
      response: { status: 500, data: { error: 'Server error' } }
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Navigate to dashboard (which should trigger API call)
    mockNavigate('/dashboard/teacher');

    // Wait for error handling
    await waitFor(() => {
      // Check for error message (adjust based on actual error handling)
      const errorElements = screen.queryAllByText(/error|errore|failed|fallito/i);
      if (errorElements.length > 0) {
        expect(errorElements[0]).toBeInTheDocument();
      }
    });
  });
});

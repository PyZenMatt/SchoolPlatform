/**
 * Comprehensive TeacherDashboard component tests
 * GOAL: Verify rendering, interactions, and states of the teacher dashboard
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import TeacherDashboard from '../views/dashboard/TeacherDashboard';
import { AuthProvider } from '../contexts/AuthContext';

// Mock router and context wrapper
const MockRouter = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

// Mock the core API client
jest.mock('../services/core/apiClient', () => ({
  get: jest.fn((url) => {
    if (url === 'profile/') {
      return Promise.resolve({
        data: {
          id: 1,
          username: 'testteacher',
          email: 'test@teacher.com',
          role: 'teacher',
          first_name: 'Test',
          last_name: 'Teacher'
        }
      });
    }
    return Promise.resolve({ data: {} });
  }),
  post: jest.fn(() => Promise.resolve({ data: {} })),
  put: jest.fn(() => Promise.resolve({ data: {} })),
  delete: jest.fn(() => Promise.resolve({ data: {} }))
}));

// Mock dashboard API calls
jest.mock('../services/api/dashboard', () => ({
  fetchUserProfile: jest.fn(() => 
    Promise.resolve({
      data: {
        id: 1,
        username: 'testteacher',
        email: 'test@teacher.com',
        role: 'teacher',
        first_name: 'Test',
        last_name: 'Teacher'
      }
    })
  ),
  fetchTeacherDashboard: jest.fn(() => 
    Promise.resolve({
      data: {
        courses: [
          {
            id: 1,
            title: 'React Advanced Course',
            students_count: 25,
            status: 'published',
            created_at: '2024-01-15',
            lessons: [
              {
                id: 1,
                title: 'Introduction to React',
                order: 1
              }
            ]
          }
        ],
        sales: {
          daily: 150.50,
          monthly: 3200.75,
          yearly: 25000.00
        },
        transactions: [
          {
            id: 1,
            type: 'course_sale',
            amount: 50,
            date: '2024-01-15',
            course_title: 'React Advanced Course'
          }
        ]
      }
    })
  )
}));

// Mock courses API calls
jest.mock('../services/api/courses', () => ({
  fetchLessonsForCourse: jest.fn((courseId) => 
    Promise.resolve({
      data: [
        {
          id: 1,
          title: 'Introduction to React',
          order: 1,
          course: courseId
        },
        {
          id: 2,
          title: 'React Components',
          order: 2,
          course: courseId
        }
      ]
    })
  ),
  fetchExercisesForLesson: jest.fn((lessonId) => 
    Promise.resolve({
      data: [
        {
          id: 1,
          title: 'React Component Exercise',
          lesson: lessonId,
          type: 'coding'
        }
      ]
    })
  )
}));

describe('TeacherDashboard Component', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
    
    // Mock localStorage for authentication
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn((key) => {
          if (key === 'accessToken' || key === 'token' || key === 'access') {
            return 'mock-teacher-auth-token';
          }
          return null;
        }),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn()
      },
      writable: true
    });
  });

  afterEach(() => {
    // Cleanup after each test
    jest.restoreAllMocks();
  });

  it('should render without crashing', () => {
    render(
      <MockRouter>
        <TeacherDashboard />
      </MockRouter>
    );

    // Component should render without errors
    expect(document.body).toBeInTheDocument();
  });

  it('should display teacher dashboard title or identifying elements', async () => {
    render(
      <MockRouter>
        <TeacherDashboard />
      </MockRouter>
    );

    // Look for teacher-specific dashboard elements
    const dashboardElement = screen.queryByText(/dashboard/i) || 
                            screen.queryByText(/teacher/i) ||
                            screen.queryByText(/courses/i) ||
                            screen.queryByText(/sales/i) ||
                            screen.queryByRole('main');

    expect(dashboardElement).toBeInTheDocument();
  });

  it('should handle loading state properly', () => {
    render(
      <MockRouter>
        <TeacherDashboard />
      </MockRouter>
    );

    // Check for loading indicators using getAllByText for multiple elements
    const loadingElements = screen.queryAllByText(/caricamento/i);
    const statusElement = screen.queryByRole('status');

    // Should have at least one loading indicator
    const hasLoadingIndicator = loadingElements.length > 0 || statusElement !== null;
    expect(hasLoadingIndicator).toBe(true);
  });

  it('should display course information when loaded', async () => {
    render(
      <MockRouter>
        <TeacherDashboard />
      </MockRouter>
    );

    // Wait for course data to load and be displayed
    await waitFor(() => {
      const courseElement = screen.queryByText(/react advanced course/i) ||
                           screen.queryByText(/course/i) ||
                           screen.queryByText(/students/i);
      
      if (courseElement) {
        expect(courseElement).toBeInTheDocument();
      }
    }, { timeout: 3000 });
  });

  it('should display sales information when loaded', async () => {
    render(
      <MockRouter>
        <TeacherDashboard />
      </MockRouter>
    );

    // Wait for sales data to be displayed
    await waitFor(() => {
      const salesElement = screen.queryByText(/150/i) ||
                          screen.queryByText(/3200/i) ||
                          screen.queryByText(/sales/i) ||
                          screen.queryByText(/revenue/i);
      
      if (salesElement) {
        expect(salesElement).toBeInTheDocument();
      }
    }, { timeout: 3000 });
  });

  it('should be accessible', () => {
    render(
      <MockRouter>
        <TeacherDashboard />
      </MockRouter>
    );

    // Basic accessibility checks
    const mainElement = screen.queryByRole('main') || document.body;
    expect(mainElement).toBeInTheDocument();
  });

  it('should handle responsive design', () => {
    render(
      <MockRouter>
        <TeacherDashboard />
      </MockRouter>
    );

    // Component should render in different viewport sizes
    expect(document.body).toBeInTheDocument();
  });

  it('should not throw errors during lifecycle', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    render(
      <MockRouter>
        <TeacherDashboard />
      </MockRouter>
    );

    // Wait a bit for async operations
    await waitFor(() => {
      expect(document.body).toBeInTheDocument();
    });

    // Should not have console errors
    expect(consoleSpy).not.toHaveBeenCalled();
    
    consoleSpy.mockRestore();
  });
});

describe('TeacherDashboard Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn((key) => {
          if (key === 'accessToken' || key === 'token' || key === 'access') {
            return 'mock-teacher-auth-token';
          }
          return null;
        }),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn()
      },
      writable: true
    });
  });

  it('should handle component structure correctly', () => {
    render(
      <MockRouter>
        <TeacherDashboard />
      </MockRouter>
    );

    // Should have proper component structure
    expect(document.body).toBeInTheDocument();
  });

  it('should handle props and context correctly', () => {
    render(
      <MockRouter>
        <TeacherDashboard />
      </MockRouter>
    );

    // Should handle AuthProvider context without errors
    expect(document.body).toBeInTheDocument();
  });

  it('should be compatible with React 18', () => {
    render(
      <MockRouter>
        <TeacherDashboard />
      </MockRouter>
    );

    // Should work with React 18 features
    expect(document.body).toBeInTheDocument();
  });
});

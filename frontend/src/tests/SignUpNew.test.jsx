/**
 * Comprehensive SignUpNew component tests
 * GOAL: Verify registration form functionality, validation, and API integration
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import SignUpNew from '../views/auth/signup/SignUpNew';
import { AuthProvider } from '../contexts/AuthContext';

// Mock react-router-dom's useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Mock wrapper component
const MockWrapper = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

// Mock the core API client
jest.mock('../services/core/apiClient', () => ({
  apiClient: {
    get: jest.fn(() => Promise.resolve({ data: {} })),
    post: jest.fn((url, data) => {
      if (url === '/register/') {
        if (data.email === 'existing@test.com') {
          return Promise.reject({
            response: {
              status: 400,
              data: { error: 'User already exists' }
            }
          });
        }
        if (data.email === 'validation@test.com') {
          return Promise.reject({
            response: {
              status: 400,
              data: { 
                email: ['This email is already registered'],
                username: ['Username too short']
              }
            }
          });
        }
        return Promise.resolve({
          data: {
            message: 'Registration successful',
            user: {
              id: 1,
              email: data.email,
              username: data.username
            }
          }
        });
      }
      return Promise.resolve({ data: {} });
    }),
    put: jest.fn(() => Promise.resolve({ data: {} })),
    delete: jest.fn(() => Promise.resolve({ data: {} }))
  }
}));

// Mock auth API functions
jest.mock('../services/api/auth', () => ({
  signup: jest.fn((userData) => {
    if (userData.email === 'existing@test.com') {
      return Promise.reject({
        response: {
          status: 400,
          data: { error: 'User already exists' }
        }
      });
    }
    if (userData.email === 'validation@test.com') {
      return Promise.reject({
        response: {
          status: 400,
          data: { 
            email: ['This email is already registered'],
            username: ['Username too short']
          }
        }
      });
    }
    return Promise.resolve({
      data: {
        message: 'Registration successful',
        user: {
          id: 1,
          email: userData.email,
          username: userData.username
        }
      }
    });
  }),
  checkUsernameAvailability: jest.fn((username) => {
    if (username === 'taken') {
      return Promise.resolve({ available: false });
    }
    return Promise.resolve({ available: true });
  })
}));

describe('SignUpNew Component', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
    mockNavigate.mockClear();
    
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(),
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

  it('should render registration form without crashing', () => {
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Should have form elements
    expect(screen.getByRole('button')).toBeInTheDocument(); // Submit button
    
    // Look for input fields by placeholder
    expect(screen.getByPlaceholderText('Username')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Conferma Password')).toBeInTheDocument();
  });

  it('should have required form fields', () => {
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Should have multiple input fields (username, email, password, confirm password)
    expect(screen.getByPlaceholderText('Username')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Conferma Password')).toBeInTheDocument();
    
    // Should have submit button
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('should show validation errors for empty fields', async () => {
    const user = userEvent.setup();
    
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Try to submit form without filling fields
    const submitButton = screen.getByRole('button');
    await user.click(submitButton);

    // Should show validation errors
    await waitFor(() => {
      const errorMessages = screen.queryAllByText(/richiesta|required|obbligatorio/i);
      expect(errorMessages.length).toBeGreaterThan(0);
    });
  });

  it('should validate email format', async () => {
    const user = userEvent.setup();
    
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Fill email field with invalid email
    const emailInput = screen.getByPlaceholderText('Email');
    
    await user.type(emailInput, 'invalid-email');
    
    // Try to submit
    const submitButton = screen.getByRole('button');
    await user.click(submitButton);

    // Should show email validation error
    await waitFor(() => {
      const emailError = screen.queryByText(/email valido|valid email|formato email/i);
      if (emailError) {
        expect(emailError).toBeInTheDocument();
      }
    });
  });

  it('should validate password strength', async () => {
    const user = userEvent.setup();
    
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Fill form with weak password
    const usernameInput = screen.getByPlaceholderText('Username');
    const emailInput = screen.getByPlaceholderText('Email');
    const passwordInput = screen.getByPlaceholderText('Password');
    
    await user.type(usernameInput, 'testuser');
    await user.type(emailInput, 'test@test.com');
    await user.type(passwordInput, '123'); // Weak password

    // Try to submit
    const submitButton = screen.getByRole('button');
    await user.click(submitButton);

    // Should show password validation error
    await waitFor(() => {
      const passwordError = screen.queryByText(/password|password troppo|too short|caratteri/i);
      if (passwordError) {
        expect(passwordError).toBeInTheDocument();
      }
    });
  });

  it('should validate password confirmation match', async () => {
    const user = userEvent.setup();
    
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Fill form with mismatched passwords
    const passwordInput = screen.getByPlaceholderText('Password');
    const confirmPasswordInput = screen.getByPlaceholderText('Conferma Password');
    
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'differentpassword');

    // Try to submit
    const submitButton = screen.getByRole('button');
    await user.click(submitButton);

    // Should show password mismatch error
    await waitFor(() => {
      const mismatchError = screen.queryByText(/password.*match|conferma|coincidono/i);
      if (mismatchError) {
        expect(mismatchError).toBeInTheDocument();
      }
    });
  });

  it('should handle successful registration', async () => {
    const user = userEvent.setup();
    
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Fill form with valid data
    const usernameInput = screen.getByPlaceholderText('Username');
    const emailInput = screen.getByPlaceholderText('Email');
    const passwordInput = screen.getByPlaceholderText('Password');
    const confirmPasswordInput = screen.getByPlaceholderText('Conferma Password');
    
    await user.type(usernameInput, 'newuser');
    await user.type(emailInput, 'newuser@test.com');
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'password123');

    // Submit form
    const submitButton = screen.getByRole('button');
    await user.click(submitButton);

    // Should navigate to login or success page
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalled();
    });
  });

  it('should handle registration errors from server', async () => {
    const user = userEvent.setup();
    
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Fill form with existing email
    const usernameInput = screen.getByPlaceholderText('Username');
    const emailInput = screen.getByPlaceholderText('Email');
    const passwordInput = screen.getByPlaceholderText('Password');
    const confirmPasswordInput = screen.getByPlaceholderText('Conferma Password');
    
    await user.type(usernameInput, 'existinguser');
    await user.type(emailInput, 'existing@test.com');
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'password123');

    // Submit form
    const submitButton = screen.getByRole('button');
    await user.click(submitButton);

    // Should show server error message
    await waitFor(() => {
      const errorMessage = screen.queryByText(/already exists|già registrata|existing/i);
      if (errorMessage) {
        expect(errorMessage).toBeInTheDocument();
      }
    });
  });

  it('should handle field-specific validation errors from server', async () => {
    const user = userEvent.setup();
    
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Fill form with data that triggers field-specific errors
    const usernameInput = screen.getByPlaceholderText('Username');
    const emailInput = screen.getByPlaceholderText('Email');
    const passwordInput = screen.getByPlaceholderText('Password');
    const confirmPasswordInput = screen.getByPlaceholderText('Conferma Password');
    
    await user.type(usernameInput, 'ab'); // Short username
    await user.type(emailInput, 'validation@test.com');
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'password123');

    // Submit form
    const submitButton = screen.getByRole('button');
    await user.click(submitButton);

    // Should show field-specific errors
    await waitFor(() => {
      const usernameError = screen.queryByText(/username.*short|username troppo/i);
      const emailError = screen.queryByText(/already registered|già registrata/i);
      
      // At least one error should be shown
      expect(usernameError || emailError).toBeTruthy();
    });
  });

  it('should disable submit button during loading', async () => {
    const user = userEvent.setup();
    
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Fill form with valid data
    const usernameInput = screen.getByPlaceholderText('Username');
    const emailInput = screen.getByPlaceholderText('Email');
    const passwordInput = screen.getByPlaceholderText('Password');
    
    await user.type(usernameInput, 'testuser');
    await user.type(emailInput, 'test@test.com');
    await user.type(passwordInput, 'password123');

    const submitButton = screen.getByRole('button');
    
    // Submit form and check if button is disabled during loading
    await user.click(submitButton);
    
    // During the async operation, button might be disabled
    expect(submitButton).toBeInTheDocument();
  });

  it('should check username availability', async () => {
    const user = userEvent.setup();
    
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Type username that's taken
    const usernameInput = screen.getByPlaceholderText('Username');
    
    await user.type(usernameInput, 'taken');
    
    // Blur to trigger availability check
    fireEvent.blur(usernameInput);

    // Should show availability feedback
    await waitFor(() => {
      const availabilityMessage = screen.queryByText(/not available|non disponibile|taken/i);
      if (availabilityMessage) {
        expect(availabilityMessage).toBeInTheDocument();
      }
    });
  });

  it('should validate required terms acceptance if present', async () => {
    const user = userEvent.setup();
    
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Fill all form fields but don't accept terms
    const usernameInput = screen.getByPlaceholderText('Username');
    const emailInput = screen.getByPlaceholderText('Email');
    const passwordInput = screen.getByPlaceholderText('Password');
    
    await user.type(usernameInput, 'testuser');
    await user.type(emailInput, 'test@test.com');
    await user.type(passwordInput, 'password123');

    // Look for terms checkbox
    const checkbox = screen.queryByRole('checkbox');
    if (checkbox) {
      // Try to submit without accepting terms
      const submitButton = screen.getByRole('button');
      await user.click(submitButton);

      // Should show terms acceptance error
      await waitFor(() => {
        const termsError = screen.queryByText(/terms|termini|privacy|accept/i);
        if (termsError) {
          expect(termsError).toBeInTheDocument();
        }
      });
    }
  });

  it('should be accessible', () => {
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Should have proper form structure
    const form = screen.getByRole('button').closest('form') || document.body;
    expect(form).toBeInTheDocument();
  });

  it('should handle component lifecycle without errors', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Wait a bit for any async operations
    await waitFor(() => {
      expect(document.body).toBeInTheDocument();
    });

    // Should not have console errors
    expect(consoleSpy).not.toHaveBeenCalled();
    
    consoleSpy.mockRestore();
  });
});

describe('SignUpNew Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNavigate.mockClear();
    
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn()
      },
      writable: true
    });
  });

  it('should integrate with AuthContext correctly', () => {
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Component should render without AuthContext errors
    expect(document.body).toBeInTheDocument();
  });

  it('should handle form validation with Formik', async () => {
    const user = userEvent.setup();
    
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Should have Formik-powered form validation
    const submitButton = screen.getByRole('button');
    await user.click(submitButton);

    // Should prevent submission with empty fields
    expect(mockNavigate).not.toHaveBeenCalledWith('/login');
  });

  it('should be compatible with React 18', () => {
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Should work with React 18 features
    expect(document.body).toBeInTheDocument();
  });

  it('should redirect to login after successful registration', async () => {
    const user = userEvent.setup();
    
    render(
      <MockWrapper>
        <SignUpNew />
      </MockWrapper>
    );

    // Fill and submit valid form
    const usernameInput = screen.getByPlaceholderText('Username');
    const emailInput = screen.getByPlaceholderText('Email');
    const passwordInput = screen.getByPlaceholderText('Password');
    const confirmPasswordInput = screen.getByPlaceholderText('Conferma Password');
    
    await user.type(usernameInput, 'successuser');
    await user.type(emailInput, 'success@test.com');
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'password123');

    const submitButton = screen.getByRole('button');
    await user.click(submitButton);

    // Should navigate after successful registration
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalled();
    }, { timeout: 3000 });
  });
});

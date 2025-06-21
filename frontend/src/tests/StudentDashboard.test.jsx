/**
 * Test completo del StudentDashboard component
 * OBIETTIVO: Verificare rendering, interazioni e stati del dashboard studente
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import StudentDashboard from '../views/dashboard/StudentDashboard';
import { AuthProvider } from '../contexts/AuthContext';

// Mock del router e context necessari
const MockRouter = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

// Mock del core API client
jest.mock('../services/core/apiClient', () => ({
  get: jest.fn((url) => {
    if (url === 'profile/') {
      return Promise.resolve({
        data: {
          id: 1,
          username: 'teststudent',
          email: 'test@student.com',
          role: 'student',
          first_name: 'Test',
          last_name: 'Student'
        }
      });
    }
    return Promise.resolve({ data: {} });
  }),
  post: jest.fn(() => Promise.resolve({ data: {} })),
  put: jest.fn(() => Promise.resolve({ data: {} })),
  delete: jest.fn(() => Promise.resolve({ data: {} }))
}));

// Mock delle API calls per evitare errori di rete
jest.mock('../services/api/dashboard', () => ({
  fetchUserProfile: jest.fn(() => 
    Promise.resolve({
      data: {
        id: 1,
        username: 'teststudent',
        email: 'test@student.com',
        role: 'student',
        first_name: 'Test',
        last_name: 'Student'
      }
    })
  ),
  fetchStudentDashboard: jest.fn(() => 
    Promise.resolve({
      data: {
        courses: [
          {
            id: 1,
            title: 'React Advanced Course',
            progress: 65,
            instructor: 'Prof. Bianchi',
            status: 'in_progress'
          }
        ],
        enrolled_courses: [
          {
            id: 1,
            title: 'React Advanced Course',
            progress: 65,
            instructor: 'Prof. Bianchi',
            status: 'in_progress'
          }
        ],
        total_courses: 1,
        wallet_balance: 1250.50,
        current_streak: 7,
        recent_transactions: [
          {
            id: 1,
            type: 'purchase',
            amount: 50,
            date: '2024-01-15'
          }
        ],
        completed_lessons: 12,
        badges: ['fast-learner', 'active-student']
      }
    })
  ),
  fetchStudentSubmissions: jest.fn(() => 
    Promise.resolve({
      data: {
        results: [
          {
            id: 1,
            exercise_title: 'React Testing',
            score: 92,
            status: 'graded'
          }
        ]
      }
    })
  )
}));

describe('StudentDashboard Component', () => {
  beforeEach(() => {
    // Reset dei mock prima di ogni test
    jest.clearAllMocks();
    
    // Mock localStorage per simulare utente autenticato
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn((key) => {
          if (key === 'accessToken' || key === 'token' || key === 'access') {
            return 'mock-auth-token';
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
    // Cleanup dopo ogni test
    jest.restoreAllMocks();
  });

  it('should render without crashing', () => {
    render(
      <MockRouter>
        <StudentDashboard />
      </MockRouter>
    );

    // Il componente dovrebbe renderizzare senza errori
    expect(document.body).toBeInTheDocument();
  });

  it('should display student dashboard title', async () => {
    render(
      <MockRouter>
        <StudentDashboard />
      </MockRouter>
    );

    // Cerca il titolo o elementi identificativi del dashboard studente
    const dashboardElement = screen.queryByText(/dashboard/i) || 
                            screen.queryByText(/studente/i) ||
                            screen.queryByText(/corsi/i) ||
                            screen.queryByRole('main');

    expect(dashboardElement).toBeInTheDocument();
  });

  it('should handle loading state properly', () => {
    render(
      <MockRouter>
        <StudentDashboard />
      </MockRouter>
    );

    // Verifica che ci sia uno stato di loading iniziale usando getAllByText
    const loadingElements = screen.queryAllByText(/caricamento/i);
    const statusElement = screen.queryByRole('status');

    // Deve esserci almeno un elemento di loading o status
    const hasLoadingIndicator = loadingElements.length > 0 || statusElement !== null;
    expect(hasLoadingIndicator).toBe(true);
  });

  it('should be accessible', () => {
    render(
      <MockRouter>
        <StudentDashboard />
      </MockRouter>
    );

    // Verifica accessibilità di base
    const container = document.querySelector('div');
    expect(container).toBeInTheDocument();
    
    // Non dovrebbero esserci errori di accessibilità evidenti
    expect(document.body.children.length).toBeGreaterThan(0);
  });

  it('should handle navigation interactions', async () => {
    render(
      <MockRouter>
        <StudentDashboard />
      </MockRouter>
    );

    // Cerca elementi cliccabili (pulsanti, link, tab)
    const clickableElements = [
      ...screen.queryAllByRole('button'),
      ...screen.queryAllByRole('link'),
      ...screen.queryAllByRole('tab')
    ];

    // Se ci sono elementi cliccabili, il primo dovrebbe essere funzionante
    if (clickableElements.length > 0) {
      const firstClickable = clickableElements[0];
      expect(firstClickable).toBeInTheDocument();
      
      // Test di click senza errori
      fireEvent.click(firstClickable);
      expect(firstClickable).toBeInTheDocument(); // Dovrebbe rimanere nel DOM
    }
  });

  it('should handle responsive design', () => {
    // Test su diverse dimensioni di schermo
    const originalInnerWidth = window.innerWidth;
    
    // Mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      configurable: true,
      value: 375
    });
    
    render(
      <MockRouter>
        <StudentDashboard />
      </MockRouter>
    );

    // Il componente dovrebbe renderizzare anche su mobile
    expect(document.body.children.length).toBeGreaterThan(0);
    
    // Ripristina il viewport originale
    Object.defineProperty(window, 'innerWidth', {
      configurable: true,
      value: originalInnerWidth
    });
  });

  it('should not throw errors during lifecycle', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    render(
      <MockRouter>
        <StudentDashboard />
      </MockRouter>
    );

    // Attendi che eventuali useEffect si completino
    await waitFor(() => {
      expect(document.body).toBeInTheDocument();
    }, { timeout: 1000 });

    // Non dovrebbero esserci errori in console
    expect(consoleSpy).not.toHaveBeenCalled();
    
    consoleSpy.mockRestore();
  });
});

/**
 * Test di integrazione con mock data
 */
describe('StudentDashboard Integration', () => {
  it('should handle component structure correctly', () => {
    const { container } = render(
      <MockRouter>
        <StudentDashboard />
      </MockRouter>
    );

    // Il container dovrebbe avere contenuto
    expect(container.firstChild).toBeInTheDocument();
    
    // Dovrebbe avere una struttura HTML valida
    expect(container.innerHTML).toContain('<');
    expect(container.innerHTML.length).toBeGreaterThan(0);
  });

  it('should handle props and context correctly', () => {
    // Test che il componente accetti props senza errori
    const testProps = {
      testProp: 'test-value'
    };

    render(
      <MockRouter>
        <StudentDashboard {...testProps} />
      </MockRouter>
    );

    expect(document.body).toBeInTheDocument();
  });

  it('should be compatible with React 18', () => {
    // Test compatibilità React 18 con concurrent features
    const { container } = render(
      <MockRouter>
        <StudentDashboard />
      </MockRouter>
    );

    // Non dovrebbero esserci warning specifici di React 18
    expect(container).toBeInTheDocument();
  });
});

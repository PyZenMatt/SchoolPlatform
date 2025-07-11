import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Table, Tabs, Tab, ProgressBar } from 'react-bootstrap';
import { Link } from 'react-router-dom';

import WalletBalanceDisplay from '../../components/blockchain/WalletBalanceDisplay';
import ProfileWalletDisplay from '../../components/blockchain/ProfileWalletDisplay';
import StudentTeoCoinDashboard from '../../components/blockchain/DBStudentTeoCoinDashboard';
import RewardNotifications from '../../components/blockchain/RewardNotifications';
import { fetchStudentDashboard, fetchUserProfile } from '../../services/api/dashboard';
import StudentSubmissions from './StudentSubmissions';

// Import dashboard styles
import './dashboard-styles.css';

// Placeholder avatar - you may want to use actual user avatar
import avatar1 from '../../assets/images/user/avatar-1.jpg';

// Helper functions for course cards
const getLevelBadgeClass = (level) => {
  switch (level?.toLowerCase()) {
    case 'beginner':
      return 'bg-success';
    case 'intermediate':
      return 'bg-warning';
    case 'advanced':
      return 'bg-danger';
    default:
      return 'bg-primary';
  }
};

const calculateCourseProgress = (course) => {
  if (!course.lessons_count || course.lessons_count === 0) return 0;
  const completed = course.completed_lessons || 0;
  return Math.round((completed / course.lessons_count) * 100);
};

const StudentDashboard = () => {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [userProfile, setUserProfile] = useState(null);
  const [stats, setStats] = useState({
    totalCourses: 0,
    completedLessons: 0,
    activeBadges: 0
  });

  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      setError('');
      try {
        // Fetch user profile
        const profileRes = await fetchUserProfile();
        setUserProfile(profileRes.data);
        
        const res = await fetchStudentDashboard();
        setCourses(res.data.courses || []);
        
        console.log('Corsi caricati:', res.data.courses);
        
        setTransactions(res.data.recent_transactions || []);
        
        // Calculate stats
        setStats({
          totalCourses: res.data.courses?.length || 0,
          completedLessons: res.data.completed_lessons || 0,
          activeBadges: res.data.badges?.length || 0
        });
      } catch (err) {
        console.error('Errore API dashboard:', err, err.response?.data);
        setError('Errore nel caricamento della dashboard');
      } finally {
        setLoading(false);
      }
    };
    loadDashboard();
  }, []);

  // Dashboard stats data in Datta Able format
  const dashStatsData = [
    { 
      title: 'Corsi Acquisiti', 
      amount: stats.totalCourses.toString(), 
      icon: 'icon-arrow-up text-c-green', 
      value: 75, 
      class: 'progress-c-theme' 
    },
    { 
      title: 'Lezioni Completate', 
      amount: stats.completedLessons.toString(), 
      icon: 'icon-arrow-up text-c-green', 
      value: 60, 
      class: 'progress-c-theme2' 
    },
    { 
      title: 'TeoCoins', 
      amount: '0', // Placeholder value - actual balance shown by TeoCoinBalance component
      icon: 'icon-arrow-up text-c-green', 
      value: 85, 
      class: 'progress-c-theme' 
    }
  ];

  if (loading) {
    return (
      <div className="pcoded-content">
        <div className="pcoded-inner-content">
          <div className="main-body">
            <div className="page-wrapper">
              <div className="page-body">
                <div className="row">
                  <div className="col-md-12">
                    <div className="card">
                      <div className="card-body text-center">
                        <div className="spinner-border text-primary" role="status">
                          <span className="sr-only">Caricamento...</span>
                        </div>
                        <p className="mt-3">Caricamento dashboard...</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <React.Fragment>
      {/* Welcome Section */}
      <Row className="mb-4">
        <Col md={12}>
          <Card>
            <Card.Body className="text-center py-5">
              <h2 className="f-w-300 d-flex align-items-center justify-content-center m-b-0">
                <i className="feather icon-user text-c-green f-30 m-r-10" />
                Benvenuto, {userProfile?.first_name || userProfile?.username || 'Studente'}!
              </h2>
              <p className="text-muted mt-3">Bentornato nella tua dashboard. Continua il tuo percorso di apprendimento.</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Stats Cards */}
      <Row>
        {dashStatsData.map((data, index) => {
          return (
            <Col key={index} md={6} xl={4}>
              <Card>
                <Card.Body>
                  <h6 className="mb-4">{data.title}</h6>
                  <div className="row d-flex align-items-center">
                    <div className="col-9">
                      <h3 className="f-w-300 d-flex align-items-center m-b-0">
                        <i className={`feather ${data.icon} f-30 m-r-5`} />
                        {data.amount}
                      </h3>
                    </div>
                    <div className="col-3 text-end">
                      <p className="m-b-0">{data.value}%</p>
                    </div>
                  </div>
                  <div className="progress m-t-30" style={{ height: '7px' }}>
                    <div
                      className={`progress-bar ${data.class}`}
                      role="progressbar"
                      style={{ width: data.value + '%' }}
                      aria-valuenow={data.value}
                      aria-valuemin="0"
                      aria-valuemax="100"
                    />
                  </div>
                </Card.Body>
              </Card>
            </Col>
          );
        })}
      </Row>

      {/* Error Alert */}
      {error && (
        <Row>
          <Col md={12}>
            <Card className="bg-danger text-white">
              <Card.Body>
                <i className="feather icon-alert-triangle me-2"></i>
                {error}
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Reward Notifications */}
      <RewardNotifications />

      {/* Main Content Row */}
      <Row>
        {/* Full Width Column */}
        <Col lg={12} className="mb-4">
          {/* Enhanced TeoCoin Dashboard */}
          <StudentTeoCoinDashboard />

          {/* Courses */}
          <Card className="mb-4">
            <Card.Header>
              <Card.Title as="h5">
                <i className="feather icon-book me-2"></i>
                I Tuoi Corsi
              </Card.Title>
            </Card.Header>
            <Card.Body>
              {courses.length === 0 ? (
                <div className="text-center py-4">
                  <i className="feather icon-book-open" style={{ fontSize: '3rem', color: '#999', marginBottom: '1rem' }}></i>
                  <h4 className="mb-3">Nessun corso acquistato</h4>
                  <p className="text-muted mb-4">Inizia il tuo percorso di apprendimento acquistando il tuo primo corso</p>
                  <Link to="/corsi" className="btn btn-primary">
                    <i className="feather icon-search me-2"></i>
                    Esplora Corsi
                  </Link>
                </div>
              ) : (
                <div className="row">
                  {courses.map(course => (
                    <div key={course.id} className="col-12 col-lg-6 mb-3">
                      <Card className="h-100 course-card border-0 shadow-sm">
                        <Card.Body className="p-4">
                          {/* Header with title and level */}
                          <div className="d-flex justify-content-between align-items-start mb-3">
                            <div className="flex-grow-1">
                              <h6 className="card-title mb-2 fw-bold text-dark">{course.title}</h6>
                              <div className="d-flex align-items-center gap-2 mb-2">
                                <span className={`badge ${getLevelBadgeClass(course.level || 'Beginner')}`}>
                                  <i className="feather icon-award me-1"></i>
                                  {course.level || 'Beginner'}
                                </span>
                                <small className="text-muted">
                                  <i className="feather icon-calendar me-1"></i>
                                  {course.created_at ? new Date(course.created_at).toLocaleDateString('it-IT') : 'N/A'}
                                </small>
                              </div>
                            </div>
                            <div className="course-price">
                              <span className="text-primary fw-bold">{course.price} TEO</span>
                            </div>
                          </div>

                          {/* Description */}
                          <p className="card-text text-muted small mb-3" style={{ minHeight: '60px' }}>
                            {course.description && course.description.length > 120 
                              ? course.description.substring(0, 120) + '...' 
                              : course.description}
                          </p>

                          {/* Progress section */}
                          <div className="mb-3">
                            <div className="d-flex justify-content-between align-items-center mb-2">
                              <small className="text-muted fw-medium">Progresso</small>
                              <small className="text-primary fw-bold">
                                {calculateCourseProgress(course)}%
                              </small>
                            </div>
                            <div className="progress" style={{ height: '6px' }}>
                              <div 
                                className="progress-bar bg-primary" 
                                role="progressbar" 
                                style={{ width: `${calculateCourseProgress(course)}%` }}
                                aria-valuenow={calculateCourseProgress(course)} 
                                aria-valuemin="0" 
                                aria-valuemax="100"
                              ></div>
                            </div>
                          </div>

                          {/* Stats */}
                          <div className="row g-2 mb-3">
                            <div className="col-4">
                              <div className="text-center p-2 bg-light rounded">
                                <div className="fw-bold text-primary small">{course.lessons_count || 0}</div>
                                <div className="text-muted" style={{ fontSize: '0.75rem' }}>Lezioni</div>
                              </div>
                            </div>
                            <div className="col-4">
                              <div className="text-center p-2 bg-light rounded">
                                <div className="fw-bold text-success small">{course.exercises_count || 0}</div>
                                <div className="text-muted" style={{ fontSize: '0.75rem' }}>Esercizi</div>
                              </div>
                            </div>
                            <div className="col-4">
                              <div className="text-center p-2 bg-light rounded">
                                <div className="fw-bold text-warning small">{course.completed_lessons || 0}</div>
                                <div className="text-muted" style={{ fontSize: '0.75rem' }}>Completate</div>
                              </div>
                            </div>
                          </div>

                          {/* Action button */}
                          <div className="d-grid">
                            <Link 
                              to={`/corsi/${course.id}`} 
                              className="btn btn-primary btn-sm d-flex align-items-center justify-content-center"
                            >
                              <i className="feather icon-play-circle me-2"></i>
                              {calculateCourseProgress(course) > 0 ? 'Continua Corso' : 'Inizia Corso'}
                            </Link>
                          </div>
                        </Card.Body>
                      </Card>
                    </div>
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>

          {/* Student Submissions - Spostato qui dopo i corsi */}
          <Card>
            <Card.Header>
              <Card.Title as="h5">
                <i className="feather icon-file-text me-2"></i>
                Esercizi Sottomessi
              </Card.Title>
            </Card.Header>
            <Card.Body>
              <StudentSubmissions />
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </React.Fragment>
  );
};

export default StudentDashboard;

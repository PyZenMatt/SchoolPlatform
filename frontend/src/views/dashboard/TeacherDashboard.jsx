import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Table, Button, Modal, Spinner, Badge } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import './TeacherDashboard.css';

import WalletBalanceDisplay from '../../components/blockchain/WalletBalanceDisplay';
import ProfileWalletDisplay from '../../components/blockchain/ProfileWalletDisplay';
import DashboardTransactionHistory from '../../components/blockchain/DashboardTransactionHistory';
import { fetchTeacherDashboard, fetchUserProfile } from '../../services/api/dashboard';
import { fetchLessonsForCourse } from '../../services/api/courses';
import CourseCreateModal from '../../components/CourseCreateModal';
import LessonCreateModal from '../../components/LessonCreateModal';
import ExerciseCreateModal from '../../components/ExerciseCreateModal';

// Import dashboard styles
import './dashboard-styles.css';

// Placeholder avatar
import avatar1 from '../../assets/images/user/avatar-1.jpg';

const TeacherDashboard = () => {
  const [courses, setCourses] = useState([]);
  const [sales, setSales] = useState({ daily: 0, monthly: 0, yearly: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  
  // Course expansion and lesson management
  const [expandedCourse, setExpandedCourse] = useState(null);
  const [courseLessons, setCourseLessons] = useState({});
  const [loadingLessons, setLoadingLessons] = useState({});
  const [showLessonModal, setShowLessonModal] = useState({});
  
  // Exercise management
  const [showExerciseModal, setShowExerciseModal] = useState({});
  const [selectedLesson, setSelectedLesson] = useState(null);

  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      setError('');
      try {
        // Fetch user profile
        const profileRes = await fetchUserProfile();
        setUserProfile(profileRes.data);
        
        const res = await fetchTeacherDashboard();
        setCourses(res.data.courses);
        setSales(res.data.sales);
        setTransactions(res.data.transactions || []);
      } catch (err) {
        console.error('Errore API dashboard:', err, err.response?.data);
        setError('Errore nel caricamento della dashboard');
      } finally {
        setLoading(false);
      }
    };
    loadDashboard();
  }, []);

  // Course expansion handling
  const handleExpandCourse = async (courseId) => {
    if (expandedCourse === courseId) {
      setExpandedCourse(null);
      return;
    }
    
    setExpandedCourse(courseId);
    setLoadingLessons(prev => ({ ...prev, [courseId]: true }));
    
    try {
      const res = await fetchLessonsForCourse(courseId);
      setCourseLessons(prev => ({ ...prev, [courseId]: res.data }));
    } catch (err) {
      console.error('Errore caricamento lezioni:', err);
      setCourseLessons(prev => ({ ...prev, [courseId]: [] }));
    } finally {
      setLoadingLessons(prev => ({ ...prev, [courseId]: false }));
    }
  };

  // Lesson modal management
  const handleShowLessonModal = (courseId) => {
    setShowLessonModal(prev => ({ ...prev, [courseId]: true }));
  };
  
  const handleHideLessonModal = (courseId) => {
    setShowLessonModal(prev => ({ ...prev, [courseId]: false }));
  };
  
  const handleLessonCreated = async (courseId) => {
    // Refresh lessons for the course
    try {
      setLoadingLessons(prev => ({ ...prev, [courseId]: true }));
      const res = await fetchLessonsForCourse(courseId);
      setCourseLessons(prev => ({ ...prev, [courseId]: res.data }));
    } catch (error) {
      console.error('Error refreshing lessons:', error);
      setCourseLessons(prev => ({ ...prev, [courseId]: [] }));
    } finally {
      setLoadingLessons(prev => ({ ...prev, [courseId]: false }));
    }
    handleHideLessonModal(courseId);
  };

  // Exercise management functions
  const handleShowExerciseModal = (lesson) => {
    setSelectedLesson(lesson);
    setShowExerciseModal(prev => ({ ...prev, [lesson.id]: true }));
  };

  const handleHideExerciseModal = (lessonId) => {
    setShowExerciseModal(prev => ({ ...prev, [lessonId]: false }));
    setSelectedLesson(null);
  };

  const handleExerciseCreated = async (lessonId, courseId) => {
    // Refresh lessons for the course to show updated exercise count
    try {
      setLoadingLessons(prev => ({ ...prev, [courseId]: true }));
      const res = await fetchLessonsForCourse(courseId);
      setCourseLessons(prev => ({ ...prev, [courseId]: res.data }));
    } catch (error) {
      console.error('Error refreshing lessons:', error);
    } finally {
      setLoadingLessons(prev => ({ ...prev, [courseId]: false }));
    }
    handleHideExerciseModal(lessonId);
  };

  // Dashboard stats data in unified Student Dashboard format
  const dashStatsData = [
    { 
      title: 'Corsi Creati', 
      amount: courses.length.toString(), 
      icon: 'icon-book-open text-c-green', 
      value: 85, 
      class: 'progress-c-theme' 
    },
    { 
      title: 'Vendite Mensili', 
      amount: `€${sales.monthly}`, 
      icon: 'icon-trending-up text-c-green', 
      value: 75, 
      class: 'progress-c-theme2' 
    },
    { 
      title: 'Vendite Totali', 
      amount: `€${sales.yearly}`, 
      icon: 'icon-award text-c-green', 
      value: 90, 
      class: 'progress-c-theme3' 
    }
  ];

  if (loading) {
    return (
      <div className="container-fluid">
        <div className="row">
          <div className="col-md-12">
            <div className="card">
              <div className="card-body">
                <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '400px' }}>
                  <div className="text-center">
                    <div className="spinner-border text-primary" role="status">
                      <span className="visually-hidden">Caricamento...</span>
                    </div>
                    <p className="mt-3">Caricamento dashboard...</p>
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
                Benvenuto, {userProfile?.first_name || userProfile?.username || 'Insegnante'}!
              </h2>
              <p className="text-muted mt-3">Gestisci i tuoi corsi e monitora le tue vendite dalla dashboard.</p>
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

      {/* Main Content Row */}
      <Row>
        {/* Full Width Column - following StudentDashboard layout */}
        <Col lg={12} className="mb-4">
          {/* Wallet Balance Display - Unified style with StudentDashboard */}
          <Row className="mb-4">
            {/* Balance Card - TEO and MATIC */}
            <Col md={6} lg={4}>
              <Card className="balance-card h-100 wallet-transactions-unified">
                <Card.Body>
                  <div className="d-flex justify-content-between align-items-start mb-3">
                    <div className="h6 text-muted mb-0 card-title h5">Saldi Wallet</div>
                  </div>
                  <WalletBalanceDisplay user={userProfile} />
                </Card.Body>
              </Card>
            </Col>

            {/* Wallet Address Card */}
            <Col md={6} lg={4}>
              <Card className="wallet-address-card h-100 wallet-transactions-unified">
                <Card.Body>
                  <div className="h6 text-muted mb-3">Indirizzo Wallet</div>
                  <ProfileWalletDisplay />
                </Card.Body>
              </Card>
            </Col>

            {/* Teacher Stats Card */}
            <Col md={6} lg={4}>
              <Card className="teacher-stats-card h-100">
                <Card.Body>
                  <div className="h6 text-muted mb-3">Statistiche</div>
                  <div className="stats-info">
                    <div className="stat-item mb-2">
                      <div className="stat-value">{courses.length}</div>
                      <div className="stat-label">Corsi Creati</div>
                    </div>
                    <div className="stat-item mb-2">
                      <div className="stat-value">€{sales.monthly}</div>
                      <div className="stat-label">Vendite Mensili</div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-value">€{sales.yearly}</div>
                      <div className="stat-label">Vendite Totali</div>
                    </div>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>

          {/* Courses Management Section */}
          <Card>
            <Card.Header className="d-flex justify-content-between align-items-center">
              <Card.Title as="h5">
                <i className="feather icon-book me-2"></i>
                I Miei Corsi
              </Card.Title>
              <Button 
                variant="primary" 
                size="sm"
                onClick={() => setShowCreateModal(true)}
              >
                <i className="feather icon-plus me-1"></i>
                Nuovo Corso
              </Button>
            </Card.Header>
            <Card.Body>
              {courses.length === 0 ? (
                <div className="text-center py-4">
                  <i className="feather icon-book" style={{ fontSize: '3rem', color: '#999', marginBottom: '1rem' }}></i>
                  <h4 className="mb-3">Nessun corso creato</h4>
                  <p className="text-muted mb-4">Inizia creando il tuo primo corso</p>
                  <Button 
                    variant="primary"
                    onClick={() => setShowCreateModal(true)}
                  >
                    <i className="feather icon-plus me-2"></i>
                    Crea Primo Corso
                  </Button>
                </div>
              ) : (
                <div className="table-responsive">
                  <Table striped hover>
                    <thead>
                      <tr>
                        <th>Corso</th>
                        <th>Lezioni</th>
                        <th>Prezzo</th>
                        <th>Creato</th>
                        <th>Azioni</th>
                      </tr>
                    </thead>
                    <tbody>
                      {courses.map(course => (
                        <React.Fragment key={course.id}>
                          <tr 
                            className={expandedCourse === course.id ? 'table-active' : ''}
                            style={{ cursor: 'pointer' }}
                          >
                            <td onClick={() => handleExpandCourse(course.id)}>
                              <div className="d-flex align-items-center">
                                <i className={`feather ${expandedCourse === course.id ? 'icon-chevron-down' : 'icon-chevron-right'} me-2`}></i>
                                <div>
                                  <strong>{course.title}</strong>
                                  <br />
                                  <small className="text-muted">{course.description?.substring(0, 50)}...</small>
                                </div>
                              </div>
                            </td>
                            <td>
                              <Badge bg="info">{course.lessons_count || 0} lezioni</Badge>
                            </td>
                            <td>
                              <strong>{course.price} TEO</strong>
                            </td>
                            <td>
                              <small>{new Date(course.created_at).toLocaleDateString('it-IT')}</small>
                            </td>
                            <td>
                              <div className="d-flex gap-1">
                                <Button
                                  variant="outline-primary"
                                  size="sm"
                                  onClick={() => handleShowLessonModal(course.id)}
                                >
                                  <i className="feather icon-plus me-1"></i>
                                  Lezione
                                </Button>
                                <Link to={`/corsi/${course.id}`} className="btn btn-outline-secondary btn-sm">
                                  <i className="feather icon-eye"></i>
                                </Link>
                              </div>
                            </td>
                          </tr>
                          
                          {/* Lessons List */}
                          {expandedCourse === course.id && (
                            <tr>
                              <td colSpan="5" className="p-0">
                                <div className="bg-light p-3">
                                  {loadingLessons[course.id] ? (
                                    <div className="text-center py-2">
                                      <Spinner animation="border" size="sm" className="me-2" />
                                      Caricamento lezioni...
                                    </div>
                                  ) : courseLessons[course.id]?.length > 0 ? (
                                    <div className="lessons-list">
                                      <h6 className="mb-3">Lezioni del corso:</h6>
                                      {courseLessons[course.id].map(lesson => (
                                        <div key={lesson.id} className="lesson-item d-flex justify-content-between align-items-center mb-2 p-2 bg-white rounded border">
                                          <div>
                                            <strong>{lesson.title}</strong>
                                            <br />
                                            <small className="text-muted">
                                              {lesson.exercises_count || 0} esercizi
                                            </small>
                                          </div>
                                          <div>
                                            <Button
                                              variant="outline-success"
                                              size="sm"
                                              onClick={() => handleShowExerciseModal(lesson)}
                                            >
                                              <i className="feather icon-plus me-1"></i>
                                              Esercizio
                                            </Button>
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  ) : (
                                    <div className="text-center py-3">
                                      <p className="text-muted mb-0">Nessuna lezione ancora creata per questo corso</p>
                                    </div>
                                  )}
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      ))}
                    </tbody>
                  </Table>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>

        {/* Transactions History */}
        <Col lg={12}>
          <Card className="wallet-transactions-unified">
            <Card.Body>
              <DashboardTransactionHistory user={userProfile} />
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Modals */}
      <CourseCreateModal 
        show={showCreateModal} 
        handleClose={() => setShowCreateModal(false)} 
      />
      
      {/* Lesson Creation Modals */}
      {Object.keys(showLessonModal).map(courseId => (
        <LessonCreateModal
          key={`lesson-${courseId}`}
          show={showLessonModal[courseId]}
          handleClose={() => handleHideLessonModal(courseId)}
          courseId={courseId}
          onLessonCreated={() => handleLessonCreated(courseId)}
        />
      ))}
      
      {/* Exercise Creation Modals */}
      {Object.keys(showExerciseModal).map(lessonId => (
        <ExerciseCreateModal
          key={`exercise-${lessonId}`}
          show={showExerciseModal[lessonId]}
          handleClose={() => handleHideExerciseModal(lessonId)}
          lesson={selectedLesson}
          onExerciseCreated={() => handleExerciseCreated(lessonId, selectedLesson?.course)}
        />
      ))}
    </React.Fragment>
  );
};

export default TeacherDashboard;

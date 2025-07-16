import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Button, Modal, Spinner, Badge } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import './TeacherDashboard.css';

import StudentTeoCoinDashboard from '../../components/blockchain/DBStudentTeoCoinDashboard';
import ZeroMaticStakingInterface from '../../components/blockchain/DBStakingInterface';
import TeoCoinBalanceWidget from '../../components/TeoCoinBalanceWidget';
import StatCard from '../../components/common/StatCard';
import CoursesTable from '../../components/courses/CoursesTable';
import { fetchTeacherDashboard, fetchUserProfile } from '../../services/api/dashboard';
import { fetchLessonsForCourse, fetchExercisesForLesson } from '../../services/api/courses';
import CourseCreateModal from '../../components/modals/CourseCreateModal';
import LessonCreateModal from '../../components/modals/LessonCreateModal';
import ExerciseCreateModal from '../../components/modals/ExerciseCreateModal';
import TeacherDiscountDashboard from '../../components/discount/DBTeacherDiscountDashboard';
import TeacherDiscountAbsorptionDashboard from '../../components/discount/TeacherDiscountAbsorptionDashboard';

// Import dashboard styles
import './dashboard-styles.css';

// Placeholder avatar
import avatar1 from '../../assets/images/user/avatar-1.jpg';

const TeacherDashboard = () => {
  const navigate = useNavigate();
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
  const [lessonExercises, setLessonExercises] = useState({});
  const [loadingExercises, setLoadingExercises] = useState({});

  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      setError('');
      try {
        // Fetch user profile
        const profileRes = await fetchUserProfile();
        setUserProfile(profileRes.data);
        
        const res = await fetchTeacherDashboard();
        console.log('🔍 TeacherDashboard API Response:', res);
        setCourses(res.data.courses);
        setSales(res.data.sales);
        setTransactions(res.data.transactions || []);
        console.log('📚 Courses set in state:', res.data.courses);
        
        // Popola le lezioni da subito con i dati che arrivano dall'API
        const lessonsData = {};
        res.data.courses.forEach(course => {
          if (course.lessons && course.lessons.length > 0) {
            lessonsData[course.id] = course.lessons;
          }
        });
        setCourseLessons(lessonsData);
        console.log('📖 Lessons populated from API:', lessonsData);
        
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
    
    // Se le lezioni sono già presenti, non fare chiamata API
    if (courseLessons[courseId]) {
      console.log('📖 Lessons already loaded for course:', courseId);
      return;
    }
    
    setLoadingLessons(prev => ({ ...prev, [courseId]: true }));
    
    try {
      const res = await fetchLessonsForCourse(courseId);
      setCourseLessons(prev => ({ ...prev, [courseId]: res.data }));
      console.log('📖 Lessons loaded from API for course:', courseId, res.data);
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

  // Load exercises for a lesson
  const loadExercisesForLesson = async (lessonId) => {
    try {
      setLoadingExercises(prev => ({ ...prev, [lessonId]: true }));
      const res = await fetchExercisesForLesson(lessonId);
      setLessonExercises(prev => ({ ...prev, [lessonId]: res.data }));
    } catch (error) {
      console.error('Error loading exercises:', error);
      setLessonExercises(prev => ({ ...prev, [lessonId]: [] }));
    } finally {
      setLoadingExercises(prev => ({ ...prev, [lessonId]: false }));
    }
  };

  // Exercise management functions
  const handleShowExerciseModal = (lesson) => {
    console.log('🎯 Selected lesson for exercise creation:', lesson);
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

  // Navigation functions
  const handleViewCourse = (courseId) => {
    navigate(`/corsi-docente/${courseId}`);
  };

  const handleViewLesson = (lessonId) => {
    navigate(`/lezioni-docente/${lessonId}`);
  };

  const handleEditCourse = (courseId) => {
    navigate(`/teacher/corsi/${courseId}/edit`);
  };

  const handleEditLesson = (lessonId) => {
    navigate(`/teacher/lezioni/${lessonId}/edit`);
  };

  const handleViewExercise = (exerciseId) => {
    navigate(`/esercizi-docente/${exerciseId}`);
  };

  const handleEditExercise = (exerciseId) => {
    navigate(`/teacher/esercizi/${exerciseId}/edit`);
  };

  // Dashboard stats data per StatCard component
  const dashStatsData = [
    { 
      title: 'Corsi Creati', 
      value: courses.length.toString(), 
      icon: 'book-open',
      percentage: 85, 
      progressColor: 'progress-c-theme',
      iconColor: 'text-c-green'
    },
    { 
      title: 'Vendite Mensili', 
      value: `€${sales.monthly}`, 
      icon: 'trending-up',
      percentage: 75, 
      progressColor: 'progress-c-theme2',
      iconColor: 'text-c-green'
    },
    { 
      title: 'Vendite Totali', 
      value: `€${sales.yearly}`, 
      icon: 'award',
      percentage: 90, 
      progressColor: 'progress-c-theme3',
      iconColor: 'text-c-green'
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
        {dashStatsData.map((data, index) => (
          <Col key={index} md={6} xl={4}>
            <StatCard 
              title={data.title}
              value={data.value}
              icon={data.icon}
              percentage={data.percentage}
              progressColor={data.progressColor}
              iconColor={data.iconColor}
            />
          </Col>
        ))}
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
          {/* TeoCoin Dashboard and Withdrawal */}
          <Row className="mb-4">
            <Col lg={6}>
              <StudentTeoCoinDashboard />
            </Col>
            <Col lg={6}>
              <TeoCoinBalanceWidget />
            </Col>
          </Row>

          {/* Staking Interface */}
          <Row className="mb-4">
            <Col lg={12}>
              <Card>
                <Card.Header>
                  <Card.Title as="h5">
                    <i className="feather icon-trending-up me-2"></i>
                    Gas-Free TeoCoin Staking System
                    <Badge bg="success" className="ms-2">0 MATIC Cost</Badge>
                  </Card.Title>
                  <p className="mb-0 text-muted">
                    Stake your TeoCoin to reduce platform commission rates - No gas fees required!
                  </p>
                </Card.Header>
                <Card.Body>
                  <ZeroMaticStakingInterface 
                    walletAddress={userProfile?.wallet_address}
                    onStakingUpdate={(data) => {
                      // Refresh dashboard data after staking operation
                      loadDashboard();
                    }}
                  />
                </Card.Body>
              </Card>
            </Col>
          </Row>

          {/* TeoCoin Escrow Manager */}
          <Row className="mb-4">
            <Col lg={12}>
              <TeacherDiscountDashboard />
            </Col>
          </Row>

          {/* Teacher Discount Absorption System */}
          <Row className="mb-4">
            <Col lg={12}>
              <TeacherDiscountAbsorptionDashboard />
            </Col>
          </Row>

          {/* Teacher Choice Dashboard */}
          <Row className="mb-4">
            <Col lg={12}>
              <Card>
                <Card.Header>
                  <Card.Title as="h5">
                    <i className="feather icon-target me-2"></i>
                    TeoCoin Choice Dashboard
                    <Badge bg="warning" className="ms-2">Layer 2</Badge>
                  </Card.Title>
                  <p className="mb-0 text-muted">
                    Make decisions on student discount requests - TEO payment or full fiat
                  </p>
                </Card.Header>
                <Card.Body className="text-center">
                  <p>View and decide on pending TeoCoin payment choices from students.</p>
                  <Link to="/teacher/choices" className="btn btn-primary">
                    <i className="feather icon-target me-2"></i>
                    Open Choice Dashboard
                  </Link>
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
                <CoursesTable
                  courses={courses}
                  showActions={true}
                  onCreateLesson={handleShowLessonModal}
                  expandedCourse={expandedCourse}
                  onExpandCourse={handleExpandCourse}
                  courseLessons={courseLessons}
                  loadingLessons={loadingLessons}
                  onCreateExercise={handleShowExerciseModal}
                  lessonExercises={lessonExercises}
                  loadingExercises={loadingExercises}
                  onLoadExercises={loadExercisesForLesson}
                  onViewCourse={handleViewCourse}
                  onViewLesson={handleViewLesson}
                  onEditCourse={handleEditCourse}
                  onEditLesson={handleEditLesson}
                  onViewExercise={handleViewExercise}
                  onEditExercise={handleEditExercise}
                />
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Modals */}
      <CourseCreateModal 
        show={showCreateModal} 
        onHide={() => setShowCreateModal(false)} 
      />
      
      {/* Lesson Creation Modals */}
      {Object.keys(showLessonModal).map(courseId => (
        <LessonCreateModal
          key={`lesson-${courseId}`}
          show={showLessonModal[courseId]}
          onHide={() => handleHideLessonModal(courseId)}
          courseId={courseId}
          onCreated={() => handleLessonCreated(courseId)}
        />
      ))}
      
      {/* Exercise Creation Modals */}
      {Object.keys(showExerciseModal).map(lessonId => (
        <ExerciseCreateModal
          key={`exercise-${lessonId}`}
          show={showExerciseModal[lessonId]}
          onHide={() => handleHideExerciseModal(lessonId)}
          lessonId={selectedLesson?.id}
          courseId={selectedLesson?.course_id || selectedLesson?.course}
          lesson={selectedLesson}
          onCreated={() => handleExerciseCreated(lessonId, selectedLesson?.course_id || selectedLesson?.course)}
        />
      ))}
    </React.Fragment>
  );
};

export default TeacherDashboard;

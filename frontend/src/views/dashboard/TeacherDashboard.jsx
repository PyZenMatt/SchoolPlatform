import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Table, Button, Modal, Spinner, Badge } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import './TeacherDashboard.css';

import WalletBalanceDisplay from '../../components/blockchain/WalletBalanceDisplay';
import ProfileWalletDisplay from '../../components/blockchain/ProfileWalletDisplay';
import TransactionHistory from '../../components/blockchain/TransactionHistory';
import { fetchTeacherDashboard, fetchUserProfile } from '../../services/api/dashboard';
import { fetchLessonsForCourse } from '../../services/api/courses';
import CourseCreateModal from '../../components/CourseCreateModal';
import LessonCreateModal from '../../components/LessonCreateModal';
import ExerciseCreateModal from '../../components/ExerciseCreateModal';

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

  // Dashboard stats data in Datta Able format
  const dashStatsData = [
    { 
      title: 'Vendite Giornaliere', 
      amount: `€${sales.daily}`, 
      icon: 'fas fa-coins', 
      color: 'c1' 
    },
    { 
      title: 'Vendite Mensili', 
      amount: `€${sales.monthly}`, 
      icon: 'fas fa-calendar-check', 
      color: 'c2' 
    },
    { 
      title: 'Corsi Attivi', 
      amount: courses.length, 
      icon: 'fas fa-book', 
      color: 'c3' 
    },
  ];

  return (
    <React.Fragment>
      
      {loading ? (
        <div className="text-center my-5">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Caricamento...</span>
          </Spinner>
          <p className="mt-2">Caricamento dashboard...</p>
        </div>
      ) : error ? (
        <div className="alert alert-danger">{error}</div>
      ) : (
        <>
          {/* Stats Cards */}
          <Row>
            {dashStatsData.map((stat, idx) => (
              <Col md={4} key={idx}>
                <Card>
                  <Card.Body className="p-0">
                    <div className={`widget-card-1 card-${stat.color}`}>
                      <div className="icon">
                        <i className={stat.icon}></i>
                      </div>
                      <div className="info">
                        <h5 className="title">{stat.title}</h5>
                        <h2 className="value">{stat.amount}</h2>
                      </div>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>

          {/* User Profile Section */}
          <Row className="mb-4">
            <Col md={12}>
              <Card>
                <Card.Body className="d-flex align-items-center">
                  <div className="teacher-profile-img me-4">
                    <img src={userProfile?.avatar || avatar1} alt="Teacher" className="rounded-circle" width="80" />
                  </div>
                  <div className="teacher-profile-info">
                    <h4 className="mb-1">{`${userProfile?.first_name || ''} ${userProfile?.last_name || ''}`}</h4>
                    <p className="text-muted mb-2">Insegnante di {userProfile?.profession || 'Arte'}</p>
                    {userProfile?.bio && <p className="mb-2">{userProfile.bio}</p>}
                    <div className="d-flex">
                      <Link to="/profile" className="btn btn-sm btn-outline-primary me-2">
                        <i className="fas fa-user me-1"></i> Profilo
                      </Link>
                      <Link to="/wallet" className="btn btn-sm btn-outline-info">
                        <i className="fas fa-wallet me-1"></i> Wallet
                      </Link>
                    </div>
                  </div>
                  <div className="ms-auto">
                    <div className="d-flex gap-2 align-items-center">
                      <WalletBalanceDisplay />
                      <ProfileWalletDisplay />
                    </div>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>

          {/* Create Course Button */}
          <Row className="mb-4">
            <Col md={12}>
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h3 className="mb-0">I Tuoi Corsi</h3>
                <Button 
                  variant="primary" 
                  onClick={() => setShowCreateModal(true)}
                >
                  <i className="fas fa-plus me-2"></i>
                  Crea Nuovo Corso
                </Button>
              </div>
            </Col>
          </Row>

          {/* Courses Table */}
          <Row className="mb-4">
            <Col md={12}>
              <Card>
                <Card.Body>
                  <div className="table-responsive">
                    <Table striped hover>
                      <thead>
                        <tr>
                          <th>Titolo</th>
                          <th>Categoria</th>
                          <th>Prezzo</th>
                          <th>Studenti</th>
                          <th>Guadagni</th>
                          <th>Azioni</th>
                        </tr>
                      </thead>
                      <tbody>
                        {courses.length === 0 ? (
                          <tr>
                            <td colSpan="6" className="text-center py-4">
                              <p className="mb-2">Non hai ancora creato corsi</p>
                              <Button 
                                variant="primary" 
                                size="sm"
                                onClick={() => setShowCreateModal(true)}
                              >
                                <i className="fas fa-plus me-2"></i>
                                Crea il tuo primo corso
                              </Button>
                            </td>
                          </tr>
                        ) : (
                          courses.map(course => (
                            <React.Fragment key={course.id}>
                              <tr 
                                onClick={() => handleExpandCourse(course.id)}
                                className={`lesson-row ${expandedCourse === course.id ? 'table-active' : ''}`}
                              >
                                <td>
                                  <div className="d-flex align-items-center">
                                    {expandedCourse === course.id ? (
                                      <i className="fas fa-caret-down me-2"></i>
                                    ) : (
                                      <i className="fas fa-caret-right me-2"></i>
                                    )}
                                    {course.title}
                                  </div>
                                </td>
                                <td>{course.category_name || 'N/A'}</td>
                                <td>€{course.price}</td>
                                <td>{course.students_count}</td>
                                <td>€{(course.price * course.students_count * 0.9).toFixed(2)}</td>
                                <td>
                                  <Link 
                                    to={`/courses/${course.id}/edit`} 
                                    className="btn btn-sm btn-primary me-2"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    <i className="fas fa-edit"></i>
                                  </Link>
                                </td>
                              </tr>
                              
                              {/* Expanded Course Details */}
                              {expandedCourse === course.id && (
                                <tr>
                                  <td colSpan="6" className="p-0">
                                    <div className="p-3 bg-light">
                                      <div className="d-flex justify-content-between mb-3">
                                        <h5>Lezioni</h5>
                                        <Button
                                          variant="outline-primary"
                                          size="sm"
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleShowLessonModal(course.id);
                                          }}
                                        >
                                          <i className="fas fa-plus me-1"></i>
                                          Aggiungi Lezione
                                        </Button>
                                      </div>
                                      
                                      {loadingLessons[course.id] ? (
                                        <div className="text-center py-3">
                                          <Spinner animation="border" size="sm" />
                                          <span className="ms-2">Caricamento lezioni...</span>
                                        </div>
                                      ) : courseLessons[course.id]?.length > 0 ? (
                                        <Table bordered size="sm">
                                          <thead>
                                            <tr>
                                              <th>Titolo</th>
                                              <th>Durata</th>
                                              <th>Esercizi</th>
                                              <th>Azioni</th>
                                            </tr>
                                          </thead>
                                          <tbody>
                                            {courseLessons[course.id].map(lesson => (
                                              <tr key={lesson.id}>
                                                <td>
                                                  <div className="d-flex align-items-center">
                                                    <span className="me-2">
                                                      {lesson.lesson_type === 'video' && <i className="fas fa-video text-warning"></i>}
                                                      {lesson.lesson_type === 'theory' && <i className="fas fa-book text-primary"></i>}
                                                      {lesson.lesson_type === 'practical' && <i className="fas fa-tools text-success"></i>}
                                                      {lesson.lesson_type === 'mixed' && <i className="fas fa-layer-group text-info"></i>}
                                                    </span>
                                                    {lesson.title}
                                                  </div>
                                                </td>
                                                <td>{lesson.duration} min</td>
                                                <td>
                                                  <div className="d-flex align-items-center justify-content-between">
                                                    <Badge bg="secondary" className="me-2">
                                                      {(lesson.exercises_count || 0)} esercizi
                                                    </Badge>
                                                    <Button
                                                      variant="outline-success"
                                                      size="sm"
                                                      onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleShowExerciseModal({ ...lesson, course_id: course.id });
                                                      }}
                                                      title="Aggiungi esercizio"
                                                    >
                                                      <i className="fas fa-plus"></i>
                                                    </Button>
                                                  </div>
                                                </td>
                                                <td>
                                                  <Link 
                                                    to={`/courses/${course.id}/lessons/${lesson.id}/edit`}
                                                    className="btn btn-sm btn-outline-primary me-1"
                                                    title="Modifica lezione"
                                                  >
                                                    <i className="fas fa-edit"></i>
                                                  </Link>
                                                  {(lesson.exercises_count || 0) > 0 && (
                                                    <Link
                                                      to={`/courses/${course.id}/lessons/${lesson.id}/exercises`}
                                                      className="btn btn-sm btn-outline-info"
                                                      title="Gestisci esercizi"
                                                    >
                                                      <i className="fas fa-list"></i>
                                                    </Link>
                                                  )}
                                                </td>
                                              </tr>
                                            ))}
                                          </tbody>
                                        </Table>
                                      ) : (
                                        <div className="text-center py-3">
                                          <p className="mb-2">Nessuna lezione creata</p>
                                          <Button
                                            variant="outline-primary"
                                            size="sm"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              handleShowLessonModal(course.id);
                                            }}
                                          >
                                            Crea la prima lezione
                                          </Button>
                                        </div>
                                      )}
                                    </div>
                                  </td>
                                </tr>
                              )}
                            </React.Fragment>
                          ))
                        )}
                      </tbody>
                    </Table>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>

          {/* Transactions History */}
          <Row>
            <Col md={12}>
              <Card>
                <Card.Header>
                  <h5>Storia Transazioni</h5>
                </Card.Header>
                <Card.Body>
                  <TransactionHistory transactions={transactions} />
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </>
      )}

      {/* Course Creation Modal */}
      {showCreateModal && (
        <CourseCreateModal
          show={showCreateModal}
          onHide={() => setShowCreateModal(false)}
          onCreated={(newCourse) => {
            setCourses(prev => [...prev, newCourse]);
            setShowCreateModal(false);
          }}
        />
      )}

      {/* Lesson Creation Modals */}
      {Object.entries(showLessonModal).map(([courseId, show]) => 
        show && (
          <LessonCreateModal
            key={courseId}
            show={show}
            onHide={() => handleHideLessonModal(courseId)}
            onCreated={() => handleLessonCreated(courseId)}
            courseId={parseInt(courseId)}
          />
        )
      )}

      {/* Exercise Create Modals */}
      {Object.entries(showExerciseModal).map(([lessonId, show]) => 
        show && selectedLesson && (
          <ExerciseCreateModal
            key={lessonId}
            show={show}
            onHide={() => handleHideExerciseModal(lessonId)}
            onCreated={() => handleExerciseCreated(lessonId, selectedLesson.course_id)}
            lessonId={parseInt(lessonId)}
            courseId={selectedLesson.course_id}
          />
        )
      )}
    </React.Fragment>
  );
};

export default TeacherDashboard;

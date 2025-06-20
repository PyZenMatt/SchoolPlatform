import React, { useState } from 'react';
import { Card, Badge, Button, Row, Col, Collapse } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import './CoursesTable.scss';

const CoursesTable = ({ 
  courses = [], 
  showActions = true, 
  onCreateLesson, 
  showCreateCourse = false,
  onCreateCourse,
  expandedCourse,
  onExpandCourse,
  courseLessons = {},
  onCreateExercise,
  lessonExercises = {},
  loadingExercises = {},
  onLoadExercises,
  onViewCourse,
  onViewLesson,
  onEditCourse,
  onEditLesson,
  onViewExercise,
  onEditExercise
}) => {
  const [expandedLessons, setExpandedLessons] = useState({});
  
  // Debug logs
  console.log('🎯 CoursesTable Props:', {
    courses: courses,
    coursesLength: courses?.length,
    courseLessons,
    expandedCourse,
    showActions,
    firstCourse: courses?.[0]
  });
  
  // Debug each course structure
  if (courses && courses.length > 0) {
    courses.forEach((course, index) => {
      console.log(`📚 Course ${index + 1}:`, {
        id: course.id,
        title: course.title,
        lessons: course.lessons,
        lessonsCount: course.lessons?.length || 0
      });
    });
  }

  const handleToggleLesson = (lessonId) => {
    setExpandedLessons(prev => ({
      ...prev,
      [lessonId]: !prev[lessonId]
    }));
  };

  const formatPrice = (price) => {
    if (!price) return '0';
    return parseFloat(price).toFixed(2);
  };

  const getBadgeVariant = (status) => {
    switch (status?.toLowerCase()) {
      case 'published':
      case 'active':
        return 'success';
      case 'draft':
        return 'warning';
      case 'archived':
        return 'secondary';
      default:
        return 'primary';
    }
  };

  if (!courses || courses.length === 0) {
    return (
      <div className="text-center py-5">
        <div className="mb-4">
          <i className="feather icon-book-open" style={{ fontSize: '3rem', color: '#6c757d' }}></i>
        </div>
        <h5 className="text-muted">Nessun corso trovato</h5>
        <p className="text-muted">Non ci sono corsi disponibili al momento.</p>
        {showCreateCourse && (
          <Button variant="primary" onClick={onCreateCourse}>
            <i className="feather icon-plus me-2"></i>
            Crea il tuo primo corso
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className="courses-grid">
      {showCreateCourse && (
        <Card className="create-course-card mb-4">
          <Card.Body className="text-center py-4">
            <div className="mb-3">
              <i className="feather icon-plus-circle" style={{ fontSize: '2.5rem', color: '#28a745' }}></i>
            </div>
            <h5>Crea Nuovo Corso</h5>
            <p className="text-muted mb-3">Aggiungi un nuovo corso alla tua piattaforma</p>
            <Button variant="success" onClick={onCreateCourse}>
              <i className="feather icon-plus me-2"></i>
              Crea Corso
            </Button>
          </Card.Body>
        </Card>
      )}

      <Row>
        {courses.map(course => (
          <Col lg={6} xl={4} key={course.id} className="mb-4">
            <Card className="course-card h-100">
              <Card.Header className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="mb-1">{course.title}</h6>
                  <Badge variant={getBadgeVariant(course.status)} className="me-2">
                    {course.status || 'Draft'}
                  </Badge>
                  <small className="text-muted">{course.lessons?.length || 0} lezioni</small>
                </div>
                <div className="course-price">
                  <strong>{formatPrice(course.price)} TEO</strong>
                </div>
              </Card.Header>
              
              <Card.Body>
                {course.description && (
                  <p className="text-muted small mb-3">{course.description}</p>
                )}
                
                <div className="course-stats mb-3">
                  <Row className="text-center">
                    <Col>
                      <div className="stat-item">
                        <strong>{course.lessons?.length || 0}</strong>
                        <small className="d-block text-muted">Lezioni</small>
                      </div>
                    </Col>
                    <Col>
                      <div className="stat-item">
                        <strong>{course.total_exercises || 0}</strong>
                        <small className="d-block text-muted">Esercizi</small>
                      </div>
                    </Col>
                    <Col>
                      <div className="stat-item">
                        <strong>{course.students_count || 0}</strong>
                        <small className="d-block text-muted">Studenti</small>
                      </div>
                    </Col>
                  </Row>
                </div>

                {/* Lessons Accordion */}
                {course.lessons && course.lessons.length > 0 && (
                  <div className="lessons-section">
                    <div className="d-flex justify-content-between align-items-center mb-2">
                      <h6 className="mb-0">Lezioni</h6>
                      <Button
                        variant="outline-primary"
                        size="sm"
                        onClick={() => onExpandCourse && onExpandCourse(
                          expandedCourse === course.id ? null : course.id
                        )}
                      >
                        <i className={`feather icon-chevron-${expandedCourse === course.id ? 'up' : 'down'}`}></i>
                      </Button>
                    </div>
                    
                    <Collapse in={expandedCourse === course.id}>
                      <div className="lessons-list">
                        {course.lessons.map((lesson, lessonIndex) => (
                          <div key={lesson.id} className="lesson-item mb-2">
                            <div 
                              className="lesson-header d-flex justify-content-between align-items-center p-2 bg-light rounded cursor-pointer"
                              onClick={() => handleToggleLesson(lesson.id)}
                            >
                              <div>
                                <strong className="d-block">{lesson.title}</strong>
                                <small className="text-muted">
                                  {lesson.exercises?.length || 0} esercizi
                                </small>
                              </div>
                              <div className="d-flex align-items-center">
                                {showActions && (
                                  <>
                                    <Button
                                      variant="outline-secondary"
                                      size="sm"
                                      className="me-1"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        onViewLesson && onViewLesson(lesson);
                                      }}
                                    >
                                      <i className="feather icon-eye"></i>
                                    </Button>
                                    <Button
                                      variant="outline-primary"
                                      size="sm"
                                      className="me-2"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        onEditLesson && onEditLesson(lesson);
                                      }}
                                    >
                                      <i className="feather icon-edit"></i>
                                    </Button>
                                  </>
                                )}
                                <i className={`feather icon-chevron-${expandedLessons[lesson.id] ? 'up' : 'down'}`}></i>
                              </div>
                            </div>
                            
                            <Collapse in={expandedLessons[lesson.id]}>
                              <div className="exercises-section p-2 bg-white border rounded mt-1">
                                <div className="d-flex justify-content-between align-items-center mb-2">
                                  <small className="text-muted font-weight-bold">Esercizi</small>
                                  {onCreateExercise && (
                                    <Button
                                      variant="warning"
                                      size="sm"
                                      onClick={() => onCreateExercise({
                                        ...lesson,
                                        course_id: course.id,
                                        course: course.id
                                      })}
                                    >
                                      <i className="feather icon-plus me-1"></i>
                                      {lesson.exercises?.length === 0 ? 'Crea Primo Esercizio' : 'Aggiungi Esercizio'}
                                    </Button>
                                  )}
                                </div>
                                
                                {lesson.exercises && lesson.exercises.length > 0 ? (
                                  <div className="exercises-list">
                                    {lesson.exercises.map((exercise, exerciseIndex) => (
                                      <div key={exercise.id} className="exercise-item d-flex justify-content-between align-items-center p-2 mb-1 bg-light rounded">
                                        <div>
                                          <strong className="d-block">{exercise.title}</strong>
                                          <small className="text-muted">
                                            Tipo: {exercise.type || 'Non specificato'}
                                          </small>
                                        </div>
                                        {showActions && (
                                          <div>
                                            <Button
                                              variant="outline-secondary"
                                              size="sm"
                                              className="me-1"
                                              onClick={() => onViewExercise && onViewExercise(exercise)}
                                            >
                                              <i className="feather icon-eye"></i>
                                            </Button>
                                            <Button
                                              variant="outline-primary"
                                              size="sm"
                                              onClick={() => onEditExercise && onEditExercise(exercise)}
                                            >
                                              <i className="feather icon-edit"></i>
                                            </Button>
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <div className="text-center py-3">
                                    <small className="text-muted">Nessun esercizio presente</small>
                                  </div>
                                )}
                              </div>
                            </Collapse>
                          </div>
                        ))}
                      </div>
                    </Collapse>
                  </div>
                )}
              </Card.Body>
              
              {showActions && (
                <Card.Footer className="d-flex justify-content-between">
                  <div>
                    <Button
                      variant="outline-secondary"
                      size="sm"
                      className="me-2"
                      onClick={() => onViewCourse && onViewCourse(course)}
                    >
                      <i className="feather icon-eye me-1"></i>
                      Visualizza
                    </Button>
                    <Button
                      variant="outline-primary"
                      size="sm"
                      onClick={() => onEditCourse && onEditCourse(course)}
                    >
                      <i className="feather icon-edit me-1"></i>
                      Modifica
                    </Button>
                  </div>
                  <div>
                    {onCreateLesson && (
                      <Button
                        variant="success"
                        size="sm"
                        onClick={() => onCreateLesson(course)}
                      >
                        <i className="feather icon-plus me-1"></i>
                        Lezione
                      </Button>
                    )}
                  </div>
                </Card.Footer>
              )}
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default CoursesTable;

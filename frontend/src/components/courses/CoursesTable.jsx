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
  loadingLessons = {},
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

  const handleExpandLesson = (lessonId) => {
    const isExpanding = !expandedLessons[lessonId];
    setExpandedLessons(prev => ({
      ...prev,
      [lessonId]: isExpanding
    }));
    
    // Load exercises when expanding a lesson for the first time
    if (isExpanding && !lessonExercises[lessonId] && onLoadExercises) {
      onLoadExercises(lessonId);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit', 
      year: 'numeric'
    });
  };

  if (courses.length === 0) {
    return (
      <div className="text-center py-5">
        <div className="empty-state">
          <i className="feather icon-book-open" style={{ fontSize: '4rem', color: '#ddd', marginBottom: '1rem' }}></i>
          <h4 className="mb-3 text-muted">Nessun corso creato</h4>
          <p className="text-muted mb-4">Inizia creando il tuo primo corso e costruisci la tua biblioteca educativa</p>
          {showCreateCourse && (
            <Button 
              variant="primary"
              size="lg"
              onClick={onCreateCourse}
              className="px-4"
            >
              <i className="feather icon-plus me-2"></i>
              Crea il tuo primo corso
            </Button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="courses-table-modern">
      {courses.map((course) => (
        <Card key={course.id} className="course-card mb-3 shadow-sm">
          <Card.Body className="p-0">
            {/* Course Header */}
            <div 
              className="course-header p-4 cursor-pointer"
              onClick={() => onExpandCourse && onExpandCourse(course.id)}
            >
              <Row className="align-items-center">
                <Col md={8}>
                  <div className="d-flex align-items-center">
                    <div className="course-icon me-3">
                      <i className={`feather ${expandedCourse === course.id ? 'icon-chevron-down' : 'icon-chevron-right'} text-primary`}></i>
                    </div>
                    <div>
                      <div className="d-flex align-items-center mb-2">
                        <Badge bg="primary" className="me-2 course-badge">
                          <i className="feather icon-book me-1"></i>
                          Corso
                        </Badge>
                        <h5 className="mb-0 course-title">{course.title}</h5>
                      </div>
                      <p className="text-muted mb-0 course-description">
                        {course.description || 'Nessuna descrizione disponibile'}
                      </p>
                    </div>
                  </div>
                </Col>
                <Col md={4} className="text-end">
                  <div className="course-meta">
                    <div className="price-tag mb-2">
                      <span className="h4 text-success mb-0">{course.price} TEO</span>
                    </div>
                    <div className="course-stats">
                      <Badge bg="info" className="me-2">
                        {course.lessons_count || 0} lezioni
                      </Badge>
                      <small className="text-muted">
                        Creato: {formatDate(course.created_at)}
                      </small>
                    </div>
                  </div>
                </Col>
              </Row>
            </div>

            {/* Course Content - Expandable */}
            <Collapse in={expandedCourse === course.id}>
              <div className="course-content">
                <div className="border-top bg-light p-4">
                  {/* Actions Row */}
                  {showActions && (
                    <Row className="mb-4">
                      <Col>
                        <div className="d-flex gap-2 flex-wrap">
                          <Button
                            variant="success"
                            size="sm"
                            onClick={() => onCreateLesson && onCreateLesson(course.id)}
                          >
                            <i className="feather icon-plus me-1"></i>
                            Nuova Lezione
                          </Button>
                          <Button 
                            variant="outline-primary" 
                            size="sm"
                            onClick={() => onViewCourse && onViewCourse(course.id)}
                          >
                            <i className="feather icon-eye me-1"></i>
                            Visualizza
                          </Button>
                          <Button 
                            variant="outline-secondary" 
                            size="sm"
                            onClick={() => onEditCourse && onEditCourse(course.id)}
                          >
                            <i className="feather icon-edit me-1"></i>
                            Modifica
                          </Button>
                        </div>
                      </Col>
                    </Row>
                  )}

                  {/* Lessons Section */}
                  <div className="lessons-section">
                    <h6 className="section-title mb-3">
                      <i className="feather icon-play-circle me-2 text-success"></i>
                      Lezioni del corso
                    </h6>
                    
                    {/* Loading state */}
                    {loadingLessons[course.id] ? (
                      <div className="text-center py-4">
                        <div className="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
                        <span className="text-muted">Caricamento lezioni...</span>
                      </div>
                    ) : courseLessons[course.id] && courseLessons[course.id].length > 0 ? (
                      <div className="lessons-list">
                        {courseLessons[course.id].map((lesson, index) => (
                          <div key={lesson.id} className="lesson-item mb-3">
                            <div className="d-flex align-items-center justify-content-between p-3 bg-white rounded border">
                              <div className="d-flex align-items-center">
                                <Button
                                  variant="link"
                                  size="sm"
                                  onClick={() => handleExpandLesson(lesson.id)}
                                  className="p-0 me-2 text-muted"
                                  title={`${expandedLessons[lesson.id] ? 'Nascondi' : 'Mostra'} esercizi (${lessonExercises[lesson.id]?.length || 0})`}
                                >
                                  <i className={`feather ${expandedLessons[lesson.id] ? 'icon-chevron-down' : 'icon-chevron-right'}`}></i>
                                </Button>
                                <div className="lesson-number me-3">
                                  <span className="badge bg-success rounded-circle">{index + 1}</span>
                                </div>
                                <div>
                                  <div className="d-flex align-items-center mb-1">
                                    <Badge bg="success" className="me-2 lesson-badge">
                                      <i className="feather icon-play me-1"></i>
                                      Lezione
                                    </Badge>
                                    <h6 className="mb-0">{lesson.title}</h6>
                                  </div>
                                  <p className="text-muted small mb-0">
                                    {lesson.description || 'Nessuna descrizione'}
                                  </p>
                                </div>
                              </div>
                              <div className="lesson-actions">
                                <Button 
                                  variant="outline-primary" 
                                  size="sm"
                                  onClick={() => onViewLesson && onViewLesson(lesson.id)}
                                  title="Visualizza lezione"
                                >
                                  <i className="feather icon-eye"></i>
                                </Button>
                              </div>
                            </div>

                            {/* Exercises - Expandable */}
                            <Collapse in={expandedLessons[lesson.id]}>
                              <div className="exercises-section mt-2 ms-4">
                                {loadingExercises[lesson.id] ? (
                                  <div className="text-center py-3">
                                    <div className="spinner-border spinner-border-sm text-primary" role="status">
                                      <span className="visually-hidden">Caricamento...</span>
                                    </div>
                                    <p className="text-muted small mt-2 mb-0">Caricamento esercizi...</p>
                                  </div>
                                ) : lessonExercises[lesson.id] && lessonExercises[lesson.id].length > 0 ? (
                                  <div className="exercises-list">
                                    {lessonExercises[lesson.id].map((exercise, exerciseIndex) => (
                                      <div key={exercise.id} className="exercise-item mb-2 p-3 bg-light rounded border-start border-warning border-3">
                                        <div className="d-flex align-items-center justify-content-between">
                                          <div className="d-flex align-items-center">
                                            <div className="exercise-number me-3">
                                              <span className="badge bg-warning text-dark rounded-circle">{exerciseIndex + 1}</span>
                                            </div>
                                            <div>
                                              <div className="d-flex align-items-center mb-1">
                                                <Badge bg="warning" text="dark" className="me-2 exercise-badge">
                                                  <i className="feather icon-check-square me-1"></i>
                                                  Esercizio
                                                </Badge>
                                                <h6 className="mb-0">{exercise.title}</h6>
                                              </div>
                                              <p className="text-muted small mb-0">
                                                {exercise.description || 'Nessuna descrizione'}
                                              </p>
                                            </div>
                                          </div>
                                          <div className="exercise-actions">
                                            <Button 
                                              variant="outline-primary" 
                                              size="sm"
                                              onClick={() => onViewExercise && onViewExercise(exercise.id)}
                                            >
                                              <i className="feather icon-eye"></i>
                                            </Button>
                                          </div>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <div className="text-center py-3">
                                    <i className="feather icon-check-square text-muted me-2"></i>
                                    <span className="text-muted">Nessun esercizio per questa lezione</span>
                                    {onCreateExercise && (
                                      <Button 
                                        variant="outline-warning" 
                                        size="sm" 
                                        className="ms-2"
                                        onClick={() => onCreateExercise(lesson.id)}
                                      >
                                        <i className="feather icon-plus me-1"></i>
                                        Aggiungi Esercizio
                                      </Button>
                                    )}
                                  </div>
                                )}
                              </div>
                            </Collapse>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-4 bg-white rounded border">
                        <i className="feather icon-play-circle text-muted" style={{ fontSize: '2rem' }}></i>
                        <p className="text-muted mt-2 mb-3">Nessuna lezione creata per questo corso</p>
                        {onCreateLesson && (
                          <Button
                            variant="success"
                            size="sm"
                            onClick={() => onCreateLesson(course.id)}
                          >
                            <i className="feather icon-plus me-1"></i>
                            Crea Prima Lezione
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Collapse>
          </Card.Body>
        </Card>
      ))}
    </div>
  );
};

export default CoursesTable;

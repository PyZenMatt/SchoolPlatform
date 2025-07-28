import React, { useState } from 'react';
import { Card, Badge, Button, Row, Col, Collapse, ProgressBar } from 'react-bootstrap';
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

  const getCategoryColor = (category) => {
    const categoryColors = {
      'Programmazione': '#007bff',
      'Design': '#28a745',
      'Marketing': '#dc3545',
      'Business': '#ffc107',
      'Lingue': '#17a2b8',
      'Arte': '#6f42c1',
      'Musica': '#fd7e14',
      'Salute': '#20c997',
      'Sport': '#e83e8c',
      'Cucina': '#6c757d'
    };
    return categoryColors[category] || '#6c757d';
  };

  const getCompletionPercentage = (course) => {
    if (!course.lessons || course.lessons.length === 0) return 0;
    const totalLessons = course.lessons.length;
    const completedLessons = course.lessons.filter(lesson => 
      lesson.exercises && lesson.exercises.length > 0
    ).length;
    return Math.round((completedLessons / totalLessons) * 100);
  };

  if (!courses || courses.length === 0) {
    return (
      <div className="courses-grid-modern">
        <div className="empty-state text-center py-5">
          <div className="mb-4">
            <i className="feather icon-book-open" style={{ fontSize: '4rem', color: '#6c757d' }}></i>
          </div>
          <h4 className="mb-3 text-muted">Nessun corso trovato</h4>
          <p className="text-muted mb-4">Inizia creando il tuo primo corso per condividere le tue conoscenze!</p>
          {showCreateCourse && (
            <Button 
              variant="primary" 
              size="lg"
              className="px-4 py-2"
              onClick={onCreateCourse}
              style={{
                background: 'linear-gradient(135deg, #04a9f5, #1de9b6)',
                border: 'none',
                borderRadius: '25px',
                boxShadow: '0 4px 15px rgba(4, 169, 245, 0.3)'
              }}
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
    <div className="courses-grid-modern">
      {showCreateCourse && (
        <Card className="create-course-card mb-4 border-0 shadow-sm">
          <Card.Body className="text-center py-5" 
            style={{
              background: 'linear-gradient(135deg, rgba(4, 169, 245, 0.05) 0%, rgba(29, 233, 182, 0.05) 100%)',
              borderRadius: '15px'
            }}
          >
            <div className="mb-4">
              <i className="feather icon-plus-circle" style={{ 
                fontSize: '3rem', 
                color: '#04a9f5',
                filter: 'drop-shadow(0 4px 8px rgba(4, 169, 245, 0.3))'
              }}></i>
            </div>
            <h5 className="mb-3 fw-bold">Crea Nuovo Corso</h5>
            <p className="text-muted mb-4">Condividi le tue conoscenze creando un corso professionale</p>
            <Button 
              variant="success" 
              size="lg"
              className="px-4 py-2"
              onClick={onCreateCourse}
              style={{
                background: 'linear-gradient(135deg, #28a745, #20c997)',
                border: 'none',
                borderRadius: '25px',
                boxShadow: '0 4px 15px rgba(40, 167, 69, 0.3)'
              }}
            >
              <i className="feather icon-plus me-2"></i>
              Crea Corso
            </Button>
          </Card.Body>
        </Card>
      )}

      <div className="courses-grid-modern">
        <div className="container-fluid px-0">
          {courses.map(course => {
        const completionRate = getCompletionPercentage(course);
        const isExpanded = expandedCourse === course.id;
          
          return (
            <div key={course.id} className="course-item mb-4 mx-auto" style={{ maxWidth: '800px' }}>
              <Card className="course-card h-100 border-0 shadow-sm position-relative">
                {/* Course Image/Header - Make clickable */}
                <div 
                  className="course-image-container position-relative cursor-pointer"
                  onClick={() => onExpandCourse && onExpandCourse(
                    isExpanded ? null : course.id
                  )}
                  style={{ cursor: 'pointer' }}
                >
                  {course.image ? (
                    <img 
                      src={course.image} 
                      alt={course.title}
                      className="course-image"
                      style={{ transition: 'transform 0.3s ease' }}
                    />
                  ) : (
                    <div className="course-placeholder" style={{
                      background: `linear-gradient(135deg, ${getCategoryColor(course.category)} 0%, ${getCategoryColor(course.category)}99 100%)`,
                      transition: 'transform 0.3s ease'
                    }}>
                      <i className="feather icon-book-open"></i>
                    </div>
                  )}
                  
                  {/* Hover overlay for better UX */}
                  <div 
                    className="course-hover-overlay position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
                    style={{
                      background: 'rgba(0, 0, 0, 0.3)',
                      opacity: 0,
                      transition: 'opacity 0.3s ease',
                      borderRadius: '15px 15px 0 0'
                    }}
                  >
                    <div className="text-center text-white">
                      <i className={`feather icon-${isExpanded ? 'eye-off' : 'eye'} fs-1 mb-2`}></i>
                      <div className="fw-bold">
                        {isExpanded ? 'Nascondi Dettagli' : 'Mostra Dettagli'}
                      </div>
                    </div>
                  </div>
                  
                  <div className="position-absolute top-0 start-0 m-3">
                    <Badge 
                      className="category-badge px-3 py-2"
                      style={{
                        background: `${getCategoryColor(course.category)}dd`,
                        color: 'white',
                        borderRadius: '15px'
                      }}
                    >
                      {course.category || 'Generale'}
                    </Badge>
                  </div>
                  
                  <div className="position-absolute top-0 end-0 m-3">
                    <Button
                      className="expand-btn"
                      size="sm"
                      variant={isExpanded ? 'success' : 'primary'}
                      style={{
                        borderRadius: '50%',
                        width: '40px',
                        height: '40px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        onExpandCourse && onExpandCourse(
                          isExpanded ? null : course.id
                        );
                      }}
                    >
                      <i className={`feather icon-chevron-${isExpanded ? 'up' : 'down'}`}></i>
                    </Button>
                  </div>
                </div>
                
                <Card.Body 
                  className="course-header cursor-pointer"
                  onClick={() => onExpandCourse && onExpandCourse(
                    isExpanded ? null : course.id
                  )}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="d-flex justify-content-between align-items-start mb-3">
                    <div className="flex-grow-1">
                      <h6 className="course-title mb-2 text-primary fw-bold" style={{ fontSize: '1.1rem' }}>
                        {course.title}
                        <i className="feather icon-external-link ms-2 text-muted" style={{ fontSize: '0.8rem' }}></i>
                      </h6>
                      <div className="d-flex align-items-center gap-2 mb-2">
                        <Badge 
                          variant={getBadgeVariant(course.status)} 
                          className="course-type-badge"
                          style={{ borderRadius: '10px' }}
                        >
                          {course.status || 'Draft'}
                        </Badge>
                        <small className="text-muted">
                          <i className="feather icon-clock me-1"></i>
                          {(courseLessons[course.id] && courseLessons[course.id].length) || course.lessons?.length || 0} lezioni
                        </small>
                        {isExpanded && (
                          <Badge bg="info" className="expanded-indicator">
                            <i className="feather icon-eye me-1"></i>
                            Espanso
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="text-end">
                      <div className="price-tag text-primary fw-bold" style={{ fontSize: '1.2rem' }}>
                        {formatPrice(course.price)} TEO
                      </div>
                      <small className="text-muted">Prezzo corso</small>
                    </div>
                  </div>
                  
                  {course.description && (
                    <p className="course-description mb-3 text-muted" style={{
                      display: '-webkit-box',
                      WebkitLineClamp: isExpanded ? 'none' : 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: isExpanded ? 'visible' : 'hidden',
                      transition: 'all 0.3s ease'
                    }}>
                      {course.description}
                    </p>
                  )}
                  
                  {/* Course Progress */}
                  <div className="mb-3">
                    <div className="d-flex justify-content-between align-items-center mb-1">
                      <small className="text-muted fw-semibold">Completamento Corso</small>
                      <small className="text-primary fw-bold">{completionRate}%</small>
                    </div>
                    <ProgressBar 
                      now={completionRate} 
                      style={{ height: '8px', borderRadius: '4px' }}
                      variant={completionRate > 70 ? 'success' : completionRate > 40 ? 'warning' : 'danger'}
                    />
                  </div>
                  
                  <div className="course-stats mb-3">
                    <Row className="text-center g-2">
                      <Col>
                        <div className="stat-item p-2 bg-light rounded">
                          <div className="stat-value text-primary fw-bold">
                            {(courseLessons[course.id] && courseLessons[course.id].length) || course.lessons?.length || 0}
                          </div>
                          <small className="stat-label text-muted d-block">Lezioni</small>
                        </div>
                      </Col>
                      <Col>
                        <div className="stat-item p-2 bg-light rounded">
                          <div className="stat-value text-warning fw-bold">
                            {course.total_exercises || 0}
                          </div>
                          <small className="stat-label text-muted d-block">Esercizi</small>
                        </div>
                      </Col>
                      <Col>
                        <div className="stat-item p-2 bg-light rounded">
                          <div className="stat-value text-success fw-bold">
                            {course.students_count || 0}
                          </div>
                          <small className="stat-label text-muted d-block">Studenti</small>
                        </div>
                      </Col>
                    </Row>
                  </div>

                  {/* Quick Actions */}
                  <div 
                    className="course-actions d-flex gap-2"
                    onClick={(e) => e.stopPropagation()} // Prevent card click when clicking buttons
                  >
                    <Button
                      variant={isExpanded ? "primary" : "outline-primary"}
                      size="sm"
                      className="flex-fill"
                      onClick={(e) => {
                        e.stopPropagation();
                        onViewCourse && onViewCourse(course.id);
                      }}
                      style={{ borderRadius: '12px' }}
                    >
                      <i className="feather icon-eye me-1"></i>
                      {isExpanded ? 'Vai al Corso' : 'Dettagli'}
                    </Button>
                    <Button
                      variant="outline-secondary"
                      size="sm"
                      className="flex-fill"
                      onClick={(e) => {
                        e.stopPropagation();
                        onEditCourse && onEditCourse(course.id);
                      }}
                      style={{ borderRadius: '12px' }}
                    >
                      <i className="feather icon-edit me-1"></i>
                      Modifica
                    </Button>
                    {onCreateLesson && (
                      <Button
                        variant="success"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          onCreateLesson(course.id);
                        }}
                        style={{ 
                          borderRadius: '12px',
                          minWidth: '45px'
                        }}
                        title="Aggiungi Lezione"
                      >
                        <i className="feather icon-plus"></i>
                      </Button>
                    )}
                  </div>
                </Card.Body>

                {/* Expanded Content - Lessons */}
                <Collapse in={isExpanded}>
                  <div className="course-expanded-content">
                    <div className="p-3">
                      <div className="d-flex justify-content-between align-items-center mb-3">
                        <h6 className="mb-0 fw-bold text-dark">
                          <i className="feather icon-list me-2 text-primary"></i>
                          Lezioni del Corso
                        </h6>
                        {onCreateLesson && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => onCreateLesson(course.id)}
                            style={{
                              background: 'linear-gradient(135deg, #04a9f5, #1de9b6)',
                              border: 'none',
                              borderRadius: '15px'
                            }}
                          >
                            <i className="feather icon-plus me-1"></i>
                            Nuova Lezione
                          </Button>
                        )}
                      </div>
                      
                      {loadingLessons && loadingLessons[course.id] ? (
                        <div className="text-center py-4">
                          <div className="spinner-border text-primary" role="status">
                            <span className="visually-hidden">Caricamento lezioni...</span>
                          </div>
                          <p className="text-muted mt-2 mb-0">Caricamento lezioni...</p>
                        </div>
                      ) : courseLessons[course.id] && courseLessons[course.id].length > 0 ? (
                        <div className="lessons-grid">
                          {courseLessons[course.id].map((lesson, lessonIndex) => (
                            <Card key={lesson.id} className="lesson-card mb-3 border-0 shadow-sm">
                              <Card.Body className="p-3">
                                <div 
                                  className="lesson-header cursor-pointer"
                                  onClick={() => handleToggleLesson(lesson.id)}
                                >
                                  <div className="d-flex justify-content-between align-items-center">
                                    <div className="flex-grow-1">
                                      <div className="d-flex align-items-center mb-2">
                                        <Badge 
                                          className="me-2 px-2 py-1"
                                          style={{
                                            background: 'linear-gradient(135deg, #28a745, #20c997)',
                                            borderRadius: '10px'
                                          }}
                                        >
                                          #{lessonIndex + 1}
                                        </Badge>
                                        <h6 className="lesson-title mb-0">{lesson.title}</h6>
                                      </div>
                                      <div className="lesson-stats d-flex gap-3">
                                        <small className="text-muted">
                                          <i className="feather icon-clock me-1"></i>
                                          {lesson.duration || '30'} min
                                        </small>
                                        <small className="text-muted">
                                          <i className="feather icon-target me-1"></i>
                                          {lesson.exercises?.length || 0} esercizi
                                        </small>
                                        <Badge 
                                          variant={lesson.lesson_type === 'video' ? 'warning' : 'info'}
                                          className="px-2 py-1"
                                          style={{ fontSize: '0.7rem', borderRadius: '8px' }}
                                        >
                                          {lesson.lesson_type || 'theory'}
                                        </Badge>
                                      </div>
                                    </div>
                                    <div className="lesson-actions d-flex align-items-center gap-2">
                                      {showActions && (
                                        <>
                                          <Button
                                            variant="outline-primary"
                                            size="sm"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              onViewLesson && onViewLesson(lesson);
                                            }}
                                          >
                                            <i className="feather icon-eye"></i>
                                          </Button>
                                          <Button
                                            variant="outline-secondary"
                                            size="sm"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              onEditLesson && onEditLesson(lesson);
                                            }}
                                          >
                                            <i className="feather icon-edit"></i>
                                          </Button>
                                        </>
                                      )}
                                      <i className={`feather icon-chevron-${expandedLessons[lesson.id] ? 'up' : 'down'} text-muted`}></i>
                                    </div>
                                  </div>
                                </div>
                                
                                <Collapse in={expandedLessons[lesson.id]}>
                                  <div className="exercises-section mt-3 p-3 rounded" style={{
                                    background: 'linear-gradient(135deg, rgba(255, 193, 7, 0.1) 0%, rgba(255, 193, 7, 0.05) 100%)',
                                    border: '2px solid rgba(255, 193, 7, 0.2)'
                                  }}>
                                    <div className="d-flex justify-content-between align-items-center mb-3">
                                      <h6 className="mb-0 fw-bold text-dark">
                                        <i className="feather icon-target me-2 text-warning"></i>
                                        Esercizi della Lezione
                                      </h6>
                                      {onCreateExercise && (
                                        <Button
                                          variant="warning"
                                          size="sm"
                                          onClick={() => onCreateExercise({
                                            ...lesson,
                                            course_id: course.id,
                                            course: course.id
                                          })}
                                          style={{ borderRadius: '15px' }}
                                        >
                                          <i className="feather icon-plus me-1"></i>
                                          {lesson.exercises?.length === 0 ? 'Primo Esercizio' : 'Aggiungi'}
                                        </Button>
                                      )}
                                    </div>
                                    
                                    {lesson.exercises && lesson.exercises.length > 0 ? (
                                      <div className="exercises-list">
                                        {lesson.exercises.map((exercise, exerciseIndex) => (
                                          <div 
                                            key={exercise.id} 
                                            className="exercise-item d-flex justify-content-between align-items-center p-2 mb-2 rounded"
                                            style={{ background: 'rgba(255, 255, 255, 0.7)' }}
                                          >
                                            <div className="flex-grow-1">
                                              <div className="d-flex align-items-center mb-1">
                                                <Badge 
                                                  className="me-2 px-2 py-1"
                                                  style={{
                                                    background: 'linear-gradient(135deg, #ffc107, #fd7e14)',
                                                    color: '#000',
                                                    borderRadius: '8px'
                                                  }}
                                                >
                                                  Ex.{exerciseIndex + 1}
                                                </Badge>
                                                <h6 className="mb-0" style={{ fontSize: '0.9rem' }}>
                                                  {exercise.title}
                                                </h6>
                                              </div>
                                              <div className="d-flex gap-2">
                                                <Badge 
                                                  variant="secondary" 
                                                  style={{ fontSize: '0.7rem', borderRadius: '8px' }}
                                                >
                                                  {exercise.exercise_type || 'practical'}
                                                </Badge>
                                                <Badge 
                                                  variant="info" 
                                                  style={{ fontSize: '0.7rem', borderRadius: '8px' }}
                                                >
                                                  {exercise.difficulty || 'beginner'}
                                                </Badge>
                                              </div>
                                            </div>
                                            {showActions && (
                                              <div className="d-flex gap-1">
                                                <Button
                                                  variant="outline-primary"
                                                  size="sm"
                                                  onClick={() => onViewExercise && onViewExercise(exercise.id)}
                                                >
                                                  <i className="feather icon-eye"></i>
                                                </Button>
                                                <Button
                                                  variant="outline-secondary"
                                                  size="sm"
                                                  onClick={() => onEditExercise && onEditExercise(exercise.id)}
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
                                        <i className="feather icon-target text-muted mb-2" style={{ fontSize: '2rem' }}></i>
                                        <p className="text-muted mb-3">Nessun esercizio creato</p>
                                        {onCreateExercise && (
                                          <Button
                                            variant="warning"
                                            size="sm"
                                            onClick={() => onCreateExercise({
                                              ...lesson,
                                              course_id: course.id,
                                              course: course.id
                                            })}
                                            style={{ borderRadius: '15px' }}
                                          >
                                            <i className="feather icon-plus me-1"></i>
                                            Crea Primo Esercizio
                                          </Button>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                </Collapse>
                              </Card.Body>
                            </Card>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-4">
                          <i className="feather icon-book text-muted mb-3" style={{ fontSize: '2.5rem' }}></i>
                          <p className="text-muted mb-3">Nessuna lezione creata per questo corso</p>
                          {onCreateLesson && (
                            <Button
                              variant="primary"
                              onClick={() => onCreateLesson(course.id)}
                              style={{
                                background: 'linear-gradient(135deg, #04a9f5, #1de9b6)',
                                border: 'none',
                                borderRadius: '15px'
                              }}
                            >
                              <i className="feather icon-plus me-2"></i>
                              Crea Prima Lezione
                            </Button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </Collapse>
              </Card>
            </div>
          );
        })}
        </div>
      </div>
    </div>
  );
};

export default CoursesTable;

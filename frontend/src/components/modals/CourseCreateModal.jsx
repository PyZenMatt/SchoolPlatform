import React, { useState, useRef, useEffect } from 'react';
import { Modal, Button, Form, Alert, Spinner, Card, Row, Col, Badge } from 'react-bootstrap';
import { createCourse } from '../../services/api/courses';
import CustomToast from '../ui/Toast';
import '../../../assets/css/components/CourseCreateModal.css';

import ErrorDisplay from '../ui/ErrorDisplay';
import { validateCourseForm, debounce } from '../../utils/formValidation';

const CourseCreateModal = ({ show, onHide, onCreated }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [category, setCategory] = useState('');
  const [coverImage, setCoverImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [validationErrors, setValidationErrors] = useState({});
  const [showToast, setShowToast] = useState(false);
  const [toastConfig, setToastConfig] = useState({ variant: 'success', title: '', message: '' });
  const fileInputRef = useRef(null);

  // Real-time validation with debouncing
  const validateForm = debounce(() => {
    const formData = { title, description, price, category };
    const validation = validateCourseForm(formData);
    setValidationErrors(validation.errors);
  }, 300);

  // Trigger validation when form data changes
  useEffect(() => {
    validateForm();
  }, [title, description, price, category]);

  // Clear validation errors when modal opens
  useEffect(() => {
    if (show) {
      setValidationErrors({});
    }
  }, [show]);

  // Categorie artistiche con icone
  const categories = [
    { value: 'disegno', label: '✏️ Disegno', color: 'primary' },
    { value: 'pittura-olio', label: '🎨 Pittura ad Olio', color: 'warning' },
    { value: 'acquerello', label: '💧 Acquerello', color: 'info' },
    { value: 'tempera', label: '🖌️ Tempera', color: 'success' },
    { value: 'acrilico', label: '🌈 Pittura Acrilica', color: 'danger' },
    { value: 'scultura', label: '🗿 Scultura', color: 'dark' },
    { value: 'storia-arte', label: '📚 Storia dell\'Arte', color: 'secondary' },
    { value: 'fotografia', label: '📸 Fotografia Artistica', color: 'primary' },
    { value: 'illustrazione', label: '🖊️ Illustrazione', color: 'info' },
    { value: 'arte-digitale', label: '💻 Arte Digitale', color: 'success' },
    { value: 'ceramica', label: '🏺 Ceramica e Terracotta', color: 'warning' },
    { value: 'incisione', label: '⚱️ Incisione e Stampa', color: 'dark' },
    { value: 'mosaico', label: '🔷 Mosaico', color: 'primary' },
    { value: 'restauro', label: '🛠️ Restauro Artistico', color: 'secondary' },
    { value: 'calligrafia', label: '✒️ Calligrafia', color: 'dark' },
    { value: 'fumetto', label: '💭 Fumetto e Graphic Novel', color: 'info' },
    { value: 'design-grafico', label: '🎨 Design Grafico', color: 'danger' },
    { value: 'arte-contemporanea', label: '🆕 Arte Contemporanea', color: 'success' },
    { value: 'arte-classica', label: '🏛️ Arte Classica', color: 'warning' },
    { value: 'other', label: '🎭 Altro', color: 'secondary' }
  ];

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      processImageFile(file);
    }
  };

  const processImageFile = (file) => {
    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Per favore seleziona un file immagine valido');
      return;
    }
    
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('L\'immagine deve essere inferiore a 5MB');
      return;
    }
    
    setCoverImage(file);
    const reader = new FileReader();
    reader.onload = (e) => setImagePreview(e.target.result);
    reader.readAsDataURL(file);
    setError(''); // Clear any previous errors
  };

  // Drag and drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      processImageFile(files[0]);
    }
  };

  const removeImage = () => {
    setCoverImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const resetForm = () => {
    setTitle('');
    setDescription('');
    setPrice('');
    setCategory('');
    setCoverImage(null);
    setImagePreview(null);
    setError('');
    setValidationErrors({});
    setShowToast(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('description', description);
      formData.append('price', price);
      formData.append('category', category);
      if (coverImage) {
        formData.append('cover_image', coverImage);
      }

      await createCourse(formData);
      
      // Show success notification
      setToastConfig({
        variant: 'success',
        title: 'Successo!',
        message: `Il corso "${title}" è stato creato con successo! 🎉`
      });
      setShowToast(true);
      
      resetForm();
      if (onCreated) onCreated();
      
      // Close modal immediately after success
      onHide();
    } catch (err) {
      console.error('Errore creazione corso:', err);
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.message || 
                          'Errore nella creazione del corso. Verifica tutti i campi.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    resetForm();
    onHide();
  };

  return (
    <>
      <Modal show={show} onHide={handleClose} size="lg">
        <Modal.Header closeButton className="border-0 pb-0">
          <Modal.Title className="d-flex align-items-center">
            <span className="me-2">🎨</span>
            Crea un Nuovo Corso Artistico
          </Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleSubmit}>
          <Modal.Body className="pt-2">
            <ErrorDisplay errors={validationErrors} />

            {error && (
              <Alert variant="danger" className="d-flex align-items-center">
                <i className="bi bi-exclamation-triangle-fill me-2"></i>
                {error}
              </Alert>
            )}

          <Card className="border-0 shadow-sm mb-4">
            <Card.Body>
              <h6 className="text-muted mb-3">📝 Informazioni Base</h6>
              
              <Form.Group className="mb-3">
                <Form.Label className="fw-semibold">
                  <i className="bi bi-pencil me-2"></i>Titolo del Corso
                </Form.Label>
                <Form.Control 
                  value={title} 
                  onChange={e => setTitle(e.target.value)} 
                  placeholder="es. Corso di Pittura ad Olio per Principianti"
                  className="form-control-lg"
                  isInvalid={!!validationErrors.title}
                  required 
                />
                <Form.Control.Feedback type="invalid">
                  {validationErrors.title}
                </Form.Control.Feedback>
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label className="fw-semibold">
                  <i className="bi bi-text-paragraph me-2"></i>Descrizione
                </Form.Label>
                <Form.Control 
                  as="textarea" 
                  rows={4}
                  value={description} 
                  onChange={e => setDescription(e.target.value)} 
                  placeholder="Descrivi il contenuto del corso, gli obiettivi di apprendimento e a chi è rivolto..."
                  isInvalid={!!validationErrors.description}
                  required 
                />
                <Form.Control.Feedback type="invalid">
                  {validationErrors.description}
                </Form.Control.Feedback>
              </Form.Group>

              <Row>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label className="fw-semibold">
                      <i className="bi bi-coin me-2"></i>Prezzo (TeoCoin)
                    </Form.Label>
                    <Form.Control 
                      type="number" 
                      min={0} 
                      value={price} 
                      onChange={e => setPrice(e.target.value)} 
                      placeholder="0"
                      className="form-control-lg"
                      isInvalid={!!validationErrors.price}
                      required 
                    />
                    <Form.Control.Feedback type="invalid">
                      {validationErrors.price}
                    </Form.Control.Feedback>
                  </Form.Group>
                </Col>
              </Row>
            </Card.Body>
          </Card>

          <Card className="border-0 shadow-sm mb-4">
            <Card.Body>
              <h6 className="text-muted mb-3">🎯 Categoria Artistica</h6>
              {validationErrors.category && (
                <div className="text-danger small mb-2">
                  <i className="bi bi-exclamation-triangle me-1"></i>
                  {validationErrors.category}
                </div>
              )}
              <Row>
                {categories.map((cat) => (
                  <Col sm={6} md={4} key={cat.value} className="mb-2">
                    <div 
                      className={`category-option cursor-pointer ${category === cat.value ? 'selected' : ''}`}
                      onClick={() => setCategory(cat.value)}
                    >
                      <Badge 
                        bg={category === cat.value ? cat.color : 'light'} 
                        text={category === cat.value ? 'white' : 'dark'}
                        className={`w-100 p-2 category-badge`}
                      >
                        {cat.label}
                      </Badge>
                    </div>
                  </Col>
                ))}
              </Row>
            </Card.Body>
          </Card>

          <Card className="border-0 shadow-sm">
            <Card.Body>
              <h6 className="text-muted mb-3">🖼️ Immagine di Copertina</h6>
              
              {!imagePreview ? (
                <div 
                  className="image-upload-area"
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={handleDragOver}
                  onDragEnter={handleDragEnter}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <div className="upload-content">
                    <i className="bi bi-cloud-upload fs-1 text-primary mb-3"></i>
                    <h5>Carica un'immagine</h5>
                    <p className="text-muted">
                      Clicca qui o <strong>trascina un'immagine</strong> per selezionare una copertina
                    </p>
                    <small className="text-muted d-block mb-2">
                      Formati supportati: JPG, PNG, GIF (max 5MB)
                    </small>
                    <Button variant="outline-primary">
                      <i className="bi bi-image me-2"></i>Seleziona Immagine
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="image-preview">
                  <img src={imagePreview} alt="Preview" className="preview-image" />
                  <div className="image-overlay">
                    <Button 
                      variant="danger" 
                      size="sm" 
                      onClick={removeImage}
                      className="remove-image-btn"
                    >
                      <i className="bi bi-trash"></i>
                    </Button>
                  </div>
                </div>
              )}
              
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageChange}
                style={{ display: 'none' }}
              />
            </Card.Body>
          </Card>
        </Modal.Body>
        
        <Modal.Footer className="border-0 pt-0">
          <Button variant="outline-secondary" onClick={handleClose}>
            <i className="bi bi-x-circle me-2"></i>Annulla
          </Button>
          <Button 
            type="submit" 
            variant="primary" 
            disabled={loading || Object.keys(validationErrors).length > 0 || !title || !description || !price || !category}
            className="px-4"
          >
            {loading ? (
              <>
                <Spinner size="sm" animation="border" className="me-2" />
                Creazione in corso...
              </>
            ) : (
              <>
                <i className="bi bi-plus-circle me-2"></i>Crea Corso
              </>
            )}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
    
    <CustomToast
      show={showToast}
      onClose={() => setShowToast(false)}
      variant={toastConfig.variant}
      title={toastConfig.title}
      message={toastConfig.message}
    />
    </>
  );
};

export default CourseCreateModal;

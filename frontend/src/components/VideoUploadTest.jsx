import React, { useState } from 'react';
import { Button, Alert, Card, Form } from 'react-bootstrap';
import { createLesson } from '../services/api/courses';

const VideoUploadTest = () => {
  const [videoFile, setVideoFile] = useState(null);
  const [videoPreview, setVideoPreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleVideoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('video/')) {
        setError('Per favore seleziona un file video valido');
        return;
      }
      
      if (file.size > 50 * 1024 * 1024) {
        setError('Il video deve essere inferiore a 50MB');
        return;
      }
      
      setVideoFile(file);
      const url = URL.createObjectURL(file);
      setVideoPreview(url);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!videoFile) {
      setError('Seleziona prima un video');
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('title', 'Test Video Lesson');
      formData.append('content', 'Questa è una lezione di test per il video upload');
      formData.append('duration', '10');
      formData.append('lesson_type', 'video');
      formData.append('course_id', '1'); // Usa un course ID esistente
      formData.append('video_file', videoFile);

      console.log('📤 Invio FormData:', {
        title: formData.get('title'),
        content: formData.get('content'),
        duration: formData.get('duration'),
        lesson_type: formData.get('lesson_type'),
        course_id: formData.get('course_id'),
        video_file: formData.get('video_file')?.name
      });

      const response = await createLesson(formData);
      console.log('✅ Risposta API:', response.data);
      
      setResult({
        success: true,
        data: response.data,
        message: 'Video caricato con successo!'
      });
    } catch (err) {
      console.error('❌ Errore upload:', err);
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.message || 
                          err.response?.data?.error ||
                          err.message ||
                          'Errore sconosciuto durante l\'upload';
      setError(errorMessage);
      setResult({
        success: false,
        error: err.response?.data || err.message,
        message: errorMessage
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card className="m-3">
      <Card.Header>
        <h5>🎥 Test Upload Video Lezioni</h5>
      </Card.Header>
      <Card.Body>
        <Form.Group className="mb-3">
          <Form.Label>Seleziona Video</Form.Label>
          <Form.Control
            type="file"
            accept="video/*"
            onChange={handleVideoChange}
          />
          <Form.Text className="text-muted">
            Formati supportati: MP4, AVI, MOV (max 50MB)
          </Form.Text>
        </Form.Group>

        {videoPreview && (
          <div className="mb-3">
            <h6>Preview:</h6>
            <video 
              src={videoPreview} 
              controls 
              style={{ width: '100%', maxWidth: '400px', height: '200px' }}
            >
              Il tuo browser non supporta il tag video.
            </video>
            <div className="mt-2">
              <small className="text-muted">
                File: {videoFile.name} ({(videoFile.size / 1024 / 1024).toFixed(2)} MB)
              </small>
            </div>
          </div>
        )}

        <Button 
          onClick={handleUpload} 
          disabled={!videoFile || uploading}
          variant="primary"
        >
          {uploading ? '⏳ Caricamento...' : '📤 Carica Video'}
        </Button>

        {error && (
          <Alert variant="danger" className="mt-3">
            <strong>❌ Errore:</strong> {error}
          </Alert>
        )}

        {result && (
          <Alert variant={result.success ? 'success' : 'danger'} className="mt-3">
            <strong>{result.success ? '✅ Successo:' : '❌ Errore:'}</strong> {result.message}
            {result.success && result.data && (
              <div className="mt-2">
                <small>
                  <strong>Lezione ID:</strong> {result.data.id}<br/>
                  <strong>Titolo:</strong> {result.data.title}<br/>
                  <strong>Video URL:</strong> {result.data.video_file_url || result.data.video_file}
                </small>
              </div>
            )}
            {!result.success && result.error && (
              <div className="mt-2">
                <small>
                  <strong>Dettagli errore:</strong> 
                  <pre>{JSON.stringify(result.error, null, 2)}</pre>
                </small>
              </div>
            )}
          </Alert>
        )}
      </Card.Body>
    </Card>
  );
};

export default VideoUploadTest;

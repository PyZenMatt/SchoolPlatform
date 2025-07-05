import React, { useState } from 'react';
import { Card, Button, Badge, Modal, Spinner, Alert } from 'react-bootstrap';
import { formatEscrowStatus, getTimeRemaining, formatTeoCoinAmount } from '../../services/api/escrow';
import './TeacherEscrowCard.css';

/**
 * TeacherEscrowCard Component
 * Displays individual escrow with accept/reject actions
 */
const TeacherEscrowCard = ({ escrow, onEscrowAction }) => {
  const [showDetails, setShowDetails] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [error, setError] = useState('');

  // Format status for display
  const statusInfo = formatEscrowStatus(escrow.status);
  
  // Calculate time remaining
  const timeInfo = getTimeRemaining(escrow.expires_at);

  // Handle escrow action (accept/reject)
  const handleAction = async (action) => {
    setActionLoading(action);
    setError('');
    
    try {
      await onEscrowAction(escrow.id, action);
      setShowDetails(false);
    } catch (err) {
      setError(err.response?.data?.error || `Errore durante ${action === 'accept' ? 'accettazione' : 'rifiuto'}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Format EUR amounts
  const formatEUR = (amount) => `€${parseFloat(amount).toFixed(2)}`;

  return (
    <>
      <Card className={`teacher-escrow-card ${timeInfo.expired ? 'expired' : ''}`}>
        <Card.Body>
          <div className="d-flex justify-content-between align-items-start mb-3">
            <div>
              <h6 className="card-title mb-1">
                {escrow.course_title}
              </h6>
              <p className="text-muted small mb-2">
                Studente: {escrow.student_name}
              </p>
            </div>
            <div className="text-end">
              <Badge variant={statusInfo.variant} className="mb-2">
                <i className={`feather icon-${statusInfo.icon} me-1`}></i>
                {statusInfo.text}
              </Badge>
              <div className={`time-remaining ${timeInfo.expired ? 'text-danger' : 'text-warning'}`}>
                <i className="feather icon-clock me-1"></i>
                <small>{timeInfo.text}</small>
              </div>
            </div>
          </div>

          {/* Amount Display */}
          <div className="escrow-amounts mb-3">
            <div className="row">
              <div className="col-6">
                <div className="amount-box teocoin-amount">
                  <label className="small text-muted">TeoCoin in Escrow</label>
                  <div className="amount-value">
                    {formatTeoCoinAmount(escrow.teocoin_amount)}
                  </div>
                </div>
              </div>
              <div className="col-6">
                <div className="amount-box eur-amount">
                  <label className="small text-muted">Prezzo Scontato</label>
                  <div className="amount-value">
                    {formatEUR(escrow.discounted_price)}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          {escrow.status === 'pending' && !timeInfo.expired && (
            <div className="escrow-actions">
              <div className="d-flex gap-2">
                <Button
                  variant="success"
                  size="sm"
                  onClick={() => handleAction('accept')}
                  disabled={actionLoading}
                  className="flex-fill"
                >
                  {actionLoading === 'accept' ? (
                    <Spinner animation="border" size="sm" />
                  ) : (
                    <>
                      <i className="feather icon-check me-1"></i>
                      Accetta
                    </>
                  )}
                </Button>
                <Button
                  variant="outline-danger"
                  size="sm"
                  onClick={() => handleAction('reject')}
                  disabled={actionLoading}
                  className="flex-fill"
                >
                  {actionLoading === 'reject' ? (
                    <Spinner animation="border" size="sm" />
                  ) : (
                    <>
                      <i className="feather icon-x me-1"></i>
                      Rifiuta
                    </>
                  )}
                </Button>
              </div>
              <Button
                variant="link"
                size="sm"
                onClick={() => setShowDetails(true)}
                className="w-100 mt-2 p-0"
              >
                <i className="feather icon-info me-1"></i>
                Dettagli
              </Button>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <Alert variant="danger" className="mt-3 mb-0 py-2">
              <small>{error}</small>
            </Alert>
          )}
        </Card.Body>
      </Card>

      {/* Details Modal */}
      <Modal show={showDetails} onHide={() => setShowDetails(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Dettagli Escrow - {escrow.course_title}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="row">
            <div className="col-md-6">
              <h6>Informazioni Corso</h6>
              <table className="table table-borderless table-sm">
                <tbody>
                  <tr>
                    <td><strong>Corso:</strong></td>
                    <td>{escrow.course_title}</td>
                  </tr>
                  <tr>
                    <td><strong>Prezzo Originale:</strong></td>
                    <td>{formatEUR(escrow.original_price)}</td>
                  </tr>
                  <tr>
                    <td><strong>Prezzo Scontato:</strong></td>
                    <td className="text-success">{formatEUR(escrow.discounted_price)}</td>
                  </tr>
                  <tr>
                    <td><strong>Sconto:</strong></td>
                    <td className="text-warning">
                      {formatEUR(escrow.original_price - escrow.discounted_price)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div className="col-md-6">
              <h6>Informazioni Studente</h6>
              <table className="table table-borderless table-sm">
                <tbody>
                  <tr>
                    <td><strong>Nome:</strong></td>
                    <td>{escrow.student_name}</td>
                  </tr>
                  <tr>
                    <td><strong>Email:</strong></td>
                    <td>{escrow.student_email}</td>
                  </tr>
                  <tr>
                    <td><strong>TeoCoin Versati:</strong></td>
                    <td className="text-primary">{formatTeoCoinAmount(escrow.teocoin_amount)}</td>
                  </tr>
                  <tr>
                    <td><strong>Data Creazione:</strong></td>
                    <td>{new Date(escrow.created_at).toLocaleDateString('it-IT')}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="border-top pt-3 mt-3">
            <h6>Sistema di Compensazione</h6>
            <div className="row">
              <div className="col-md-6">
                <div className="choice-option accept-option p-3 border rounded">
                  <h6 className="text-success">
                    <i className="feather icon-check-circle me-2"></i>
                    Se Accetti
                  </h6>
                  <p className="mb-2">Riceverai:</p>
                  <ul className="list-unstyled">
                    <li>💰 <strong>{formatEUR(escrow.teacher_compensation_eur)}</strong> in EUR</li>
                    <li>🪙 <strong>{formatTeoCoinAmount(escrow.teacher_compensation_tcn)}</strong> in TeoCoin</li>
                  </ul>
                  <small className="text-muted">
                    Lo studente accede al corso con lo sconto applicato
                  </small>
                </div>
              </div>
              <div className="col-md-6">
                <div className="choice-option reject-option p-3 border rounded">
                  <h6 className="text-danger">
                    <i className="feather icon-x-circle me-2"></i>
                    Se Rifiuti
                  </h6>
                  <p className="mb-2">Accadrà:</p>
                  <ul className="list-unstyled">
                    <li>💰 Lo studente paga <strong>{formatEUR(escrow.original_price)}</strong></li>
                    <li>🔄 I TeoCoin tornano allo studente</li>
                    <li>📚 Lo studente accede al corso normalmente</li>
                  </ul>
                  <small className="text-muted">
                    Nessuna penalità per nessuno
                  </small>
                </div>
              </div>
            </div>
          </div>

          {escrow.status === 'pending' && !timeInfo.expired && (
            <div className="border-top pt-3 mt-3">
              <div className="d-flex gap-3">
                <Button
                  variant="success"
                  onClick={() => handleAction('accept')}
                  disabled={actionLoading}
                  className="flex-fill"
                >
                  {actionLoading === 'accept' ? (
                    <Spinner animation="border" size="sm" />
                  ) : (
                    <>
                      <i className="feather icon-check me-2"></i>
                      Accetta Escrow
                    </>
                  )}
                </Button>
                <Button
                  variant="danger"
                  onClick={() => handleAction('reject')}
                  disabled={actionLoading}
                  className="flex-fill"
                >
                  {actionLoading === 'reject' ? (
                    <Spinner animation="border" size="sm" />
                  ) : (
                    <>
                      <i className="feather icon-x me-2"></i>
                      Rifiuta Escrow
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {error && (
            <Alert variant="danger" className="mt-3">
              {error}
            </Alert>
          )}
        </Modal.Body>
      </Modal>
    </>
  );
};

export default TeacherEscrowCard;

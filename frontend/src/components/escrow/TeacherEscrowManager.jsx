import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Spinner, Alert, Badge, Tabs, Tab } from 'react-bootstrap';
import TeacherEscrowCard from './TeacherEscrowCard';
import { 
  fetchTeacherEscrows, 
  fetchEscrowStats, 
  acceptEscrow, 
  rejectEscrow,
  formatTeoCoinAmount 
} from '../../services/api/escrow';

/**
 * TeacherEscrowManager Component
 * Main component for managing teacher escrows
 */
const TeacherEscrowManager = () => {
  const [escrows, setEscrows] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('pending');

  // Load escrows and stats
  const loadEscrowData = async () => {
    setLoading(true);
    setError('');
    
    try {
      const [escrowsRes, statsRes] = await Promise.all([
        fetchTeacherEscrows(),
        fetchEscrowStats()
      ]);
      
      setEscrows(escrowsRes.data);
      setStats(statsRes.data);
    } catch (err) {
      console.error('Error loading escrow data:', err);
      setError('Errore nel caricamento degli escrow');
    } finally {
      setLoading(false);
    }
  };

  // Handle escrow action (accept/reject)
  const handleEscrowAction = async (escrowId, action) => {
    try {
      if (action === 'accept') {
        await acceptEscrow(escrowId);
      } else if (action === 'reject') {
        await rejectEscrow(escrowId);
      }
      
      // Reload data after action
      await loadEscrowData();
    } catch (err) {
      throw err; // Re-throw to let the card component handle the error
    }
  };

  // Filter escrows by status
  const filterEscrowsByStatus = (status) => {
    return escrows.filter(escrow => escrow.status === status);
  };

  // Load data on component mount
  useEffect(() => {
    loadEscrowData();
  }, []);

  if (loading) {
    return (
      <Card>
        <Card.Body className="text-center py-5">
          <Spinner animation="border" variant="primary" />
          <p className="mt-3 mb-0">Caricamento escrow...</p>
        </Card.Body>
      </Card>
    );
  }

  // Get counts for each status
  const pendingCount = filterEscrowsByStatus('pending').length;
  const acceptedCount = filterEscrowsByStatus('accepted').length;
  const rejectedCount = filterEscrowsByStatus('rejected').length;
  const expiredCount = filterEscrowsByStatus('expired').length;

  return (
    <Card>
      <Card.Header>
        <div className="d-flex justify-content-between align-items-center">
          <div>
            <Card.Title as="h5" className="mb-1">
              <i className="feather icon-shield me-2"></i>
              TeoCoin Escrow Manager
            </Card.Title>
            <p className="text-muted mb-0 small">
              Gestisci i pagamenti TeoCoin in attesa della tua decisione
            </p>
          </div>
          {stats && (
            <div className="text-end">
              <div className="small text-muted">Totale in Escrow</div>
              <div className="h6 mb-0 text-warning">
                {formatTeoCoinAmount(stats.total_teocoin_in_escrow)}
              </div>
            </div>
          )}
        </div>
      </Card.Header>
      
      <Card.Body>
        {error && (
          <Alert variant="danger" className="mb-4">
            <i className="feather icon-alert-triangle me-2"></i>
            {error}
          </Alert>
        )}

        {/* Stats Summary */}
        {stats && (
          <Row className="mb-4">
            <Col md={3}>
              <div className="stat-box text-center p-3 border rounded">
                <div className="h4 mb-1 text-warning">{stats.pending_count}</div>
                <div className="small text-muted">In Attesa</div>
              </div>
            </Col>
            <Col md={3}>
              <div className="stat-box text-center p-3 border rounded">
                <div className="h4 mb-1 text-success">{stats.accepted_count}</div>
                <div className="small text-muted">Accettati</div>
              </div>
            </Col>
            <Col md={3}>
              <div className="stat-box text-center p-3 border rounded">
                <div className="h4 mb-1 text-danger">{stats.rejected_count}</div>
                <div className="small text-muted">Rifiutati</div>
              </div>
            </Col>
            <Col md={3}>
              <div className="stat-box text-center p-3 border rounded">
                <div className="h4 mb-1 text-secondary">{stats.expired_count}</div>
                <div className="small text-muted">Scaduti</div>
              </div>
            </Col>
          </Row>
        )}

        {/* Tabs for different escrow statuses */}
        <Tabs 
          activeKey={activeTab} 
          onSelect={(tab) => setActiveTab(tab)} 
          className="mb-4"
        >
          <Tab 
            eventKey="pending" 
            title={
              <span>
                In Attesa 
                {pendingCount > 0 && (
                  <Badge variant="warning" className="ms-2">{pendingCount}</Badge>
                )}
              </span>
            }
          >
            <div className="escrow-list">
              {pendingCount === 0 ? (
                <div className="text-center py-5">
                  <i className="feather icon-clock" style={{ fontSize: '3rem', color: '#999' }}></i>
                  <h5 className="mt-3 mb-2">Nessun escrow in attesa</h5>
                  <p className="text-muted">
                    Non ci sono pagamenti TeoCoin in attesa della tua decisione
                  </p>
                </div>
              ) : (
                <Row>
                  {filterEscrowsByStatus('pending').map(escrow => (
                    <Col key={escrow.id} lg={6} xl={4} className="mb-3">
                      <TeacherEscrowCard 
                        escrow={escrow} 
                        onEscrowAction={handleEscrowAction}
                      />
                    </Col>
                  ))}
                </Row>
              )}
            </div>
          </Tab>

          <Tab 
            eventKey="accepted" 
            title={
              <span>
                Accettati
                {acceptedCount > 0 && (
                  <Badge variant="success" className="ms-2">{acceptedCount}</Badge>
                )}
              </span>
            }
          >
            <div className="escrow-list">
              {acceptedCount === 0 ? (
                <div className="text-center py-5">
                  <i className="feather icon-check-circle" style={{ fontSize: '3rem', color: '#28a745' }}></i>
                  <h5 className="mt-3 mb-2">Nessun escrow accettato</h5>
                  <p className="text-muted">
                    Gli escrow accettati appariranno qui
                  </p>
                </div>
              ) : (
                <Row>
                  {filterEscrowsByStatus('accepted').map(escrow => (
                    <Col key={escrow.id} lg={6} xl={4} className="mb-3">
                      <TeacherEscrowCard 
                        escrow={escrow} 
                        onEscrowAction={handleEscrowAction}
                      />
                    </Col>
                  ))}
                </Row>
              )}
            </div>
          </Tab>

          <Tab 
            eventKey="history" 
            title="Storico"
          >
            <div className="escrow-list">
              {rejectedCount + expiredCount === 0 ? (
                <div className="text-center py-5">
                  <i className="feather icon-archive" style={{ fontSize: '3rem', color: '#6c757d' }}></i>
                  <h5 className="mt-3 mb-2">Nessuno storico</h5>
                  <p className="text-muted">
                    Gli escrow rifiutati e scaduti appariranno qui
                  </p>
                </div>
              ) : (
                <Row>
                  {[...filterEscrowsByStatus('rejected'), ...filterEscrowsByStatus('expired')]
                    .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
                    .map(escrow => (
                      <Col key={escrow.id} lg={6} xl={4} className="mb-3">
                        <TeacherEscrowCard 
                          escrow={escrow} 
                          onEscrowAction={handleEscrowAction}
                        />
                      </Col>
                    ))}
                </Row>
              )}
            </div>
          </Tab>
        </Tabs>

        {/* Additional Help Text */}
        <div className="border-top pt-3 mt-4">
          <Row>
            <Col md={6}>
              <div className="help-box">
                <h6 className="text-success">
                  <i className="feather icon-help-circle me-2"></i>
                  Come funziona?
                </h6>
                <ul className="small text-muted list-unstyled">
                  <li>• Gli studenti pagano con TeoCoin per ottenere sconti</li>
                  <li>• I TeoCoin vanno in escrow fino alla tua decisione</li>
                  <li>• Hai 7 giorni per accettare o rifiutare</li>
                  <li>• Se accetti: ricevi EUR ridotti + TeoCoin</li>
                  <li>• Se rifiuti: studente paga prezzo pieno</li>
                </ul>
              </div>
            </Col>
            <Col md={6}>
              <div className="help-box">
                <h6 className="text-info">
                  <i className="feather icon-clock me-2"></i>
                  Tempi
                </h6>
                <ul className="small text-muted list-unstyled">
                  <li>• Escrow attivi per 7 giorni</li>
                  <li>• Dopo 7 giorni: TeoCoin tornano alla piattaforma</li>
                  <li>• Studente paga comunque il prezzo pieno</li>
                  <li>• Nessuna penalità per nessuno</li>
                </ul>
              </div>
            </Col>
          </Row>
        </div>
      </Card.Body>
    </Card>
  );
};

export default TeacherEscrowManager;

import React, { useState, useEffect } from 'react';
import { Card, Badge, Button, Spinner, Table } from 'react-bootstrap';
import { blockchainAPI } from '../../services/api/blockchainAPI';

const TransactionHistory = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await blockchainAPI.getTransactionHistory();
      setTransactions(response.transactions || []);
    } catch (error) {
      setError('Errore nel caricamento delle transazioni');
      console.error('Error loading transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTransactionIcon = (type) => {
    switch (type) {
      case 'reward':
        return <i className="feather icon-gift text-success"></i>;
      case 'achievement':
        return <i className="feather icon-award text-warning"></i>;
      case 'course_completion':
        return <i className="feather icon-trending-up text-info"></i>;
      default:
        return <i className="feather icon-trending-up text-secondary"></i>;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'success':
        return <Badge bg="success">Completata</Badge>;
      case 'pending':
        return <Badge bg="warning">In corso</Badge>;
      case 'failed':
        return <Badge bg="danger">Fallita</Badge>;
      default:
        return <Badge bg="secondary">{status}</Badge>;
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  return (
    <Card className="mb-4">
      <Card.Header className="d-flex justify-content-between align-items-center">
        <Card.Title className="mb-0 d-flex align-items-center">
          <i className="feather icon-activity me-2 text-primary"></i>
          Transazioni TeoCoin
        </Card.Title>
        <Button 
          variant="outline-primary" 
          size="sm" 
          onClick={loadTransactions} 
          disabled={loading}
        >
          <i className="feather icon-refresh-cw me-1"></i>
          Aggiorna
        </Button>
      </Card.Header>
      <Card.Body>
        {error && (
          <div className="alert alert-danger" role="alert">
            <i className="feather icon-alert-circle me-2"></i>
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-4">
            <Spinner animation="border" variant="primary" />
            <p className="mt-2 text-muted">Caricamento transazioni...</p>
          </div>
        ) : transactions.length > 0 ? (
          <div className="table-responsive">
            <Table hover className="align-middle">
              <thead>
                <tr>
                  <th>Tipo</th>
                  <th>Data</th>
                  <th>Importo</th>
                  <th>Stato</th>
                  <th>Hash</th>
                  <th>Azioni</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx, index) => (
                  <tr key={index}>
                    <td>
                      <div className="d-flex align-items-center">
                        <span className="me-2">{getTransactionIcon(tx.type)}</span>
                        <span className="text-capitalize">{tx.type.replace('_', ' ')}</span>
                      </div>
                    </td>
                    <td>
                      <div className="d-flex align-items-center">
                        <i className="feather icon-clock me-1 text-muted"></i>
                        <small>{formatDate(tx.timestamp)}</small>
                      </div>
                    </td>
                    <td>
                      <strong className="text-success">+{tx.amount} TEC</strong>
                    </td>
                    <td>{getStatusBadge(tx.status)}</td>
                    <td>
                      <small className="text-muted">{tx.hash ? tx.hash.substring(0, 10) + '...' : 'N/A'}</small>
                    </td>
                    <td>
                      {tx.hash && (
                        <Button 
                          variant="link" 
                          size="sm" 
                          className="p-0"
                          href={`https://etherscan.io/tx/${tx.hash}`} 
                          target="_blank" 
                          rel="noopener noreferrer"
                        >
                          <i className="feather icon-external-link"></i>
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </div>
        ) : (
          <div className="text-center py-4">
            <i className="feather icon-inbox mb-3" style={{fontSize: '2rem', opacity: 0.5}}></i>
            <p className="text-muted mb-0">Nessuna transazione disponibile</p>
          </div>
        )}
      </Card.Body>
      <Card.Footer className="text-center text-muted">
        <small>Le transazioni potrebbero richiedere tempo per essere confermate sulla blockchain</small>
      </Card.Footer>
    </Card>
  );
};

export default TransactionHistory;

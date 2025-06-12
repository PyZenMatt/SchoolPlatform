import React, { useState, useEffect } from 'react';
import { Spinner, Button } from 'react-bootstrap';
import { blockchainAPI } from '../../services/api/blockchainAPI';

const DashboardTransactionHistory = ({ user, showTitle = true, maxTransactions = 10 }) => {
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

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const openTransaction = (txHash) => {
    if (txHash) {
      // Ensure hash has 0x prefix for blockchain explorer
      const formattedHash = txHash.startsWith('0x') ? txHash : `0x${txHash}`;
      window.open(`https://amoy.polygonscan.com/tx/${formattedHash}`, '_blank');
    }
  };

  const formatTransactionHash = (hash) => {
    if (!hash) return null;
    // Ensure hash has 0x prefix for display
    return hash.startsWith('0x') ? hash : `0x${hash}`;
  };

  if (loading) {
    return (
      <div className="text-center py-4">
        <Spinner animation="border" size="sm" />
        <p className="mt-2 mb-0 text-muted">Caricamento transazioni...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-4">
        <i className="feather icon-alert-triangle text-danger f-30 mb-3"></i>
        <p className="text-danger mb-3">{error}</p>
        <Button variant="outline-primary" size="sm" onClick={loadTransactions}>
          <i className="feather icon-refresh-cw me-1"></i>
          Riprova
        </Button>
      </div>
    );
  }

  const displayTransactions = transactions.slice(0, maxTransactions);

  return (
    <>
      <div className="d-flex justify-content-between align-items-start mb-3">
        <div className="h6 text-muted mb-0 card-title h5">
          <i className="feather icon-list me-2"></i>
          Transazioni Recenti
        </div>
        <small className="text-muted">
          {displayTransactions.length > 0 
            ? `Ultime ${displayTransactions.length} transazioni` 
            : 'Nessuna transazione'
          }
        </small>
      </div>
      
      {displayTransactions.length === 0 ? (
        <div className="text-center py-4">
          <i className="feather icon-inbox text-muted" style={{ fontSize: '3rem', opacity: 0.5 }}></i>
          <p className="mt-3 mb-0 text-muted">Nessuna transazione trovata</p>
          <small className="text-muted">Le tue transazioni TeoCoins appariranno qui</small>
        </div>
      ) : (
        <>
          <div className="transactions-list mb-3">
            {displayTransactions.map((transaction, index) => (
              <div key={transaction.id || index} className="transaction-item border-bottom pb-3 mb-3 wallet-style">
                <div className="d-flex align-items-start">
                  <div className="transaction-icon me-3">
                    {transaction.transaction_type?.includes('reward') || 
                     transaction.transaction_type?.includes('exercise') || 
                     transaction.type === 'reward' || 
                     transaction.type === 'achievement' ? (
                      <div className="icon-wrapper bg-success text-white rounded-circle p-2">
                        <i className="feather icon-gift"></i>
                      </div>
                    ) : (transaction.amount || 0) > 0 ? (
                      <div className="icon-wrapper bg-success text-white rounded-circle p-2">
                        <i className="feather icon-arrow-down-left"></i>
                      </div>
                    ) : (
                      <div className="icon-wrapper bg-danger text-white rounded-circle p-2">
                        <i className="feather icon-arrow-up-right"></i>
                      </div>
                    )}
                  </div>
                  
                  <div className="transaction-details flex-grow-1">
                    <div className="d-flex justify-content-between align-items-start">
                      <div>
                        <div className="transaction-title fw-bold">
                          {transaction.description || 
                           (transaction.transaction_type ? 
                            transaction.transaction_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 
                            'Transazione')
                          }
                        </div>
                        <div className="transaction-meta small text-muted">
                          {(transaction.tx_hash || transaction.transaction_hash) && (
                            <div className="hash mb-1">
                              <strong style={{ color: '#ecf0f1' }}>Hash:</strong> 
                              <code className="ms-1 small" style={{ color: '#bdc3c7', backgroundColor: 'rgba(255,255,255,0.1)', padding: '2px 4px', borderRadius: '3px' }}>
                                {formatTransactionHash(transaction.tx_hash || transaction.transaction_hash)}
                              </code>
                              <Button
                                variant="link"
                                size="sm"
                                className="p-0 ms-2 text-decoration-none"
                                style={{ color: '#3498db' }}
                                onClick={() => openTransaction(transaction.tx_hash || transaction.transaction_hash)}
                                title="Vedi su Polygonscan"
                              >
                                <i className="feather icon-external-link" style={{ fontSize: '0.8rem' }}></i>
                              </Button>
                            </div>
                          )}
                          {(transaction.created_at || transaction.date) && (
                            <div className="date">
                              {formatDate(transaction.created_at || transaction.date)}
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <div className="transaction-amount text-end">
                        <span className={`amount fw-bold ${parseFloat(transaction.amount || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                          {parseFloat(transaction.amount || 0) >= 0 ? '+' : ''}{parseFloat(transaction.amount || 0).toFixed(4)} TEO
                        </span>
                        {(transaction.tx_hash || transaction.transaction_hash) && (
                          <div className="mt-1">
                            <Button
                              variant="outline-light"
                              size="sm"
                              className="p-1"
                              onClick={() => openTransaction(transaction.tx_hash || transaction.transaction_hash)}
                              title="Vedi su Blockchain"
                              style={{ minWidth: 'auto', borderColor: 'rgba(255,255,255,0.3)' }}
                            >
                              <i className="feather icon-external-link"></i>
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="balance-details">
            <small className="text-muted d-block">Network: Polygon Amoy</small>
            <small className="text-muted">
              Ultime {displayTransactions.length} transazioni
            </small>
          </div>

          <Button 
            variant="outline-primary" 
            size="sm" 
            className="refresh-btn mt-3 w-100"
            onClick={loadTransactions}
          >
            <i className="feather icon-refresh-cw me-1"></i>
            Aggiorna
          </Button>
        </>
      )}
    </>
  );
};

export default DashboardTransactionHistory;

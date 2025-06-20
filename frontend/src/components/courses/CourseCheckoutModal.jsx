import React, { useState } from 'react';
import { Modal, Button, Alert, Spinner } from 'react-bootstrap';
import { purchaseCourse } from '../../services/api/courses';
import { web3Service } from '../../services/api/web3Service';
import { useAuth } from '../../contexts/AuthContext';

/**
 * CourseCheckoutModal - Handles the blockchain-based checkout process for courses
 * 
 * This component:
 * 1. Checks for wallet connection
 * 2. Verifies blockchain balance in real-time
 * 3. Confirms the purchase with the user
 * 4. Handles the blockchain transaction
 * 5. Shows transaction hash and success/error status
 */
const CourseCheckoutModal = ({ course, show, handleClose, onPurchaseComplete }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState('confirm'); // confirm, purchasing, success
  const [blockchainBalance, setBlockchainBalance] = useState(0);
  const [maticBalance, setMaticBalance] = useState(0);
  const [transactionHash, setTransactionHash] = useState('');

  // Determina se il wallet è connesso dal profilo utente
  const walletConnected = Boolean(user?.wallet_address);
  // Always use the user's registered wallet address, not MetaMask current account
  const walletAddress = user?.wallet_address;

  // Carica i saldi quando si apre il modal
  React.useEffect(() => {
    const loadBalances = async () => {
      if (!show || !walletAddress) return;
      
      try {
        console.log('💰 Caricamento saldi per wallet profilo:', walletAddress);
        
        // Carica i saldi usando l'indirizzo del profilo utente
        const [teoBalance, maticBalanceData] = await Promise.all([
          web3Service.getBalance(walletAddress),
          web3Service.getMaticBalance(walletAddress)
        ]);
        
        setBlockchainBalance(parseFloat(teoBalance));
        setMaticBalance(parseFloat(maticBalanceData));
        
        console.log('💰 Saldi caricati - TEO:', teoBalance, 'MATIC:', maticBalanceData);
        
      } catch (err) {
        console.error('Errore nel caricamento saldi:', err);
        
        // Gestisci specificamente l'errore di wallet non specificato
        if (err.message && err.message.includes('Nessun indirizzo wallet specificato')) {
          setError('Devi collegare un wallet dal tuo profilo prima di visualizzare i saldi');
        } else {
          setError('Errore nel caricamento dei saldi wallet');
        }
      }
    };
    
    if (show) {
      setError(''); // Reset errori quando si apre il modal
      loadBalances();
    }
  }, [show, walletAddress]);

  const handleConfirmPurchase = async () => {
    // Controllo se l'utente ha un wallet collegato nel profilo
    if (!user?.wallet_address) {
      setError('Devi collegare un wallet dal tuo profilo prima di procedere con l\'acquisto');
      return;
    }

    // Controllo se ha abbastanza TeoCoin
    if (blockchainBalance < course.price) {
      setError(`TeoCoin insufficienti. Necessari: ${course.price} TEO, Disponibili: ${blockchainBalance.toFixed(2)} TEO`);
      return;
    }

    // Check if user has sufficient MATIC for gas fees
    const minMaticRequired = 0.01; // Minimum MATIC required for gas
    if (maticBalance < minMaticRequired) {
      setError(
        `MATIC insufficienti per gas fees. ` +
        `Hai ${maticBalance.toFixed(4)} MATIC, servono almeno ${minMaticRequired} MATIC. ` +
        `Ottieni MATIC da: https://faucet.polygon.technology/`
      );
      return;
    }

    setLoading(true);
    setError('');
    setStep('purchasing');
    
    try {
      // Check if teacher has a wallet address
      if (!course.teacher.wallet_address) {
        throw new Error('Il docente non ha configurato un wallet per ricevere i pagamenti');
      }

      // Execute the NEW APPROVE+SPLIT course payment logic
      console.log('🎓 Processing course payment with APPROVE+SPLIT PROCESS...');
      const result = await web3Service.processCoursePaymentDirect(
        walletAddress,                // student address
        course.teacher.wallet_address, // teacher address
        course.price,                 // course price
        course.id                     // course id
      );

      setTransactionHash(result.teacherTxHash || 'N/A');
      
      // Update balances after successful payment
      const [newTeoBalance, newMaticBalance] = await Promise.all([
        web3Service.getBalance(walletAddress),
        web3Service.getMaticBalance(walletAddress)
      ]);
      
      setBlockchainBalance(parseFloat(newTeoBalance));
      setMaticBalance(parseFloat(newMaticBalance));
      
      setStep('success');
      setLoading(false);
      
      // Call the parent callback to refresh course enrollment
      if (onPurchaseComplete) {
        onPurchaseComplete();
      }
      
    } catch (err) {
      console.error('Error during course purchase:', err);
      
      let errorMsg = 'Errore durante l\'acquisto del corso.';
      if (err.message) {
        errorMsg = err.message;
      }
      
      setError(errorMsg);
      setStep('confirm');
      setLoading(false);
    }
  };

  const refreshBalances = async () => {
    if (!walletConnected || !walletAddress) {
      return;
    }
    
    try {
      console.log('🔄 Refreshing balances for wallet:', walletAddress);
      
      const [teoBalance, maticBalanceData] = await Promise.all([
        web3Service.getBalance(walletAddress),
        web3Service.getMaticBalance(walletAddress)
      ]);
      
      console.log('💰 Refreshed TEO:', teoBalance, 'MATIC:', maticBalanceData);
      
      setBlockchainBalance(parseFloat(teoBalance));
      setMaticBalance(parseFloat(maticBalanceData));
    } catch (err) {
      console.error('Error refreshing balances:', err);
    }
  };

  const renderStepContent = () => {
    switch (step) {
      case 'connecting':
        return (
          <div className="text-center p-4">
            <Spinner animation="border" className="mb-3" />
            <p>Connessione al wallet in corso...</p>
          </div>
        );
        
      case 'purchasing':
        return (
          <div className="text-center p-4">
            <Spinner animation="border" className="mb-3" />
            <p>Acquisto in corso...</p>
            <small className="text-muted">Non chiudere questa finestra</small>
          </div>
        );
        
      case 'success':
        return (
          <div className="text-center p-4">
            <div className="mb-3 text-success">
              <i className="feather icon-check-circle" style={{ fontSize: '48px' }}></i>
            </div>
            <h5>Acquisto completato!</h5>
            <p>Hai acquistato con successo il corso "{course?.title}".</p>
            {transactionHash && (
              <div className="mb-3">
                <small className="text-muted">Hash transazione:</small>
                <br />
                <code className="text-break" style={{ fontSize: '12px' }}>
                  {transactionHash}
                </code>
              </div>
            )}
            <Button variant="primary" onClick={handleClose}>
              Inizia a studiare
            </Button>
          </div>
        );
        
      case 'confirm':
      default:
        return (
          <>
            <Modal.Header closeButton>
              <Modal.Title>Acquista Corso</Modal.Title>
            </Modal.Header>
            
            <Modal.Body>
              {error && <Alert variant="danger">{error}</Alert>}
              
              {/* Info sul nuovo processo */}
              <Alert variant="info" className="mb-3">
                <i className="feather icon-info me-2"></i>
                <strong>Sistema di pagamento semplificato:</strong> Dovrai firmare UNA SOLA volta su MetaMask 
                per approvare i token. Il sistema distribuirà automaticamente i fondi al teacher (85%) 
                e alla piattaforma (15%). Gas fees minimizzate!
              </Alert>
              
              <div className="d-flex align-items-center mb-4">
                <div className="me-3">
                  {course?.thumbnail && (
                    <img 
                      src={course.thumbnail} 
                      alt={course?.title} 
                      style={{ width: '80px', height: '60px', objectFit: 'cover', borderRadius: '4px' }}
                    />
                  )}
                </div>
                <div>
                  <h5 className="mb-1">{course?.title}</h5>
                  <p className="mb-0 text-muted">
                    {course?.teacher_name || 'Insegnante'} • {course?.category_name || 'Categoria'}
                  </p>
                </div>
              </div>
              
              <div className="mb-4">
                <div className="d-flex justify-content-between mb-2">
                  <span>Prezzo corso</span>
                  <span className="fw-bold">{course?.price} TEO</span>
                </div>
                <div className="d-flex justify-content-between text-muted small">
                  <span>Commissione piattaforma (15%)</span>
                  <span>{Math.round(course?.price * 0.15 * 100) / 100} TEO</span>
                </div>
              {walletConnected && (
                <Alert variant="info" className="d-flex justify-content-between align-items-center">
                  <div>
                    <i className="feather icon-lock me-2"></i>
                    <strong>Wallet registrato:</strong>
                    <br />
                    <code className="text-break" style={{ fontSize: '12px' }}>
                      {walletAddress}
                    </code>
                    <br />
                    <small className="text-muted">
                      Wallet collegato al tuo profilo utente
                    </small>
                  </div>
                  <Button 
                    variant="outline-secondary" 
                    size="sm"
                    onClick={() => {
                      // Nota: per disconnettere il wallet, l'utente deve andare nel profilo
                      // Qui possiamo solo mostrare un messaggio informativo
                      alert('Per disconnettere il wallet, vai nel tuo profilo utente');
                    }}
                  >
                    <i className="feather icon-log-out me-1"></i>
                    Disconnetti
                  </Button>
                </Alert>
              )}
              
              {walletConnected && (
                <>
                  <div className="d-flex justify-content-between mt-2">
                    <span className="text-muted">Saldo TeoCoin</span>
                    <span className={`fw-bold ${blockchainBalance >= course?.price ? 'text-success' : 'text-danger'}`}>
                      {blockchainBalance.toFixed(2)} TEO
                    </span>
                  </div>
                  <div className="d-flex justify-content-between mt-1">
                    <span className="text-muted">Saldo MATIC (gas)</span>
                    <span className={`fw-bold ${maticBalance >= 0.01 ? 'text-success' : 'text-danger'}`}>
                      {maticBalance.toFixed(4)} MATIC
                    </span>
                  </div>
                </>
              )}
              </div>
              
              {walletConnected && (blockchainBalance < course?.price || maticBalance < 0.01) && (
                <Alert variant="warning">
                  <i className="feather icon-alert-triangle me-2"></i>
                  {blockchainBalance < course?.price && (
                    <div>
                      <strong>⚠️ TeoCoin insufficienti!</strong> Hai bisogno di almeno {course?.price} TEO per acquistare questo corso.
                    </div>
                  )}
                  {maticBalance < 0.01 && (
                    <div>
                      <strong>⚠️ MATIC insufficienti!</strong> Hai bisogno di almeno 0.01 MATIC per pagare le gas fees. 
                      <br />
                      <a href="https://faucet.polygon.technology/" target="_blank" rel="noopener noreferrer" className="text-decoration-none">
                        Ottieni MATIC dal faucet Polygon →
                      </a>
                    </div>
                  )}
                </Alert>
              )}
              
              {!walletConnected && (
                <Alert variant="info">
                  <i className="feather icon-info me-2"></i>
                  Connetti il tuo wallet per vedere i tuoi saldi e procedere con l'acquisto.
                </Alert>
              )}
            </Modal.Body>
            
            <Modal.Footer>
              <Button variant="secondary" onClick={handleClose}>
                Annulla
              </Button>
              
              {!walletConnected ? (
                <Button variant="primary" onClick={connectWallet} disabled={loading}>
                  <i className="feather icon-link me-2"></i>
                  Connetti Wallet
                </Button>
              ) : (
                <Button 
                  variant="primary" 
                  onClick={handleConfirmPurchase} 
                  disabled={loading || blockchainBalance < course?.price || maticBalance < 0.01}
                >
                  <i className="feather icon-shopping-cart me-2"></i>
                  {blockchainBalance < course?.price ? 
                    'TeoCoin insufficienti' : 
                    maticBalance < 0.01 ?
                    'MATIC insufficienti' :
                    `Conferma Acquisto (${course?.price} TEO)`
                  }
                </Button>
              )}
            </Modal.Footer>
          </>
        );
    }
  };

  return (
    <Modal 
      show={show} 
      onHide={handleClose}
      backdrop="static"
      keyboard={step !== 'purchasing'}
      centered
    >
      {renderStepContent()}
    </Modal>
  );
};

export default CourseCheckoutModal;

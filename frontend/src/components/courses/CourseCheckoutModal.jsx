import React, { useState } from 'react';
import { Modal, Button, Alert, Spinner, Nav, Tab } from 'react-bootstrap';
import { purchaseCourse } from '../../services/api/courses';
import { web3Service } from '../../services/api/web3Service';
import { useAuth } from '../../contexts/AuthContext';
import PaymentModal from '../PaymentModal';

/**
 * Enhanced CourseCheckoutModal - Supports both Stripe and TeoCoin payments
 * 
 * This component provides two payment options:
 * 1. Fiat payment via Stripe (EUR) with TeoCoin rewards
 * 2. TeoCoin payment with discount (existing blockchain flow)
 */
const CourseCheckoutModal = ({ course, show, handleClose, onPurchaseComplete }) => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('fiat'); // 'fiat' or 'teocoin'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState('confirm'); // confirm, purchasing, success
  const [blockchainBalance, setBlockchainBalance] = useState(0);
  const [maticBalance, setMaticBalance] = useState(0);
  const [transactionHash, setTransactionHash] = useState('');
  const [paymentResult, setPaymentResult] = useState(null);

  // Wallet connection status
  const walletConnected = Boolean(user?.wallet_address);
  const walletAddress = user?.wallet_address;

  // Calculate pricing options
  const fiatPrice = course?.price_eur || 0;
  const teoReward = course?.teocoin_reward || 0;
  const teoDiscount = course?.teocoin_discount_percent || 10;
  const teoPrice = course?.price || 0;
  const discountedTeoPrice = teoPrice * (1 - teoDiscount / 100);

  // Load balances when modal opens (for TeoCoin tab)
  React.useEffect(() => {
    const loadBalances = async () => {
      if (!show || !walletAddress || activeTab !== 'teocoin') return;
      
      try {
        console.log('💰 Loading balances for wallet:', walletAddress);
        
        const [teoBalance, maticBalanceData] = await Promise.all([
          web3Service.getBalance(walletAddress),
          web3Service.getMaticBalance(walletAddress)
        ]);
        
        setBlockchainBalance(parseFloat(teoBalance));
        setMaticBalance(parseFloat(maticBalanceData));
        
        console.log('💰 Balances loaded - TEO:', teoBalance, 'MATIC:', maticBalanceData);
        
      } catch (err) {
        console.error('Error loading balances:', err);
        if (err.message && err.message.includes('Nessun indirizzo wallet specificato')) {
          setError('Devi collegare un wallet dal tuo profilo prima di visualizzare i saldi');
        } else {
          setError('Errore nel caricamento dei saldi wallet');
        }
      }
    };
    
    if (show) {
      setError('');
      setStep('confirm');
      setPaymentResult(null);
      loadBalances();
    }
  }, [show, walletAddress, activeTab]);

  // Handle Stripe payment success
  const handleStripeSuccess = (result) => {
    setPaymentResult(result);
    setStep('success');
  };

  // Handle Stripe payment error  
  const handleStripeError = (error) => {
    setError(error);
    setStep('confirm');
  };

  // Layer 2 gas-free TeoCoin discount (UPDATED)
  const handleTeoCoinDiscount = async () => {
    console.log('🚀 Processing Layer 2 gas-free TeoCoin discount...');
    
    if (!user?.wallet_address) {
      setError('Devi collegare un wallet dal tuo profilo prima di procedere con l\'acquisto');
      return;
    }

    if (blockchainBalance < discountedTeoPrice) {
      setError(`TeoCoin insufficienti. Necessari: ${discountedTeoPrice.toFixed(2)} TEO, Disponibili: ${blockchainBalance.toFixed(2)} TEO`);
      return;
    }

    // ✅ NO MORE MATIC CHECK - Layer 2 handles all gas fees!
    console.log('⛽ Gas cost for student: 0 ETH (Layer 2 covers all fees)');

    setLoading(true);
    setError('');
    setStep('purchasing');
    
    try {
      if (!course.teacher.wallet_address) {
        throw new Error('Il docente non ha configurato un wallet per ricevere i pagamenti');
      }

      // Use Layer 2 gas-free transfer instead of old web3Service
      console.log('🎓 Processing Layer 2 TeoCoin course payment...');
      
      // Create Layer 2 payment request
      const response = await fetch('/api/v1/services/discount/layer2/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
        body: JSON.stringify({
          course_id: parseInt(course.id),
          discount_amount: 0, // Full TEO payment, not discount
          discount_percentage: 0,
          student_wallet: walletAddress,
          teo_amount: discountedTeoPrice // Full TEO price
        })
      });

      const data = await response.json();
      
      if (data.success) {
        console.log('✅ Layer 2 TeoCoin payment processed successfully!');
        setTransactionHash(data.data.transaction_hash || 'Layer2-' + Date.now());
      if (data.success) {
        console.log('✅ Layer 2 TeoCoin payment processed successfully!');
        setTransactionHash(data.data.transaction_hash || 'Layer2-' + Date.now());
        
        // Complete the course purchase
        const purchaseResult = await purchaseCourse(course.id, {
          payment_method: 'teocoin_layer2',
          transaction_hash: data.data.transaction_hash,
          teo_amount: discountedTeoPrice,
          gas_free: true,
          layer2_processed: true
        });

        if (purchaseResult.success) {
          // Update balances after successful payment
          const [newTeoBalance, newMaticBalance] = await Promise.all([
            web3Service.getBalance(walletAddress),
            web3Service.getMaticBalance(walletAddress)
          ]);
          
          setBlockchainBalance(parseFloat(newTeoBalance));
          setMaticBalance(parseFloat(newMaticBalance));
          
          setStep('success');
          setLoading(false);
          
          if (onPurchaseComplete) {
            onPurchaseComplete();
          }
        } else {
          throw new Error(purchaseResult.error || 'Purchase completion failed');
        }
      } else {
        throw new Error(data.error || 'Layer 2 payment failed');
      }
      
    } catch (err) {
      console.error('❌ Layer 2 TeoCoin payment failed:', err);
      setError(`Pagamento fallito: ${err.message}`);
      setStep('confirm');
      setLoading(false);
    }
  };

  const refreshBalances = async () => {
    if (!walletConnected || !walletAddress) return;
    
    try {
      const [teoBalance, maticBalanceData] = await Promise.all([
        web3Service.getBalance(walletAddress),
        web3Service.getMaticBalance(walletAddress)
      ]);
      
      setBlockchainBalance(parseFloat(teoBalance));
      setMaticBalance(parseFloat(maticBalanceData));
    } catch (err) {
      console.error('Error refreshing balances:', err);
    }
  };

  const renderFiatPaymentTab = () => {
    if (step === 'success' && paymentResult) {
      return (
        <div className="text-center p-4">
          <div className="mb-3 text-success">
            <i className="feather icon-check-circle" style={{ fontSize: '48px' }}></i>
          </div>
          <h5>Pagamento completato!</h5>
          <p>Hai acquistato con successo il corso "{course?.title}".</p>
          <div className="mb-3">
            <strong>€{fiatPrice}</strong> pagati
            <br />
            <span className="text-success">+{teoReward} TEO</span> guadagnati come ricompensa!
          </div>
          <Button variant="primary" onClick={handleClose}>
            Accedi al corso
          </Button>
        </div>
      );
    }

    return (
      <div className="p-3">
        <div className="payment-option-card mb-4 p-3" style={{ border: '2px solid #007bff', borderRadius: '8px', backgroundColor: '#f8f9ff' }}>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h5 className="mb-0 text-primary">💳 Pagamento con Carta</h5>
            <span className="badge badge-primary">Consigliato</span>
          </div>
          <div className="row">
            <div className="col-6">
              <strong>Prezzo: €{fiatPrice}</strong>
            </div>
            <div className="col-6 text-end">
              <span className="text-success">+{teoReward} TEO Reward</span>
            </div>
          </div>
          <small className="text-muted">
            Pagamento sicuro con Stripe. Ricevi {teoReward} TeoCoin come ricompensa al completamento del corso.
          </small>
        </div>

        {error && (
          <Alert variant="danger" className="mb-3">
            {error}
          </Alert>
        )}

        <PaymentModal
          course={course}
          onSuccess={handleStripeSuccess}
          onError={handleStripeError}
          embedded={true}
        />
      </div>
    );
  };

  const renderTeoCoinPaymentTab = () => {
    if (step === 'purchasing') {
      return (
        <div className="text-center p-4">
          <Spinner animation="border" className="mb-3" />
          <p>Acquisto in corso...</p>
          <small className="text-muted">Non chiudere questa finestra</small>
        </div>
      );
    }

    if (step === 'success') {
      return (
        <div className="text-center p-4">
          <div className="mb-3 text-success">
            <i className="feather icon-check-circle" style={{ fontSize: '48px' }}></i>
          </div>
          <h5>Acquisto completato!</h5>
          <p>Hai acquistato con successo il corso "{course?.title}" con TeoCoin.</p>
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
            Accedi al corso
          </Button>
        </div>
      );
    }

    return (
      <div className="p-3">
        <div className="payment-option-card mb-4 p-3" style={{ border: '2px solid #28a745', borderRadius: '8px', backgroundColor: '#f8fff9' }}>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h5 className="mb-0 text-success">🪙 Pagamento con TeoCoin</h5>
            <span className="badge badge-success">{teoDiscount}% Sconto</span>
          </div>
          <div className="row">
            <div className="col-6">
              <strong>{discountedTeoPrice.toFixed(2)} TEO</strong>
              <br />
              <small className="text-muted">
                <s>{teoPrice} TEO</s> (-{teoDiscount}%)
              </small>
            </div>
            <div className="col-6 text-end">
              <span className="text-success">Sconto esclusivo</span>
            </div>
          </div>
        </div>

        {!walletConnected && (
          <Alert variant="warning">
            <strong>Wallet non collegato</strong>
            <br />
            Devi collegare un wallet dal tuo profilo per procedere con il pagamento TeoCoin.
          </Alert>
        )}

        {walletConnected && (
          <div className="wallet-info mb-3 p-3" style={{ backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
            <h6>💼 Saldo Wallet</h6>
            <div className="row">
              <div className="col-6">
                <span className="text-muted">TEO:</span> <strong>{blockchainBalance.toFixed(2)}</strong>
              </div>
              <div className="col-6">
                <span className="text-muted">MATIC:</span> <strong>{maticBalance.toFixed(4)}</strong>
              </div>
            </div>
            <Button variant="outline-secondary" size="sm" onClick={refreshBalances} className="mt-2">
              🔄 Aggiorna saldi
            </Button>
          </div>
        )}

        {error && (
          <Alert variant="danger" className="mb-3">
            {error}
          </Alert>
        )}

        <div className="d-grid">
          <Button
            variant="success"
            size="lg"
            onClick={handleTeoCoinDiscount}
            disabled={loading || !walletConnected || blockchainBalance < discountedTeoPrice}
          >
            {loading ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Elaborazione...
              </>
            ) : (
              `Acquista con ${discountedTeoPrice.toFixed(2)} TEO`
            )}
          </Button>
        </div>
      </div>
    );
  };

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
                    <span className="fw-bold text-success">
                      🚀 Gas-Free (Layer 2)
                    </span>
                  </div>
                </>
              )}
              </div>
              
              {walletConnected && blockchainBalance < course?.price && (
                <Alert variant="warning">
                  <i className="feather icon-alert-triangle me-2"></i>
                  <div>
                    <strong>⚠️ TeoCoin insufficienti!</strong> Hai bisogno di almeno {course?.price} TEO per acquistare questo corso.
                  </div>
                </Alert>
              )}
              
              {walletConnected && blockchainBalance >= course?.price && (
                <Alert variant="success">
                  <i className="feather icon-check-circle me-2"></i>
                  <div>
                    <strong>✅ Pronto per l'acquisto gas-free!</strong> 
                    <br />
                    🚀 Layer 2 coprirà tutte le gas fees - paghi 0 ETH per il gas!
                  </div>
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
                  disabled={loading || blockchainBalance < course?.price}
                >
                  <i className="feather icon-shopping-cart me-2"></i>
                  {blockchainBalance < course?.price ? 
                    'TeoCoin insufficienti' : 
                    `🚀 Acquista Gas-Free (${course?.price} TEO)`
                  }
                </Button>
              )}
            </Modal.Footer>
          </>
        );
    }
  };

  return (
    <Modal show={show} onHide={handleClose} size="lg" centered>
      <Modal.Header closeButton>
        <Modal.Title>
          💳 Acquista Corso: {course?.title}
        </Modal.Title>
      </Modal.Header>
      
      <Modal.Body>
        <Tab.Container activeKey={activeTab} onSelect={setActiveTab}>
          <Nav variant="pills" className="justify-content-center mb-4">
            <Nav.Item>
              <Nav.Link eventKey="fiat" className="mx-2">
                💳 Carta di Credito
              </Nav.Link>
            </Nav.Item>
            <Nav.Item>
              <Nav.Link eventKey="teocoin" className="mx-2">
                🪙 TeoCoin
              </Nav.Link>
            </Nav.Item>
          </Nav>

          <Tab.Content>
            <Tab.Pane eventKey="fiat">
              {renderFiatPaymentTab()}
            </Tab.Pane>
            
            <Tab.Pane eventKey="teocoin">
              {renderTeoCoinPaymentTab()}
            </Tab.Pane>
          </Tab.Content>
        </Tab.Container>
      </Modal.Body>
      
      {step === 'confirm' && (
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose}>
            Annulla
          </Button>
        </Modal.Footer>
      )}
    </Modal>
  );
};

export default CourseCheckoutModal;

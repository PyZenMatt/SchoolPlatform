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
  // Use backend-calculated teocoin_price if available
  const discountedTeoPrice = course?.teocoin_price || 0;
  // For strikethrough display, show the original (non-discounted) TEO price
  const teoPrice = course?.price_eur ? course.price_eur * 10 : 0;

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
    if (onPurchaseComplete) {
      onPurchaseComplete();
    }
  };

  // Handle Stripe payment error  
  const handleStripeError = (error) => {
    setError(error);
    setStep('confirm');
  };

  // Handle TeoCoin payment (existing logic)
  const handleTeoCoinPurchase = async () => {
    if (!user?.wallet_address) {
      setError('Devi collegare un wallet dal tuo profilo prima di procedere con l\'acquisto');
      return;
    }

    if (blockchainBalance < discountedTeoPrice) {
      setError(`TeoCoin insufficienti. Necessari: ${discountedTeoPrice.toFixed(2)} TEO, Disponibili: ${blockchainBalance.toFixed(2)} TEO`);
      return;
    }

    const minMaticRequired = 0.01;
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
      if (!course.teacher.wallet_address) {
        throw new Error('Il docente non ha configurato un wallet per ricevere i pagamenti');
      }

      console.log('🎓 Processing TeoCoin course payment...');
      const result = await web3Service.processCoursePaymentDirect(
        walletAddress,
        course.teacher.wallet_address,
        discountedTeoPrice,
        course.id
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
      
      if (onPurchaseComplete) {
        onPurchaseComplete();
      }
      
    } catch (err) {
      console.error('Error during TeoCoin purchase:', err);
      setError(err.message || 'Errore durante l\'acquisto del corso con TeoCoin.');
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
          onClose={handleClose}
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

    if (step === 'success' && !paymentResult) {
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
            onClick={handleTeoCoinPurchase}
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

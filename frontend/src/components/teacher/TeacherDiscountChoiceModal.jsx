import React, { useState } from 'react';
import { Modal, Button, Alert, Badge, Spinner } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';

/**
 * PHASE 3.3: Teacher Discount Choice Modal
 * 
 * Allows teachers to make decisions on student discount requests:
 * - Accept TeoCoin: Get TEO tokens + bonus
 * - Take Full Fiat: Get full EUR payment
 */
const TeacherDiscountChoiceModal = ({ 
    show, 
    handleClose, 
    discountRequest, 
    onChoice 
}) => {
    const { user } = useAuth();
    const [processing, setProcessing] = useState(false);
    const [error, setError] = useState('');

    const handleChoice = async (choice) => {
        if (!discountRequest) return;
        
        setProcessing(true);
        setError('');
        
        try {
            const response = await fetch('/api/v1/courses/teacher-choice/accept/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                },
                body: JSON.stringify({
                    request_id: discountRequest.id,
                    choice: choice // 'accept' or 'decline'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Notify parent component
                if (onChoice) {
                    onChoice({
                        choice,
                        data,
                        discountRequest
                    });
                }
                handleClose();
            } else {
                setError(data.error || 'Failed to submit choice');
            }
            
        } catch (error) {
            console.error('Choice submission failed:', error);
            setError('Network error. Please try again.');
        } finally {
            setProcessing(false);
        }
    };

    if (!discountRequest) return null;

    const {
        student,
        course,
        discount_percent,
        teo_amount,
        course_price,
        teacher_earnings_if_accepted,
        teacher_earnings_if_declined,
        expires_at
    } = discountRequest;

    // Calculate earnings comparison
    const fiatDifference = teacher_earnings_if_declined?.fiat - teacher_earnings_if_accepted?.fiat;
    const teoGained = teacher_earnings_if_accepted?.teo || 0;

    return (
        <Modal show={show} onHide={handleClose} size="lg" centered>
            <Modal.Header closeButton>
                <Modal.Title>
                    <i className="fas fa-handshake me-2"></i>
                    Student Discount Request
                </Modal.Title>
            </Modal.Header>
            
            <Modal.Body>
                {error && (
                    <Alert variant="danger">
                        <i className="fas fa-exclamation-triangle me-2"></i>
                        {error}
                    </Alert>
                )}

                {/* Request Details */}
                <div className="mb-4">
                    <h5>Request Details</h5>
                    <div className="bg-light p-3 rounded">
                        <div className="row">
                            <div className="col-md-6">
                                <strong>Student:</strong> {student?.email || 'Unknown'}<br/>
                                <strong>Course:</strong> {course?.title || 'Unknown Course'}<br/>
                                <strong>Course Price:</strong> €{course_price}
                            </div>
                            <div className="col-md-6">
                                <strong>Discount Requested:</strong> 
                                <Badge bg="primary" className="ms-2">{discount_percent}%</Badge><br/>
                                <strong>TEO Cost:</strong> {teo_amount} TEO<br/>
                                <strong>Expires:</strong> {new Date(expires_at).toLocaleString()}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Choice Options */}
                <div className="mb-4">
                    <h5>Your Options</h5>
                    
                    {/* Accept TeoCoin Option */}
                    <div className="border rounded p-3 mb-3" style={{borderColor: '#28a745'}}>
                        <div className="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 className="text-success mb-1">
                                    <i className="fab fa-bitcoin me-2"></i>
                                    Accept TeoCoin Payment
                                </h6>
                                <p className="mb-2">
                                    Student gets {discount_percent}% discount, you receive TEO tokens
                                </p>
                                <div className="small text-muted">
                                    <strong>You receive:</strong><br/>
                                    • €{teacher_earnings_if_accepted?.fiat} (fiat)<br/>
                                    • {teacher_earnings_if_accepted?.teo} TEO tokens<br/>
                                    • Total TEO: {teacher_earnings_if_accepted?.total_teo} TEO
                                </div>
                            </div>
                            <Button 
                                variant="success" 
                                onClick={() => handleChoice('accept')}
                                disabled={processing}
                                className="ms-3"
                            >
                                {processing ? (
                                    <Spinner size="sm" className="me-2" />
                                ) : (
                                    <i className="fas fa-check me-2"></i>
                                )}
                                Accept TEO
                            </Button>
                        </div>
                    </div>

                    {/* Decline / Full Fiat Option */}
                    <div className="border rounded p-3" style={{borderColor: '#007bff'}}>
                        <div className="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 className="text-primary mb-1">
                                    <i className="fas fa-euro-sign me-2"></i>
                                    Take Full Fiat Payment
                                </h6>
                                <p className="mb-2">
                                    Student pays full price, you receive full EUR payment
                                </p>
                                <div className="small text-muted">
                                    <strong>You receive:</strong><br/>
                                    • €{teacher_earnings_if_declined?.fiat} (fiat)<br/>
                                    • 0 TEO tokens
                                </div>
                            </div>
                            <Button 
                                variant="primary" 
                                onClick={() => handleChoice('decline')}
                                disabled={processing}
                                className="ms-3"
                            >
                                {processing ? (
                                    <Spinner size="sm" className="me-2" />
                                ) : (
                                    <i className="fas fa-money-bill me-2"></i>
                                )}
                                Take Fiat
                            </Button>
                        </div>
                    </div>
                </div>

                {/* Earnings Comparison */}
                <div className="mb-4">
                    <h6>Earnings Comparison</h6>
                    <div className="bg-info bg-opacity-10 p-3 rounded">
                        <div className="row text-center">
                            <div className="col-md-4">
                                <strong>Fiat Difference</strong><br/>
                                <span className="text-danger">
                                    -€{fiatDifference?.toFixed(2) || 0}
                                </span><br/>
                                <small className="text-muted">Less EUR if you accept TEO</small>
                            </div>
                            <div className="col-md-4">
                                <strong>TEO Gained</strong><br/>
                                <span className="text-success">
                                    +{teoGained} TEO
                                </span><br/>
                                <small className="text-muted">TEO tokens if you accept</small>
                            </div>
                            <div className="col-md-4">
                                <strong>Recommendation</strong><br/>
                                <Badge bg={teoGained > fiatDifference * 2 ? 'success' : 'warning'}>
                                    {teoGained > fiatDifference * 2 ? 'Accept TEO' : 'Consider carefully'}
                                </Badge><br/>
                                <small className="text-muted">Based on TEO/EUR ratio</small>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Additional Info */}
                <div className="small text-muted">
                    <i className="fas fa-info-circle me-1"></i>
                    <strong>Note:</strong> TEO tokens can be staked to reduce your platform commission rate 
                    and can be used for future transactions or held as investment.
                </div>
            </Modal.Body>
            
            <Modal.Footer>
                <Button variant="secondary" onClick={handleClose} disabled={processing}>
                    Cancel
                </Button>
                <div className="ms-auto small text-muted">
                    Decision expires: {new Date(expires_at).toLocaleString()}
                </div>
            </Modal.Footer>
        </Modal>
    );
};

export default TeacherDiscountChoiceModal;

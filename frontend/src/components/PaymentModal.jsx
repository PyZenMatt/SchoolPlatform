/**
 * PaymentModal.jsx - Fiat Payment Integration Component
 * Handles Stripe payment flow for course purchases
 */

import React, { useState, useEffect } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import {
    Elements,
    CardElement,
    useStripe,
    useElements
} from '@stripe/react-stripe-js';
import './PaymentModal.css';

// Initialize Stripe (you'll need to set your publishable key)
const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || 'pk_test_...');

const PaymentForm = ({ course, onSuccess, onClose, onError }) => {
    const stripe = useStripe();
    const elements = useElements();
    const [processing, setProcessing] = useState(false);
    const [paymentMethod, setPaymentMethod] = useState('fiat');
    const [paymentSummary, setPaymentSummary] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchPaymentSummary();
    }, [course.id]);

    const fetchPaymentSummary = async () => {
        try {
            const response = await fetch(`/api/courses/payment/summary/${course.id}/`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();
            if (data.success) {
                setPaymentSummary(data.data);
            } else {
                onError(data.error || 'Failed to load payment options');
            }
        } catch (error) {
            onError('Failed to load payment options');
        } finally {
            setLoading(false);
        }
    };

    const handleFiatPayment = async () => {
        if (!stripe || !elements) {
            onError('Stripe not loaded');
            return;
        }

        setProcessing(true);

        try {
            // Create payment intent
            const intentResponse = await fetch('/api/courses/payment/create-intent/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    course_id: course.id,
                    amount_eur: course.price_eur
                }),
            });

            const intentData = await intentResponse.json();
            
            if (!intentData.success) {
                throw new Error(intentData.error || 'Failed to create payment intent');
            }

            // Confirm payment with Stripe
            const cardElement = elements.getElement(CardElement);
            const { error, paymentIntent } = await stripe.confirmCardPayment(
                intentData.client_secret,
                {
                    payment_method: {
                        card: cardElement,
                        billing_details: {
                            name: 'Student', // You can get this from user context
                        },
                    },
                }
            );

            if (error) {
                throw new Error(error.message);
            }

            if (paymentIntent.status === 'succeeded') {
                // Confirm with backend
                const confirmResponse = await fetch('/api/courses/payment/confirm/', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        payment_intent_id: paymentIntent.id,
                        course_id: course.id
                    }),
                });

                const confirmData = await confirmResponse.json();
                
                if (confirmData.success) {
                    onSuccess({
                        method: 'fiat',
                        amount: intentData.amount,
                        teocoingReward: confirmData.teocoin_reward,
                        enrollment: confirmData.enrollment
                    });
                } else {
                    throw new Error(confirmData.error || 'Payment confirmation failed');
                }
            }

        } catch (error) {
            onError(error.message);
        } finally {
            setProcessing(false);
        }
    };

    const handleTeoCoinPayment = async () => {
        setProcessing(true);
        
        try {
            // This would call your existing TeoCoin payment API
            const response = await fetch('/api/courses/purchase/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    course_id: course.id,
                    payment_method: 'teocoin'
                }),
            });

            const data = await response.json();
            
            if (data.success) {
                onSuccess({
                    method: 'teocoin',
                    amount: course.teocoin_price,
                    enrollment: data.enrollment
                });
            } else {
                throw new Error(data.error || 'TeoCoin payment failed');
            }

        } catch (error) {
            onError(error.message);
        } finally {
            setProcessing(false);
        }
    };

    if (loading) {
        return (
            <div className="payment-modal-overlay">
                <div className="payment-modal">
                    <div className="loading">Loading payment options...</div>
                </div>
            </div>
        );
    }

    if (paymentSummary?.already_enrolled) {
        return (
            <div className="payment-modal-overlay">
                <div className="payment-modal">
                    <div className="already-enrolled">
                        <h3>✅ Already Enrolled</h3>
                        <p>You are already enrolled in this course!</p>
                        <button onClick={onClose} className="btn-primary">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    const pricingOptions = paymentSummary?.pricing_options || [];

    return (
        <div className="payment-modal-overlay">
            <div className="payment-modal">
                <div className="payment-header">
                    <h3>💳 Choose Payment Method</h3>
                    <button onClick={onClose} className="close-btn">×</button>
                </div>

                <div className="course-info">
                    <h4>{course.title}</h4>
                    <p>Complete this course and earn crypto rewards!</p>
                </div>

                <div className="payment-options">
                    {pricingOptions.map((option) => (
                        <div
                            key={option.method}
                            className={`payment-option ${paymentMethod === option.method ? 'selected' : ''}`}
                            onClick={() => setPaymentMethod(option.method)}
                        >
                            <div className="option-header">
                                <input
                                    type="radio"
                                    name="payment"
                                    checked={paymentMethod === option.method}
                                    onChange={() => setPaymentMethod(option.method)}
                                />
                                <div className="option-info">
                                    <div className="price">
                                        {option.price} {option.currency}
                                    </div>
                                    <div className="description">
                                        {option.description}
                                    </div>
                                </div>
                            </div>
                            
                            {option.discount && (
                                <div className="discount-badge">
                                    {option.discount}% OFF
                                </div>
                            )}
                            
                            {option.method === 'fiat' && (
                                <div className="fiat-benefits">
                                    <div className="benefit">💳 Pay with credit/debit card</div>
                                    <div className="benefit">🪙 Earn {option.reward} TEO rewards</div>
                                    <div className="benefit">⚡ Instant access</div>
                                </div>
                            )}
                            
                            {option.method === 'teocoin' && (
                                <div className="teocoin-benefits">
                                    <div className="benefit">🪙 Pay with TeoCoin</div>
                                    <div className="benefit">💰 Save {option.discount}%</div>
                                    <div className="balance">
                                        Balance: {paymentSummary?.user_teocoin_balance || 0} TEO
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                {paymentMethod === 'fiat' && (
                    <div className="stripe-form">
                        <h4>💳 Card Details</h4>
                        <div className="card-element-container">
                            <CardElement
                                options={{
                                    style: {
                                        base: {
                                            fontSize: '16px',
                                            color: '#424770',
                                            '::placeholder': {
                                                color: '#aab7c4',
                                            },
                                        },
                                    },
                                }}
                            />
                        </div>
                    </div>
                )}

                <div className="payment-actions">
                    {paymentMethod === 'fiat' && (
                        <button
                            onClick={handleFiatPayment}
                            disabled={processing || !stripe}
                            className="btn-primary"
                        >
                            {processing ? '⏳ Processing...' : '💳 Pay with Card'}
                        </button>
                    )}

                    {paymentMethod === 'teocoin' && (
                        <button
                            onClick={handleTeoCoinPayment}
                            disabled={processing || !paymentSummary?.can_pay_with_teocoin}
                            className="btn-crypto"
                        >
                            {processing ? '⏳ Processing...' : '🪙 Pay with TeoCoin'}
                        </button>
                    )}

                    <button onClick={onClose} className="btn-secondary">
                        Cancel
                    </button>
                </div>

                {!paymentSummary?.wallet_connected && paymentMethod === 'teocoin' && (
                    <div className="wallet-warning">
                        ⚠️ Connect your wallet to pay with TeoCoin
                    </div>
                )}
            </div>
        </div>
    );
};

const PaymentModal = ({ course, onSuccess, onClose, onError }) => {
    return (
        <Elements stripe={stripePromise}>
            <PaymentForm
                course={course}
                onSuccess={onSuccess}
                onClose={onClose}
                onError={onError}
            />
        </Elements>
    );
};

export default PaymentModal;

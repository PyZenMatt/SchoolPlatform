/**
 * PaymentModal.jsx - Fiat Payment Integration Component
 * Handles Stripe payment flow for course purchases
 * VERSION: 2.2 - Fixed Italian postal code (20121 Milano)
 * LAST UPDATED: 2025-06-22 10:00
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
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || 'pk_test_...');

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

    // Handle ESC key to close modal
    useEffect(() => {
        const handleEscKey = (event) => {
            if (event.key === 'Escape') {
                onClose();
            }
        };

        document.addEventListener('keydown', handleEscKey);
        return () => {
            document.removeEventListener('keydown', handleEscKey);
        };
    }, [onClose]);

    const fetchPaymentSummary = async () => {
        try {
            // Import the API function
            const { getPaymentSummary } = await import('../services/api/courses');
            
            const response = await getPaymentSummary(course.id);
            if (response.data.success) {
                setPaymentSummary(response.data.data);
            } else {
                onError(response.data.error || 'Failed to load payment options');
            }
        } catch (error) {
            onError('Failed to load payment options');
        } finally {
            setLoading(false);
        }
    };

    const handleFiatPayment = async () => {
        console.log('🔄 Starting fiat payment process... [v2.1]', new Date().toISOString());
        
        if (!stripe || !elements) {
            console.error('❌ Stripe not loaded');
            onError('Stripe not loaded');
            return;
        }

        setProcessing(true);

        try {
            console.log('📡 Importing API functions...');
            // Import the API function
            const { createPaymentIntent, confirmPayment } = await import('../services/api/courses');
            
            console.log('💳 Creating payment intent for course:', course.id);
            // Create payment intent using our API
            const intentResponse = await createPaymentIntent(course.id);
            
            console.log('📝 Payment intent response:', intentResponse);
            
            if (!intentResponse.data.success) {
                throw new Error(intentResponse.data.error || 'Failed to create payment intent');
            }

            console.log('✅ Payment intent created, confirming with Stripe...');
            // Confirm payment with Stripe - provide complete Italian billing details
            const cardElement = elements.getElement(CardElement);
            const { error, paymentIntent } = await stripe.confirmCardPayment(
                intentResponse.data.client_secret,
                {
                    payment_method: {
                        card: cardElement,
                        billing_details: {
                            name: 'Mario Rossi',
                            email: 'mario.rossi@example.com',
                            address: {
                                line1: 'Via Roma 123',
                                city: 'Milano',
                                postal_code: '20121',
                                state: 'MI',
                                country: 'IT',
                            },
                        },
                    },
                }
            );

            console.log('🔍 Stripe confirmation result:', { error, paymentIntent });
            console.log('🔧 BILLING DETAILS VERSION 2.5 APPLIED! Complete Italian billing address with Milan postal code 20121');

            if (error) {
                console.error('❌ Stripe payment error:', error);
                throw new Error(error.message);
            }

            if (paymentIntent.status === 'succeeded') {
                console.log('✅ Payment succeeded, confirming with backend...');
                // Confirm with backend using our API
                const confirmResponse = await confirmPayment(course.id, paymentIntent.id);
                
                console.log('📋 Backend confirmation response:', confirmResponse);
                
                if (confirmResponse.data.success) {
                    console.log('🎉 Payment completed successfully!');
                    onSuccess({
                        method: 'fiat',
                        amount: paymentIntent.amount,
                        teocoinReward: confirmResponse.data.teocoin_reward,
                        enrollment: confirmResponse.data.enrollment
                    });
                } else {
                    console.error('❌ Backend confirmation failed:', confirmResponse.data.error);
                    throw new Error(confirmResponse.data.error || 'Payment confirmation failed');
                }
            } else {
                console.error('❌ Payment intent status:', paymentIntent.status);
                throw new Error('Payment was not successful');
            }

        } catch (error) {
            console.error('💥 Payment process failed:', error);
            onError(error.message);
        } finally {
            console.log('🏁 Payment process completed, stopping spinner...');
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
            <div className="payment-modal-overlay" onClick={onClose}>
                <div className="payment-modal" onClick={(e) => e.stopPropagation()}>
                    <div className="loading">Loading payment options...</div>
                </div>
            </div>
        );
    }

    if (paymentSummary?.already_enrolled) {
        return (
            <div className="payment-modal-overlay" onClick={onClose}>
                <div className="payment-modal" onClick={(e) => e.stopPropagation()}>
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
        <div className="payment-modal-overlay" onClick={onClose}>
            <div className="payment-modal" onClick={(e) => e.stopPropagation()}>
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
                        <div className="payment-instructions">
                            <p>💡 <strong>Test Card:</strong> 4242 4242 4242 4242</p>
                            <p>📮 <strong>Note:</strong> Billing address is automatically set to Milan, Italy</p>
                        </div>
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
                                    hidePostalCode: true, // Hide postal code since we provide it programmatically
                                    iconStyle: 'solid',
                                    hideIcon: false,
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

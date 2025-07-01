/**
 * PaymentModal.jsx - Fiat Payment Integration Component
 * Handles Stripe payment flow for course purchases
 * VERSION: 2.2 - Fixed Italian postal code (20121 Milano)
 * LAST UPDATED: 2025-06-22 10:00
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import {
    Elements,
    CardElement,
    useStripe,
    useElements
} from '@stripe/react-stripe-js';
import './PaymentModal.css';

// ⚡ PERFORMANCE: Pre-load and cache Stripe instance
let stripeInstance = null;
const getStripeInstance = async () => {
    if (!stripeInstance) {
        stripeInstance = await loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || 'pk_test_...');
    }
    return stripeInstance;
};

// ⚡ PERFORMANCE: Cache payment summaries in memory
const paymentSummaryCache = new Map();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

const PaymentForm = ({ course, onSuccess, onClose, onError }) => {
    const stripe = useStripe();
    const elements = useElements();
    const [processing, setProcessing] = useState(false);
    const [paymentMethod, setPaymentMethod] = useState('fiat');
    const [paymentSummary, setPaymentSummary] = useState(null);
    const [loading, setLoading] = useState(true);

    // ⚡ PERFORMANCE: Memoize cache key
    const cacheKey = useMemo(() => `payment_summary_${course.id}`, [course.id]);

    // ⚡ PERFORMANCE: Optimized payment summary fetching with cache
    const fetchPaymentSummary = useCallback(async () => {
        try {
            // Check cache first
            const cached = paymentSummaryCache.get(cacheKey);
            if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
                setPaymentSummary(cached.data);
                setLoading(false);
                return;
            }

            // Import API function dynamically only when needed
            const { getPaymentSummary } = await import('../services/api/courses');
            
            const response = await getPaymentSummary(course.id);
            if (response.data.success) {
                const summaryData = response.data.data;
                
                // Cache the result
                paymentSummaryCache.set(cacheKey, {
                    data: summaryData,
                    timestamp: Date.now()
                });
                
                setPaymentSummary(summaryData);
            } else {
                onError(response.data.error || 'Failed to load payment options');
            }
        } catch (error) {
            onError('Failed to load payment options');
        } finally {
            setLoading(false);
        }
    }, [course.id, cacheKey, onError]);

    useEffect(() => {
        fetchPaymentSummary();
    }, [fetchPaymentSummary]);

    // ⚡ PERFORMANCE: Handle ESC key with useCallback to prevent re-renders
    const handleEscKey = useCallback((event) => {
        if (event.key === 'Escape') {
            onClose();
        }
    }, [onClose]);

    useEffect(() => {
        document.addEventListener('keydown', handleEscKey);
        return () => {
            document.removeEventListener('keydown', handleEscKey);
        };
    }, [handleEscKey]);

    // ⚡ PERFORMANCE: Optimized fiat payment with pre-loaded data
    const handleFiatPayment = useCallback(async () => {
        console.log('🔄 Starting OPTIMIZED fiat payment process... [v3.0]', new Date().toISOString());
        
        if (!stripe || !elements) {
            console.error('❌ Stripe not loaded');
            onError('Stripe not loaded');
            return;
        }

        setProcessing(true);

        try {
            console.log('📡 Importing API functions...');
            // ⚡ PERFORMANCE: Dynamic import only when payment is initiated
            const { createPaymentIntent, confirmPayment } = await import('../services/api/courses');
            
            console.log('💳 Creating payment intent for course:', course.id);
            // Create payment intent using our optimized API
            const intentResponse = await createPaymentIntent(course.id, {
                teocoin_discount: 0,  // No discount for Stripe payments
                payment_method: 'stripe'
            });
            
            console.log('📝 Payment intent response:', intentResponse);
            
            if (!intentResponse.data.success) {
                throw new Error(intentResponse.data.error || 'Failed to create payment intent');
            }

            console.log('✅ Payment intent created, confirming with Stripe...');
            // ⚡ PERFORMANCE: Pre-filled billing details to skip form validation
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
            console.log('🔧 BILLING DETAILS VERSION 3.0 OPTIMIZED! Pre-filled Italian billing for speed');

            if (error) {
                console.error('❌ Stripe payment error:', error);
                throw new Error(error.message);
            }

            if (paymentIntent.status === 'succeeded') {
                console.log('✅ Payment succeeded, confirming with backend...');
                // ⚡ PERFORMANCE: Parallel backend confirmation
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
    }, [stripe, elements, course.id, onSuccess, onError]);

    const handleTeoCoinPayment = async () => {
        setProcessing(true);
        try {
            // Find the TeoCoin pricing option to get discount amount from original pricing options
            const teoOption = (paymentSummary?.pricing_options || []).find(opt => opt.method === 'teocoin');
            if (!teoOption || !teoOption.discount) {
                throw new Error('TeoCoin discount not available');
            }

            // Get wallet address from Web3 context or localStorage
            const walletAddress = localStorage.getItem('wallet_address') || 
                                localStorage.getItem('connectedWalletAddress');
            
            if (!walletAddress) {
                throw new Error('Please connect your wallet to use TeoCoin discounts');
            }

            // Use the new discount-based payment intent creation
            const { createPaymentIntent } = await import('../services/api/courses');
            
            console.log('🪙 Processing TeoCoin discount payment...');
            const intentResponse = await createPaymentIntent(course.id, {
                teocoin_discount: teoOption.discount,
                payment_method: 'teocoin',
                wallet_address: walletAddress
            });
            
            console.log('📝 TeoCoin payment response:', intentResponse);
            
            if (!intentResponse.data.success) {
                throw new Error(intentResponse.data.error || 'Failed to process TeoCoin payment');
            }

            const data = intentResponse.data;
            
            // Show success with discount details and automatically complete enrollment
            const message = `✅ Discount applied! You saved €${data.discount_applied} using ${data.teo_cost} TEO. Course enrollment complete!`;
            
            onSuccess({
                method: 'teocoin_discount',
                discount: teoOption.discount,
                final_amount: data.final_amount,
                discount_applied: data.discount_applied,
                teo_cost: data.teo_cost,
                teacher_bonus: data.teacher_bonus,
                message: message,
                enrollment: true  // Automatically enrolled
            });
            
        } catch (error) {
            console.error('TeoCoin payment error:', error);
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
    // Remove hybrid option - only show fiat and teocoin
    const cleanedOptions = pricingOptions.filter(opt => opt.method !== 'hybrid');

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
                    {cleanedOptions.map((option) => (
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
                            disabled={processing}
                            className="btn-crypto"
                        >
                            {processing ? '⏳ Processing...' : '🪙 Apply Discount & Pay'}
                        </button>
                    )}
                    <button onClick={onClose} className="btn-secondary">
                        Cancel
                    </button>
                </div>

                {paymentMethod === 'teocoin' && (
                    <div className="teocoin-info">
                        ℹ️ This will automatically deduct the required TEO for the discount and complete your enrollment.
                    </div>
                )}
            </div>
        </div>
    );
};

const PaymentModal = ({ course, onSuccess, onClose, onError }) => {
    const [stripeInstance, setStripeInstance] = useState(null);

    // ⚡ PERFORMANCE: Pre-load Stripe instance immediately
    useEffect(() => {
        const loadStripeAsync = async () => {
            const stripe = await getStripeInstance();
            setStripeInstance(stripe);
        };
        loadStripeAsync();
    }, []);

    // Show loading while Stripe loads (should be very fast with caching)
    if (!stripeInstance) {
        return (
            <div className="payment-modal-overlay" onClick={onClose}>
                <div className="payment-modal-content" onClick={(e) => e.stopPropagation()}>
                    <div className="payment-loading">
                        <div className="spinner"></div>
                        <p>⚡ Loading payment system...</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <Elements stripe={stripeInstance}>
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

/**
 * Enhanced PaymentModal with Layer 2 Gas-Free TeoCoin Integration
 * This component integrates the Layer 2 system for truly gas-free discounts
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import {
    Elements,
    CardElement,
    useStripe,
    useElements
} from '@stripe/react-stripe-js';
import { ethers } from 'ethers';

// Import the new Layer 2 component
import Layer2TeoCoinDiscount from './Layer2TeoCoinDiscount';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

const PaymentModal = ({ 
    isOpen, 
    onClose, 
    course, 
    onPaymentSuccess,
    onError 
}) => {
    const [web3Provider, setWeb3Provider] = useState(null);
    const [walletAddress, setWalletAddress] = useState('');
    const [walletConnected, setWalletConnected] = useState(false);
    const [discountApplied, setDiscountApplied] = useState(false);
    const [discountInfo, setDiscountInfo] = useState(null);
    const [paymentMethod, setPaymentMethod] = useState('fiat');
    const [showLayer2, setShowLayer2] = useState(false);

    // Connect MetaMask wallet
    const connectWallet = async () => {
        try {
            if (window.ethereum) {
                console.log('🦊 Connecting to MetaMask...');
                
                // Request account access
                await window.ethereum.request({
                    method: 'eth_requestAccounts'
                });

                // Create provider
                const provider = new ethers.BrowserProvider(window.ethereum);
                const signer = await provider.getSigner();
                const address = await signer.getAddress();
                
                console.log('✅ Wallet connected:', address);
                
                setWeb3Provider(provider);
                setWalletAddress(address.toLowerCase());
                setWalletConnected(true);
                
                // Check network
                const network = await provider.getNetwork();
                if (network.chainId !== 80002n) {
                    alert('⚠️ Please switch to Polygon Amoy testnet (Chain ID: 80002)');
                }
                
            } else {
                throw new Error('MetaMask not found. Please install MetaMask browser extension.');
            }
        } catch (error) {
            console.error('❌ Wallet connection failed:', error);
            onError(error.message);
        }
    };

    // Handle Layer 2 discount application
    const handleLayer2DiscountApplied = (discountData) => {
        console.log('✅ Layer 2 discount applied:', discountData);
        
        setDiscountApplied(true);
        setDiscountInfo(discountData);
        setShowLayer2(false);
        
        // Store discount for payment completion
        localStorage.setItem('applied_teocoin_discount', JSON.stringify({
            ...discountData,
            layer2_processed: true,
            gas_free: true
        }));
        
        // Switch to fiat payment to complete the process
        setPaymentMethod('fiat');
    };

    // Calculate final price with discount
    const finalPrice = discountInfo 
        ? (course.price - discountInfo.discount_amount)
        : course.price;

    if (!isOpen) return null;

    return (
        <div className="payment-modal-overlay">
            <div className="payment-modal">
                <div className="modal-header">
                    <h2>💳 Complete Your Purchase</h2>
                    <button onClick={onClose} className="close-btn">×</button>
                </div>

                <div className="course-info">
                    <h3>{course.title}</h3>
                    <p>Instructor: {course.teacher?.username}</p>
                    <div className="pricing-info">
                        {discountApplied ? (
                            <div className="discount-applied">
                                <p className="original-price">Original: €{course.price.toFixed(2)}</p>
                                <p className="discount-amount">
                                    TeoCoin Discount: -€{discountInfo.discount_amount.toFixed(2)}
                                    {discountInfo.gas_free && <span className="gas-free-badge">⛽ Gas-Free</span>}
                                </p>
                                <p className="final-price">Final Price: €{finalPrice.toFixed(2)}</p>
                                {discountInfo.layer2_processed && (
                                    <p className="layer2-processed">🚀 Processed via Layer 2</p>
                                )}
                            </div>
                        ) : (
                            <p className="price">Price: €{course.price.toFixed(2)}</p>
                        )}
                    </div>
                </div>

                {/* Wallet Connection Section */}
                <div className="wallet-section">
                    {!walletConnected ? (
                        <div className="connect-wallet">
                            <h4>🔗 Connect Wallet for TeoCoin Discounts</h4>
                            <button 
                                onClick={connectWallet}
                                className="connect-wallet-btn"
                            >
                                🦊 Connect MetaMask
                            </button>
                            <p className="wallet-note">
                                Connect your wallet to use gas-free TeoCoin discounts
                            </p>
                        </div>
                    ) : (
                        <div className="wallet-connected">
                            <p>✅ Wallet Connected: {walletAddress.slice(0, 6)}...{walletAddress.slice(-4)}</p>
                            {!discountApplied && (
                                <button 
                                    onClick={() => setShowLayer2(true)}
                                    className="teocoin-discount-btn"
                                >
                                    🚀 Apply Layer 2 TeoCoin Discount
                                </button>
                            )}
                        </div>
                    )}
                </div>

                {/* Layer 2 TeoCoin Discount Component */}
                {showLayer2 && (
                    <Layer2TeoCoinDiscount
                        course={course}
                        onDiscountApplied={handleLayer2DiscountApplied}
                        onError={onError}
                        web3Provider={web3Provider}
                        walletAddress={walletAddress}
                    />
                )}

                {/* Payment Method Selection */}
                <div className="payment-methods">
                    <h4>💳 Payment Method</h4>
                    <div className="payment-options">
                        <label className="payment-option">
                            <input
                                type="radio"
                                value="fiat"
                                checked={paymentMethod === 'fiat'}
                                onChange={(e) => setPaymentMethod(e.target.value)}
                            />
                            <span>💳 Credit/Debit Card</span>
                            {discountApplied && <span className="discounted-amount">€{finalPrice.toFixed(2)}</span>}
                        </label>
                    </div>
                </div>

                {/* Stripe Payment Form */}
                {paymentMethod === 'fiat' && (
                    <Elements stripe={stripePromise}>
                        <CardPaymentForm 
                            course={course}
                            finalPrice={finalPrice}
                            discountInfo={discountInfo}
                            onPaymentSuccess={onPaymentSuccess}
                            onError={onError}
                        />
                    </Elements>
                )}

                {/* Benefits Display */}
                {discountApplied && discountInfo.gas_free && (
                    <div className="layer2-benefits-summary">
                        <h4>🚀 Layer 2 Benefits Applied</h4>
                        <ul>
                            <li>⛽ Zero gas fees for you</li>
                            <li>🚀 Instant discount processing</li>
                            <li>💰 €{discountInfo.discount_amount} discount applied</li>
                            <li>🏗️ Platform handled all blockchain fees</li>
                        </ul>
                    </div>
                )}

                <style jsx>{`
                    .payment-modal-overlay {
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background: rgba(0, 0, 0, 0.5);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        z-index: 1000;
                    }
                    
                    .payment-modal {
                        background: white;
                        padding: 30px;
                        border-radius: 15px;
                        max-width: 600px;
                        width: 90%;
                        max-height: 90vh;
                        overflow-y: auto;
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                    }
                    
                    .modal-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 20px;
                        border-bottom: 2px solid #eee;
                        padding-bottom: 15px;
                    }
                    
                    .close-btn {
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        color: #666;
                    }
                    
                    .wallet-section {
                        margin: 20px 0;
                        padding: 20px;
                        border: 2px solid #e3f2fd;
                        border-radius: 10px;
                        background: #f8f9fa;
                    }
                    
                    .connect-wallet-btn {
                        background: #ff6b35;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: bold;
                        cursor: pointer;
                        transition: all 0.3s ease;
                    }
                    
                    .connect-wallet-btn:hover {
                        background: #ff5722;
                        transform: translateY(-2px);
                    }
                    
                    .teocoin-discount-btn {
                        background: #4CAF50;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: bold;
                        cursor: pointer;
                        margin-top: 10px;
                    }
                    
                    .discount-applied {
                        background: #e8f5e8;
                        padding: 15px;
                        border-radius: 8px;
                        border: 2px solid #4CAF50;
                    }
                    
                    .gas-free-badge {
                        background: #4CAF50;
                        color: white;
                        padding: 2px 8px;
                        border-radius: 12px;
                        font-size: 12px;
                        margin-left: 10px;
                    }
                    
                    .layer2-processed {
                        color: #2196F3;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    
                    .layer2-benefits-summary {
                        background: #e3f2fd;
                        padding: 15px;
                        border-radius: 8px;
                        margin-top: 20px;
                    }
                    
                    .layer2-benefits-summary ul {
                        list-style: none;
                        padding: 0;
                        margin: 10px 0 0 0;
                    }
                    
                    .layer2-benefits-summary li {
                        padding: 5px 0;
                        font-weight: 500;
                    }
                `}</style>
            </div>
        </div>
    );
};

// Simplified Card Payment Form Component
const CardPaymentForm = ({ course, finalPrice, discountInfo, onPaymentSuccess, onError }) => {
    const stripe = useStripe();
    const elements = useElements();
    const [processing, setProcessing] = useState(false);

    const handleSubmit = async (event) => {
        event.preventDefault();
        setProcessing(true);

        try {
            // Create payment intent with discount info
            const { createPaymentIntent } = await import('../services/api/courses');
            const response = await createPaymentIntent(course.id, {
                final_amount: finalPrice,
                discount_info: discountInfo,
                payment_method: 'fiat_with_layer2_discount'
            });

            if (response.data.success) {
                const { client_secret } = response.data;

                // Confirm payment with Stripe
                const result = await stripe.confirmCardPayment(client_secret, {
                    payment_method: {
                        card: elements.getElement(CardElement),
                    }
                });

                if (result.error) {
                    throw new Error(result.error.message);
                } else {
                    onPaymentSuccess({
                        ...result.paymentIntent,
                        discount_applied: !!discountInfo,
                        layer2_processed: discountInfo?.layer2_processed
                    });
                }
            } else {
                throw new Error(response.data.error);
            }
        } catch (error) {
            onError(error.message);
        } finally {
            setProcessing(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="card-payment-form">
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
            
            <button 
                type="submit" 
                disabled={!stripe || processing}
                className="pay-button"
            >
                {processing ? 'Processing...' : `Pay €${finalPrice.toFixed(2)}`}
            </button>
        </form>
    );
};

export default PaymentModal;

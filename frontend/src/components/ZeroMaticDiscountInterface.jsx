import React, { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import { 
    getStudentAllowance, 
    createDiscountRequest,
    generateStudentDiscountMessage 
} from '../services/api/gasFreeV2';

/**
 * ZeroMaticDiscountInterface - True Zero-MATIC discount system
 * Students only sign messages, never pay gas fees
 * Platform handles all blockchain complexity
 */
const ZeroMaticDiscountInterface = ({ 
    course, 
    onDiscountApplied, 
    onError,
    web3Provider,
    walletAddress 
}) => {
    const [processing, setProcessing] = useState(false);
    const [studentAllowance, setStudentAllowance] = useState(null);
    const [discountInfo, setDiscountInfo] = useState(null);
    const [success, setSuccess] = useState(null);
    const [error, setError] = useState(null);
    const [loadingAllowance, setLoadingAllowance] = useState(false);

    // Check student's platform allowance (not ERC20 balance!)
    const checkStudentAllowance = async () => {
        if (!walletAddress) return;
        
        setLoadingAllowance(true);
        try {
            const data = await getStudentAllowance(walletAddress);
            
            if (data.success) {
                setStudentAllowance(data.platform_allowance);
                console.log(`✅ Student allowance: ${data.platform_allowance} TEO`);
            } else {
                setError(data.error || "Failed to check allowance");
            }
        } catch (error) {
            console.error('Error checking allowance:', error);
            setError(error.message || "Failed to check allowance");
        } finally {
            setLoadingAllowance(false);
        }
    };

    // Calculate discount information
    const calculateDiscountInfo = (discountPercent = 10) => {
        const coursePrice = course.price * 100; // Convert to cents
        const discountAmount = (coursePrice * discountPercent) / 100;
        const finalPrice = coursePrice - discountAmount;
        const teoRequired = (discountAmount * 10) / 100; // 10 TEO = 1 EUR
        
        return {
            discountPercent,
            discountAmount: discountAmount / 100, // Back to EUR
            finalPrice: finalPrice / 100, // Back to EUR
            teoRequired,
            originalPrice: course.price
        };
    };

    // Process ZERO-MATIC discount (student only signs message)
    const processZeroMaticDiscount = async (discountPercent = 10) => {
        setProcessing(true);
        setError(null);
        setSuccess(null);
        
        try {
            console.log('🚀 Processing ZERO-MATIC discount...');
            console.log(`💰 Course: ${course.title} (€${course.price})`);
            console.log(`🎯 Discount: ${discountPercent}%`);
            console.log(`👛 Student wallet: ${walletAddress}`);
            console.log('⛽ Gas cost for student: 0 MATIC (Platform pays ALL fees)');

            if (!window.ethereum) {
                throw new Error('MetaMask not found. Please install MetaMask.');
            }

            const provider = new ethers.BrowserProvider(window.ethereum);
            const signer = await provider.getSigner();
            
            // Calculate discount details
            const info = calculateDiscountInfo(discountPercent);
            setDiscountInfo(info);
            
            // Check if student has enough allowance
            if (studentAllowance < info.teoRequired) {
                throw new Error(`Insufficient platform allowance. You have ${studentAllowance} TEO, but need ${info.teoRequired} TEO. Please contact support.`);
            }
            
            console.log(`📊 Discount info:`, info);
            
            // Step 1: Create signature message (NO GAS COST)
            console.log('🎫 Creating signature for gas-free discount...');
            
            const nonce = Date.now();
            const messageData = generateStudentDiscountMessage({
                studentAddress: walletAddress,
                teacherAddress: course.teacher?.wallet_address,
                courseId: course.id,
                discountPercent: discountPercent,
                nonce: nonce
            });
            
            // Student signs message (FREE - no gas cost)
            console.log('✍️ Please sign the message in MetaMask (no gas fees)...');
            const signature = await signer.signMessage(messageData);
            console.log('✅ Message signed successfully (cost: 0 MATIC)');
            
            // Step 2: Send to backend (platform handles blockchain transaction)
            console.log('📤 Sending request to platform (platform pays gas)...');
            
            const result = await createDiscountRequest({
                student_address: walletAddress,
                teacher_address: course.teacher?.wallet_address,
                course_id: course.id,
                course_price: course.price * 100,
                discount_percent: discountPercent,
                student_signature: signature,
                nonce: nonce
            });
            
            if (result.success) {
                console.log('🎉 Gas-free discount applied successfully!');
                
                setSuccess({
                    message: 'Discount applied successfully!',
                    discountAmount: `€${info.discountAmount.toFixed(2)}`,
                    finalPrice: `€${info.finalPrice.toFixed(2)}`,
                    teoSpent: `${info.teoRequired} TEO`,
                    requestId: result.request_id,
                    txHash: result.tx_hash,
                    studentGasCost: '0 MATIC (Gas-free!)',
                    platformGasCost: result.platform_gas_cost
                });
                
                // Update student allowance
                const newAllowance = studentAllowance - info.teoRequired;
                setStudentAllowance(newAllowance);
                
                // Callback to parent component
                if (onDiscountApplied) {
                    onDiscountApplied({
                        discountPercent,
                        discountAmount: info.discountAmount,
                        finalPrice: info.finalPrice,
                        requestId: result.request_id
                    });
                }
                
            } else {
                throw new Error(result.error || 'Failed to create discount request');
            }
            
        } catch (error) {
            console.error('❌ Zero-MATIC discount failed:', error);
            setError(error.message);
            if (onError) {
                onError(error.message);
            }
        } finally {
            setProcessing(false);
        }
    };

    // Check allowance on component mount
    useEffect(() => {
        if (walletAddress) {
            checkStudentAllowance();
        }
    }, [walletAddress]);

    // Show loading state
    if (loadingAllowance) {
        return (
            <div className="zero-matic-discount-container">
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Checking your gas-free allowance...</p>
                </div>
            </div>
        );
    }

    // Show error if no allowance data
    if (studentAllowance === null) {
        return (
            <div className="zero-matic-discount-container">
                <div className="error-state">
                    <h3>⚠️ Setup Required</h3>
                    <p>Your account needs to be approved for gas-free discounts.</p>
                    <button 
                        className="btn btn-primary"
                        onClick={checkStudentAllowance}
                    >
                        Check Again
                    </button>
                </div>
            </div>
        );
    }

    const discountOptions = [5, 10, 15];
    const previewInfo = calculateDiscountInfo(10);

    return (
        <div className="zero-matic-discount-container">
            <div className="discount-header">
                <h3>🚀 Zero-MATIC TeoCoin Discount</h3>
                <p className="zero-cost-badge">
                    ⛽ <strong>0 MATIC</strong> gas fees for you!
                </p>
            </div>

            {/* Allowance Status */}
            <div className="allowance-status">
                <div className="allowance-info">
                    <span className="label">Your Platform Allowance:</span>
                    <span className="value">{studentAllowance} TEO</span>
                    <span className={`status ${studentAllowance > 10 ? 'sufficient' : 'low'}`}>
                        {studentAllowance > 10 ? '✅ Sufficient' : '⚠️ Low'}
                    </span>
                </div>
                {studentAllowance <= 10 && (
                    <p className="low-allowance-warning">
                        Low allowance detected. Contact support to increase your allowance.
                    </p>
                )}
            </div>

            {/* Course Info */}
            <div className="course-info">
                <h4>{course.title}</h4>
                <div className="price-info">
                    <span className="original-price">€{course.price}</span>
                    <span className="arrow">→</span>
                    <span className="discounted-price">€{previewInfo.finalPrice}</span>
                    <span className="savings">Save €{previewInfo.discountAmount}</span>
                </div>
            </div>

            {/* Discount Options */}
            <div className="discount-options">
                <h4>Choose Your Discount:</h4>
                <div className="options-grid">
                    {discountOptions.map(percent => {
                        const info = calculateDiscountInfo(percent);
                        const canAfford = studentAllowance >= info.teoRequired;
                        
                        return (
                            <div 
                                key={percent}
                                className={`discount-option ${!canAfford ? 'disabled' : ''}`}
                            >
                                <div className="percent">{percent}%</div>
                                <div className="savings">Save €{info.discountAmount.toFixed(2)}</div>
                                <div className="cost">{info.teoRequired} TEO</div>
                                <button
                                    className="btn btn-primary"
                                    disabled={processing || !canAfford}
                                    onClick={() => processZeroMaticDiscount(percent)}
                                >
                                    {processing ? 'Processing...' : `Apply ${percent}% Discount`}
                                </button>
                                {!canAfford && (
                                    <p className="insufficient-funds">
                                        Need {info.teoRequired} TEO
                                    </p>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* How It Works */}
            <div className="how-it-works">
                <h4>🔧 How Zero-MATIC Works:</h4>
                <div className="steps">
                    <div className="step">
                        <span className="number">1</span>
                        <span className="text">You sign a message (FREE)</span>
                    </div>
                    <div className="step">
                        <span className="number">2</span>
                        <span className="text">Platform pays gas fees (~$0.003)</span>
                    </div>
                    <div className="step">
                        <span className="number">3</span>
                        <span className="text">Instant discount applied!</span>
                    </div>
                </div>
                <p className="zero-complexity">
                    <strong>No MATIC needed. No gas fees. No complexity.</strong>
                </p>
            </div>

            {/* Processing State */}
            {processing && (
                <div className="processing-overlay">
                    <div className="processing-content">
                        <div className="spinner-large"></div>
                        <h3>Processing Gas-Free Discount...</h3>
                        <div className="processing-steps">
                            <div className="step active">✍️ Sign message (FREE)</div>
                            <div className="step active">📤 Platform processing...</div>
                            <div className="step">🎉 Discount applied!</div>
                        </div>
                        <p><strong>You pay 0 MATIC gas fees!</strong></p>
                    </div>
                </div>
            )}

            {/* Success State */}
            {success && (
                <div className="success-state">
                    <div className="success-content">
                        <h3>🎉 Discount Applied Successfully!</h3>
                        <div className="success-details">
                            <div className="detail">
                                <span className="label">Discount:</span>
                                <span className="value">{success.discountAmount}</span>
                            </div>
                            <div className="detail">
                                <span className="label">New Price:</span>
                                <span className="value">{success.finalPrice}</span>
                            </div>
                            <div className="detail">
                                <span className="label">TEO Spent:</span>
                                <span className="value">{success.teoSpent}</span>
                            </div>
                            <div className="detail highlight">
                                <span className="label">Your Gas Cost:</span>
                                <span className="value">{success.studentGasCost}</span>
                            </div>
                        </div>
                        <div className="transaction-info">
                            <p>Request ID: {success.requestId}</p>
                            <a 
                                href={`https://polygonscan.com/tx/${success.txHash}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="tx-link"
                            >
                                View Transaction
                            </a>
                        </div>
                    </div>
                </div>
            )}

            {/* Error State */}
            {error && (
                <div className="error-state">
                    <h3>❌ Error</h3>
                    <p>{error}</p>
                    <button 
                        className="btn btn-secondary"
                        onClick={() => setError(null)}
                    >
                        Try Again
                    </button>
                </div>
            )}
        </div>
    );
};

export default ZeroMaticDiscountInterface;

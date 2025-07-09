import React, { useState, useEffect } from 'react';
import { ethers } from 'ethers';

/**
 * Layer 2 TeoCoin Discount Component - Gas-Free Implementation
 * Uses existing Layer 2 infrastructure to provide truly gas-free discounts
 */
const Layer2TeoCoinDiscount = ({ 
    course, 
    onDiscountApplied, 
    onError,
    web3Provider,
    walletAddress 
}) => {
    const [processing, setProcessing] = useState(false);
    const [teoBalance, setTeoBalance] = useState(null);
    const [discountSimulation, setDiscountSimulation] = useState(null);
    const [balanceLoading, setBalanceLoading] = useState(false);

    // Check student's TEO balance
    const checkTeoBalance = async () => {
        if (!walletAddress) return;
        
        setBalanceLoading(true);
        try {
            const response = await fetch(`/api/v1/services/discount/layer2/balance/?wallet_address=${walletAddress}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
                }
            });
            
            const data = await response.json();
            if (data.success) {
                setTeoBalance(data.data);
            } else {
                console.error('Balance check failed:', data.error);
            }
        } catch (error) {
            console.error('Error checking TEO balance:', error);
        } finally {
            setBalanceLoading(false);
        }
    };

    // Simulate discount to show costs
    const simulateDiscount = async (discountAmount) => {
        try {
            const response = await fetch('/api/v1/services/discount/layer2/simulate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
                },
                body: JSON.stringify({
                    discount_amount: discountAmount
                })
            });
            
            const data = await response.json();
            if (data.success) {
                setDiscountSimulation(data.simulation);
            }
        } catch (error) {
            console.error('Simulation failed:', error);
        }
    };

    // Process gas-free discount via Layer 2
    const processLayer2Discount = async (discountAmount, discountPercent) => {
        setProcessing(true);
        
        try {
            console.log('🚀 Processing Layer 2 gas-free discount...');
            console.log(`💰 Discount: €${discountAmount} (${discountPercent}%)`);
            console.log(`👛 Student wallet: ${walletAddress}`);
            console.log('⛽ Gas cost for student: 0 ETH (Layer 2 covers all fees)');

            // Step 1: Check if platform is approved to spend student's TEO
            const platformAddress = "0xd74fc566c0c5b83f95fd82e6866d8a7a6eaca7a9"; // Layer 2 contract
            const teoCoinAddress = "0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8"; // TEO contract
            
            // Check current allowance
            const contract = new ethers.Contract(teoCoinAddress, [
                "function allowance(address owner, address spender) view returns (uint256)"
            ], web3Provider);
            
            const currentAllowance = await contract.allowance(walletAddress, platformAddress);
            const requiredAmount = ethers.parseEther(discountAmount.toString());
            
            console.log(`Current allowance: ${ethers.formatEther(currentAllowance)} TEO`);
            console.log(`Required amount: ${ethers.formatEther(requiredAmount)} TEO`);
            
            // Step 2: If allowance is insufficient, request approval
            if (currentAllowance < requiredAmount) {
                console.log('🔐 Requesting TEO spending approval...');
                
                const signer = await web3Provider.getSigner();
                const teoContract = new ethers.Contract(teoCoinAddress, [
                    "function approve(address spender, uint256 amount) returns (bool)"
                ], signer);
                
                // Approve a large amount to avoid repeated approvals
                const approvalAmount = ethers.parseEther("1000"); // Approve 1000 TEO
                
                const approveTx = await teoContract.approve(platformAddress, approvalAmount);
                console.log('⏳ Waiting for approval transaction...');
                await approveTx.wait();
                console.log('✅ TEO spending approved!');
            }

            // Step 3: Create Layer 2 discount request
            const response = await fetch('/api/v1/services/discount/layer2/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
                },
                body: JSON.stringify({
                    course_id: course.id,
                    discount_amount: discountAmount,
                    discount_percentage: discountPercent,
                    student_wallet: walletAddress
                })
            });

            const data = await response.json();
            
            if (data.success) {
                console.log('✅ Layer 2 discount processed successfully!');
                console.log('📜 Transaction hash:', data.data.transaction_hash);
                console.log('💸 TEO transferred:', data.data.teo_cost);
                console.log('⛽ Student gas cost:', data.data.student_gas_cost);

                // Show success message
                alert(`✅ Gas-Free TeoCoin Discount Applied!

💰 Discount: €${discountAmount} (${discountPercent}%)
🪙 TEO Cost: ${data.data.teo_cost} TEO
⛽ Your Gas Cost: ${data.data.student_gas_cost}
🏗️ Platform Covers: All gas fees via Layer 2

✨ Your ${discountAmount} TEO has been transferred to the platform!
📜 TX Hash: ${data.data.transaction_hash}

Your discount has been applied and you can now complete payment.`);

                // Apply discount to payment flow
                onDiscountApplied({
                    request_id: data.data.request_id,
                    discount_amount: discountAmount,
                    discount_percentage: discountPercent,
                    teo_cost: data.data.teo_cost,
                    transaction_hash: data.data.transaction_hash,
                    gas_free: true,
                    layer2_processed: true,
                    student_wallet: walletAddress,
                    final_price: parseFloat(course.price_eur) - discountAmount
                });

            } else {
                throw new Error(data.error || 'Layer 2 discount failed');
            }

        } catch (error) {
            console.error('❌ Layer 2 discount failed:', error);
            if (error.message.includes('user rejected')) {
                onError('Transaction cancelled by user');
            } else if (error.message.includes('insufficient')) {
                onError(`Insufficient TEO balance: ${error.message}`);
            } else {
                onError(`Layer 2 discount failed: ${error.message}`);
            }
        } finally {
            setProcessing(false);
        }
    };

    // Load balance and simulation on mount
    useEffect(() => {
        if (walletAddress) {
            checkTeoBalance();
            simulateDiscount(10); // Default 10 EUR discount
        }
    }, [walletAddress]);

    return (
        <div className="layer2-teocoin-discount">
            <div className="discount-header">
                <h3>🚀 Layer 2 Gas-Free TeoCoin Discount</h3>
                <p className="gas-free-badge">⛽ 0 ETH gas cost for students</p>
            </div>

            {/* Balance Display */}
            <div className="balance-section">
                <h4>Your TEO Balance</h4>
                {balanceLoading ? (
                    <p>Loading balance...</p>
                ) : teoBalance ? (
                    <div className="balance-info">
                        <p>💰 Balance: {teoBalance.teo_balance.toFixed(2)} TEO</p>
                        <p className={teoBalance.has_sufficient_balance ? 'sufficient' : 'insufficient'}>
                            {teoBalance.has_sufficient_balance ? '✅ Sufficient for discount' : '❌ Insufficient balance'}
                        </p>
                    </div>
                ) : (
                    <button onClick={checkTeoBalance}>Check Balance</button>
                )}
            </div>

            {/* Discount Simulation */}
            {discountSimulation && (
                <div className="simulation-section">
                    <h4>Discount Preview</h4>
                    <div className="simulation-details">
                        <p>💸 Discount: €{discountSimulation.discount_amount_eur}</p>
                        <p>🪙 TEO Cost: {discountSimulation.teo_cost} TEO</p>
                        <p>⛽ Your Gas: {discountSimulation.gas_cost_student}</p>
                        <p>🏗️ Platform Gas: {discountSimulation.gas_cost_platform}</p>
                        <p>✨ Layer 2: {discountSimulation.layer2_enabled ? '✅ Enabled' : '❌ Disabled'}</p>
                        <p>📝 Approval: {discountSimulation.requires_approval ? '❌ Required' : '✅ Not Required'}</p>
                    </div>
                </div>
            )}

            {/* Discount Action Buttons */}
            <div className="discount-actions">
                {teoBalance?.has_sufficient_balance ? (
                    <div className="discount-options">
                        <button 
                            onClick={() => processLayer2Discount(10, 10)}
                            disabled={processing}
                            className="discount-btn discount-10"
                        >
                            {processing ? 'Processing...' : '💰 €10 Discount (10 TEO)'}
                        </button>
                        
                        <button 
                            onClick={() => processLayer2Discount(20, 20)}
                            disabled={processing || teoBalance.teo_balance < 20}
                            className="discount-btn discount-20"
                        >
                            {processing ? 'Processing...' : '💰 €20 Discount (20 TEO)'}
                        </button>
                    </div>
                ) : (
                    <div className="insufficient-balance">
                        <p>❌ Insufficient TEO balance for discount</p>
                        <p>Need at least 10 TEO for minimum discount</p>
                    </div>
                )}
            </div>

            {/* Layer 2 Benefits */}
            <div className="layer2-benefits">
                <h4>🚀 Layer 2 Benefits</h4>
                <ul>
                    <li>⛽ Zero gas fees for students</li>
                    <li>🚀 Instant transactions</li>
                    <li>📝 No approvals required</li>
                    <li>🏗️ Platform handles all infrastructure</li>
                    <li>✨ Seamless user experience</li>
                </ul>
            </div>

            <style jsx>{`
                .layer2-teocoin-discount {
                    padding: 20px;
                    border: 2px solid #4CAF50;
                    border-radius: 10px;
                    background: linear-gradient(135deg, #f0fff0 0%, #e8f5e8 100%);
                    margin: 20px 0;
                }
                
                .discount-header {
                    text-align: center;
                    margin-bottom: 20px;
                }
                
                .gas-free-badge {
                    background: #4CAF50;
                    color: white;
                    padding: 5px 15px;
                    border-radius: 20px;
                    display: inline-block;
                    margin-top: 10px;
                    font-weight: bold;
                }
                
                .balance-section, .simulation-section {
                    margin: 15px 0;
                    padding: 15px;
                    background: white;
                    border-radius: 8px;
                    border: 1px solid #ddd;
                }
                
                .balance-info .sufficient {
                    color: #4CAF50;
                    font-weight: bold;
                }
                
                .balance-info .insufficient {
                    color: #f44336;
                    font-weight: bold;
                }
                
                .discount-actions {
                    margin: 20px 0;
                }
                
                .discount-options {
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                }
                
                .discount-btn {
                    padding: 15px 25px;
                    font-size: 16px;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }
                
                .discount-10 {
                    background: #4CAF50;
                    color: white;
                }
                
                .discount-20 {
                    background: #2196F3;
                    color: white;
                }
                
                .discount-btn:hover:not(:disabled) {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }
                
                .discount-btn:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                }
                
                .layer2-benefits {
                    margin-top: 20px;
                    padding: 15px;
                    background: #e3f2fd;
                    border-radius: 8px;
                }
                
                .layer2-benefits ul {
                    list-style: none;
                    padding: 0;
                }
                
                .layer2-benefits li {
                    padding: 5px 0;
                    font-weight: 500;
                }
                
                .insufficient-balance {
                    text-align: center;
                    color: #f44336;
                    font-weight: bold;
                }
            `}</style>
        </div>
    );
};

export default Layer2TeoCoinDiscount;

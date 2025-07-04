/**
 * PaymentModal.jsx - Enhanced Payment Integration with MetaMask TeoCoin Support
 * Handles Stripe payment flow + TeoCoin discount with MetaMask Web3 integration
 * VERSION: 3.0 - Added MetaMask integration for TeoCoin transfers
 * LAST UPDATED: 2025-06-22 12:00
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

// Web3 imports for MetaMask integration
import { ethers } from 'ethers';

// TeoCoin contract configuration
const TEOCOIN_CONTRACT_ADDRESS = '0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8'; // From settings
const REWARD_POOL_ADDRESS = '0x3b72a4E942CF1467134510cA3952F01b63005044'; // From settings

// Minimal ERC-20 ABI for TeoCoin operations
const TEOCOIN_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "spender", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "address", "name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
];

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
    const [discountApplied, setDiscountApplied] = useState(false);
    
    // Web3 state for MetaMask integration
    const [web3Provider, setWeb3Provider] = useState(null);
    const [walletConnected, setWalletConnected] = useState(false);
    const [walletAddress, setWalletAddress] = useState('');
    const [teoBalance, setTeoBalance] = useState(0);
    const [teoAllowance, setTeoAllowance] = useState(0);
    const [approvalStatus, setApprovalStatus] = useState('none'); // none, pending, completed, failed

    // Check if TeoCoin discount was applied (clear any stale data first)
    useEffect(() => {
        // Clear any stale discount data when modal opens
        localStorage.removeItem('applied_teocoin_discount');
        setDiscountApplied(false);
        console.log('🧹 Cleared stale discount data on modal open');
    }, []);

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

    // Debug logging for payment summary
    useEffect(() => {
        if (paymentSummary) {
            console.log('🔍 DEBUG Payment Summary:', {
                user_teocoin_balance: paymentSummary.user_teocoin_balance,
                can_pay_with_teocoin: paymentSummary.can_pay_with_teocoin,
                wallet_connected: paymentSummary.wallet_connected,
                pricing_options: paymentSummary.pricing_options,
                already_enrolled: paymentSummary.already_enrolled
            });
        }
    }, [paymentSummary]);

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

    // ====== WEB3 METAMASK INTEGRATION ======
    
    // Switch to Polygon Amoy network
    const switchToPolygonAmoy = async () => {
        try {
            // Try switching to existing network
            await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: '0x13882' }], // 80002 in hex
            });
        } catch (switchError) {
            // If network doesn't exist, add it
            if (switchError.code === 4902) {
                try {
                    await window.ethereum.request({
                        method: 'wallet_addEthereumChain',
                        params: [{
                            chainId: '0x13882',
                            chainName: 'Polygon Amoy Testnet',
                            nativeCurrency: {
                                name: 'MATIC',
                                symbol: 'MATIC',
                                decimals: 18,
                            },
                            rpcUrls: ['https://rpc-amoy.polygon.technology/'],
                            blockExplorerUrls: ['https://amoy.polygonscan.com/'],
                        }],
                    });
                } catch (addError) {
                    throw new Error('Failed to add Polygon Amoy network to MetaMask');
                }
            } else {
                throw switchError;
            }
        }
    };
    
    // Check MetaMask connection on component mount
    useEffect(() => {
        const checkWalletConnection = async () => {
            if (typeof window.ethereum !== 'undefined') {
                try {
                    const provider = new ethers.BrowserProvider(window.ethereum);
                    const accounts = await provider.listAccounts();
                    
                    if (accounts.length > 0) {
                        console.log('🔍 Checking network and RPC connectivity...');
                        
                        // Test network connectivity
                        const network = await provider.getNetwork();
                        console.log('🌐 Connected to network:', network.chainId, network.name);
                        
                        // Test if we can make basic RPC calls
                        const blockNumber = await provider.getBlockNumber();
                        console.log('📦 Latest block:', blockNumber);
                        
                        setWeb3Provider(provider);
                        setWalletConnected(true);
                        setWalletAddress(accounts[0].address);
                        await updateTeoInfo(provider, accounts[0].address);
                        console.log('✅ Wallet already connected:', accounts[0].address);
                    }
                } catch (error) {
                    console.log('❌ MetaMask connection issue:', error.message);
                }
            } else {
                console.log('❌ MetaMask not installed');
            }
        };
        
        checkWalletConnection();
    }, []);

    // Connect to MetaMask wallet
    const connectWallet = async () => {
        try {
            if (typeof window.ethereum === 'undefined') {
                throw new Error('MetaMask is not installed. Please install MetaMask to use TeoCoin payments.');
            }

            const provider = new ethers.BrowserProvider(window.ethereum);
            
            // Check network first
            const network = await provider.getNetwork();
            if (network.chainId !== 80002n) {
                console.log('🔄 Wrong network detected, switching to Polygon Amoy...');
                await switchToPolygonAmoy();
                // Recreate provider after network switch
                const newProvider = new ethers.BrowserProvider(window.ethereum);
                setWeb3Provider(newProvider);
            } else {
                setWeb3Provider(provider);
            }
            
            await provider.send("eth_requestAccounts", []);
            const signer = await provider.getSigner();
            const address = await signer.getAddress();

            setWalletConnected(true);
            setWalletAddress(address);
            
            // Update TEO balance and allowance
            await updateTeoInfo(provider, address);
            
            console.log('✅ Wallet connected:', address);
            console.log('🌐 Network:', await provider.getNetwork());
        } catch (error) {
            console.error('Failed to connect wallet:', error);
            onError(error.message);
        }
    };

    // Update TEO balance and allowance information
    const updateTeoInfo = async (provider, address) => {
        try {
            const contract = new ethers.Contract(TEOCOIN_CONTRACT_ADDRESS, TEOCOIN_ABI, provider);
            
            // Get balance
            const balanceWei = await contract.balanceOf(address);
            const balance = Number(ethers.formatEther(balanceWei));
            
            // Get allowance for reward pool
            const allowanceWei = await contract.allowance(address, REWARD_POOL_ADDRESS);
            const allowance = Number(ethers.formatEther(allowanceWei));
            
            // Check MATIC balance for gas fees
            const maticBalance = await provider.getBalance(address);
            const maticFormatted = Number(ethers.formatEther(maticBalance));
            
            setTeoBalance(balance);
            setTeoAllowance(allowance);
            
            console.log('💰 TEO Balance:', balance);
            console.log('🔑 TEO Allowance:', allowance);
            console.log('⛽ MATIC Balance:', maticFormatted);
            
            // Warn if MATIC is low
            if (maticFormatted < 0.01) {
                console.warn('⚠️ Low MATIC balance - may not be able to pay gas fees');
            }
        } catch (error) {
            console.error('Failed to update TEO info:', error);
        }
    };

    // Approve TeoCoin spending with fallback methods
    const approveTeoCoin = async (amount) => {
        try {
            setApprovalStatus('pending');
            
            const signer = await web3Provider.getSigner();
            const contract = new ethers.Contract(TEOCOIN_CONTRACT_ADDRESS, TEOCOIN_ABI, signer);
            
            // Convert amount to Wei (18 decimals)
            const amountWei = ethers.parseEther(amount.toString());
            
            console.log('🔑 Requesting approval for', amount, 'TEO to', REWARD_POOL_ADDRESS);
            console.log('🔍 Network check - Current chain ID:', await web3Provider.getNetwork());
            
            // Check current network - should be Polygon Amoy (80002)
            const network = await web3Provider.getNetwork();
            if (network.chainId !== 80002n) {
                throw new Error(`Wrong network! Please switch to Polygon Amoy testnet (Chain ID: 80002). Current: ${network.chainId}`);
            }
            
            // Try multiple approval methods to bypass MetaMask RPC issues
            let tx;
            const gasLimit = 60000n;
            
            console.log('🚀 Attempting approval with method 1 (direct call)...');
            
            try {
                // Method 1: Direct contract call (what we've been trying)
                tx = await contract.approve(REWARD_POOL_ADDRESS, amountWei, {
                    gasLimit: gasLimit
                });
                console.log('✅ Method 1 succeeded:', tx.hash);
            } catch (method1Error) {
                console.log('❌ Method 1 failed, trying Method 2 (manual transaction)...');
                
                // Method 2: Manual transaction construction
                try {
                    const nonce = await signer.getNonce();
                    const gasPrice = await web3Provider.getFeeData();
                    
                    // Build transaction manually
                    const txRequest = {
                        to: TEOCOIN_CONTRACT_ADDRESS,
                        data: contract.interface.encodeFunctionData('approve', [REWARD_POOL_ADDRESS, amountWei]),
                        gasLimit: gasLimit,
                        gasPrice: gasPrice.gasPrice,
                        nonce: nonce,
                    };
                    
                    console.log('� Manual transaction:', txRequest);
                    tx = await signer.sendTransaction(txRequest);
                    console.log('✅ Method 2 succeeded:', tx.hash);
                } catch (method2Error) {
                    console.log('❌ Method 2 failed, trying Method 3 (populateTransaction)...');
                    
                    // Method 3: Use populateTransaction
                    try {
                        const populatedTx = await contract.approve.populateTransaction(REWARD_POOL_ADDRESS, amountWei);
                        populatedTx.gasLimit = gasLimit;
                        
                        console.log('📝 Populated transaction:', populatedTx);
                        tx = await signer.sendTransaction(populatedTx);
                        console.log('✅ Method 3 succeeded:', tx.hash);
                    } catch (method3Error) {
                        console.error('❌ All methods failed:');
                        console.error('Method 1:', method1Error.message);
                        console.error('Method 2:', method2Error.message);
                        console.error('Method 3:', method3Error.message);
                        throw new Error('All approval methods failed. This appears to be a MetaMask RPC connectivity issue with Polygon Amoy testnet.');
                    }
                }
            }
            
            console.log('⏳ Waiting for approval confirmation...');
            
            // Wait for confirmation
            const receipt = await tx.wait();
            console.log('✅ Approval confirmed in block:', receipt.blockNumber);
            console.log('💰 Gas used:', receipt.gasUsed.toString());
            
            setApprovalStatus('completed');
            
            // Update allowance
            await updateTeoInfo(web3Provider, walletAddress);
            
        } catch (error) {
            console.error('Approval failed:', error);
            setApprovalStatus('failed');
            
            // Provide more specific error messages
            if (error.message.includes('user rejected')) {
                throw new Error('Transaction was cancelled by user');
            } else if (error.message.includes('insufficient funds')) {
                throw new Error('Insufficient MATIC for gas fees. Please add some MATIC to your wallet.');
            } else if (error.message.includes('Wrong network')) {
                throw error; // Re-throw network error as-is
            } else if (error.message.includes('Internal JSON-RPC error')) {
                throw new Error('Persistent MetaMask RPC issue. Try: 1) Different browser 2) Reset MetaMask 3) Use WalletConnect instead');
            } else if (error.message.includes('All approval methods failed')) {
                throw error; // Re-throw our detailed error
            } else {
                throw new Error(`Approval failed: ${error.message}`);
            }
        }
    };

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
            
            // Check if TeoCoin discount was applied
            const appliedDiscount = localStorage.getItem('applied_teocoin_discount');
            let client_secret, discountInfo = null;
            
            if (appliedDiscount) {
                // Use the discounted payment intent
                discountInfo = JSON.parse(appliedDiscount);
                client_secret = discountInfo.client_secret;
                console.log('💰 Using TeoCoin discounted payment intent:', discountInfo);
            } else {
                // Create new payment intent for full price
                const { createPaymentIntent } = await import('../services/api/courses');
                
                console.log('💳 Creating payment intent for course:', course.id);
                const intentResponse = await createPaymentIntent(course.id, {
                    teocoin_discount: 0,  // No discount for Stripe payments
                    payment_method: 'stripe'
                });
                
                console.log('📝 Payment intent response:', intentResponse);
                
                if (!intentResponse.data.success) {
                    throw new Error(intentResponse.data.error || 'Failed to create payment intent');
                }
                
                client_secret = intentResponse.data.client_secret;
            }

            console.log('✅ Payment intent ready, confirming with Stripe...');
            // ⚡ PERFORMANCE: Pre-filled billing details to skip form validation
            const cardElement = elements.getElement(CardElement);
            const { error, paymentIntent } = await stripe.confirmCardPayment(
                client_secret,
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
                const { confirmPayment } = await import('../services/api/courses');
                const confirmResponse = await confirmPayment(course.id, paymentIntent.id);
                
                console.log('📋 Backend confirmation response:', confirmResponse);
                
                if (confirmResponse.data.success) {
                    console.log('🎉 Payment completed successfully!');
                    
                    // Clear discount info after successful payment
                    if (appliedDiscount) {
                        localStorage.removeItem('applied_teocoin_discount');
                    }
                    
                    onSuccess({
                        method: discountInfo ? 'hybrid' : 'fiat',
                        amount: paymentIntent.amount,
                        teocoinReward: confirmResponse.data.teocoin_reward,
                        teocoinDiscount: discountInfo,
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

    // Unified payment handler that routes to the appropriate payment method
    const handlePayment = async () => {
        if (paymentMethod === 'teocoin') {
            if (!walletConnected) {
                await connectWallet();
                return;
            }
            await handleTeoCoinPayment();
        } else {
            await handleFiatPayment();
        }
    };

    // Enhanced TeoCoin payment flow with complete integration
    const handleTeoCoinPayment = async () => {
        try {
            if (!walletConnected || !web3Provider) {
                throw new Error('Please connect your MetaMask wallet first');
            }

            setProcessing(true);
            
            // Find the TeoCoin pricing option to get discount amount
            const teoOption = (paymentSummary?.pricing_options || []).find(opt => opt.method === 'teocoin');
            if (!teoOption || !teoOption.discount) {
                throw new Error('TeoCoin discount not available');
            }

            // Calculate required TEO amount from payment summary
            const teoRequired = parseFloat(teoOption.price || 0);
            
            console.log('💰 TeoCoin Payment Flow Started');
            console.log('� Required TEO:', teoRequired);
            console.log('💰 Current balance:', teoBalance);
            console.log('🔑 Current allowance:', teoAllowance);

            // Step 1: Check TeoCoin balance
            if (teoBalance < teoRequired) {
                throw new Error(`Insufficient TeoCoin balance. Required: ${teoRequired} TEO, Available: ${teoBalance} TEO`);
            }

            // Step 2: Handle approval if needed
            let approvalTxHash = null;
            if (teoAllowance < teoRequired) {
                console.log('🔑 Approval needed. Requesting approval for', teoRequired, 'TEO');
                approvalTxHash = await handleApproval(teoRequired);
                console.log('✅ Approval completed with tx:', approvalTxHash);
            } else {
                console.log('✅ Sufficient allowance available');
            }

            // Step 3: Execute actual TeoCoin transfer transaction
            console.log('💰 Executing TeoCoin transfer transaction...');
            const transferTxHash = await executeTeoCoinTransfer(teoRequired);
            console.log('✅ Transfer completed with tx:', transferTxHash);

            // Step 4: Create payment intent with transfer hash
            const { createPaymentIntent } = await import('../services/api/courses');
            const response = await createPaymentIntent(course.id, {
                teocoin_discount: teoOption.discount,
                payment_method: 'hybrid',
                wallet_address: walletAddress,
                approval_tx_hash: transferTxHash // Use transfer hash instead of approval hash
            });

            console.log('📝 Payment intent response:', response);

            if (response.data.success) {
                // Step 4: Complete payment flow
                if (response.data.final_amount > 0) {
                    // Hybrid payment - store discount info and switch to card payment
                    const discountInfo = {
                        discount: teoOption.discount,
                        discount_applied: response.data.discount_applied,
                        teo_cost: response.data.teo_cost,
                        final_amount: response.data.final_amount,
                        client_secret: response.data.client_secret,
                        approval_completed: true
                    };
                    
                    localStorage.setItem('applied_teocoin_discount', JSON.stringify(discountInfo));
                    setDiscountApplied(true);
                    setPaymentMethod('fiat');
                    
                    // Show success message
                    const coursePrice = parseFloat(course.price_eur || course.price || 0);
                    alert(`✅ TeoCoin discount applied successfully!
                    
💰 Original price: €${coursePrice.toFixed(2)}
🪙 TEO used: ${discountInfo.teo_cost}  
💸 Discount: €${discountInfo.discount_applied}
💳 Final price: €${discountInfo.final_amount}

Complete your purchase with the discounted amount.`);
                } else {
                    // Full TeoCoin payment completed
                    onSuccess({
                        method: 'teocoin',
                        amount: 0,
                        teocoinDiscount: response.data,
                        enrollment: response.data.enrollment
                    });
                }
            } else {
                throw new Error(response.data.error || 'TeoCoin payment failed');
            }
            
        } catch (error) {
            console.error('TeoCoin payment failed:', error);
            onError(error.message);
            setApprovalStatus('failed');
        } finally {
            setProcessing(false);
        }
    };

    // Enhanced approval handling with transaction hash return
    const handleApproval = async (amount) => {
        try {
            setApprovalStatus('pending');
            
            const signer = await web3Provider.getSigner();
            const contract = new ethers.Contract(TEOCOIN_CONTRACT_ADDRESS, TEOCOIN_ABI, signer);
            
            // Convert amount to Wei (18 decimals)
            const amountWei = ethers.parseEther(amount.toString());
            
            console.log('🔑 Requesting approval for', amount, 'TEO to', REWARD_POOL_ADDRESS);
            
            // Check current network
            const network = await web3Provider.getNetwork();
            if (network.chainId !== 80002n) {
                throw new Error(`Wrong network! Please switch to Polygon Amoy testnet. Current: ${network.chainId}`);
            }
            
            // Show user confirmation
            const userConfirmed = confirm(
                `Approve ${amount} TEO spending for TeoCoin discount?\n\n` +
                `This will allow the reward pool to spend ${amount} TEO from your wallet.\n` +
                `Click OK to proceed with MetaMask approval.`
            );

            if (!userConfirmed) {
                throw new Error('Approval cancelled by user');
            }

            // Request approval transaction
            const tx = await contract.approve(REWARD_POOL_ADDRESS, amountWei, {
                gasLimit: 60000n
            });
            
            console.log('⏳ Waiting for approval confirmation...');
            const receipt = await tx.wait();
            
            console.log('✅ Approval confirmed in block:', receipt.blockNumber);
            setApprovalStatus('completed');
            
            // Update allowance
            await updateTeoInfo(web3Provider, walletAddress);
            
            return tx.hash;
            
        } catch (error) {
            console.error('Approval failed:', error);
            setApprovalStatus('failed');
            
            if (error.message.includes('user rejected')) {
                throw new Error('Transaction was cancelled by user');
            } else if (error.message.includes('insufficient funds')) {
                throw new Error('Insufficient MATIC for gas fees');
            } else {
                throw new Error(`Approval failed: ${error.message}`);
            }
        }
    };

    // Execute actual TeoCoin transfer transaction
    const executeTeoCoinTransfer = async (amount) => {
        try {
            const signer = await web3Provider.getSigner();
            const contract = new ethers.Contract(TEOCOIN_CONTRACT_ADDRESS, TEOCOIN_ABI, signer);
            
            // Convert amount to Wei (18 decimals)
            const amountWei = ethers.parseEther(amount.toString());
            
            console.log('💰 Executing TeoCoin transfer:', amount, 'TEO to', REWARD_POOL_ADDRESS);
            
            // Show user confirmation for transfer
            const userConfirmed = confirm(
                `Transfer ${amount} TEO for discount?\n\n` +
                `This will transfer ${amount} TEO from your wallet to apply the course discount.\n` +
                `Click OK to proceed with the transfer.`
            );

            if (!userConfirmed) {
                throw new Error('Transfer cancelled by user');
            }

            // Execute transfer using transferFrom (since we have approval)
            // Note: We need to extend the ABI to include transferFrom
            const transferAbi = [
                {
                    "inputs": [
                        {"internalType": "address", "name": "from", "type": "address"},
                        {"internalType": "address", "name": "to", "type": "address"},
                        {"internalType": "uint256", "name": "amount", "type": "uint256"}
                    ],
                    "name": "transferFrom",
                    "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ];
            
            // Create contract with extended ABI
            const extendedContract = new ethers.Contract(TEOCOIN_CONTRACT_ADDRESS, [...TEOCOIN_ABI, ...transferAbi], signer);
            
            // Execute transferFrom: from user wallet to reward pool
            const transferTx = await extendedContract.transferFrom(
                walletAddress,
                REWARD_POOL_ADDRESS,
                amountWei,
                { gasLimit: 80000n }
            );
            
            console.log('⏳ Waiting for transfer confirmation...');
            const receipt = await transferTx.wait();
            
            console.log('✅ Transfer confirmed in block:', receipt.blockNumber);
            console.log('💰 Gas used:', receipt.gasUsed.toString());
            
            // Update balance
            await updateTeoInfo(web3Provider, walletAddress);
            
            return transferTx.hash;
            
        } catch (error) {
            console.error('Transfer failed:', error);
            
            if (error.message.includes('user rejected')) {
                throw new Error('Transfer was cancelled by user');
            } else if (error.message.includes('insufficient funds')) {
                throw new Error('Insufficient MATIC for gas fees');
            } else if (error.message.includes('insufficient allowance')) {
                throw new Error('Insufficient TeoCoin allowance. Please approve spending first.');
            } else {
                throw new Error(`Transfer failed: ${error.message}`);
            }
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
    // Remove disabled options (free for paid courses, disabled teocoin options)
    const cleanedOptions = pricingOptions.filter(opt => !opt.disabled);

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
                    {discountApplied && (
                        <div className="discount-summary">
                            🎉 TeoCoin discount applied! Check browser console for details.
                        </div>
                    )}
                </div>

                <div className="payment-options">
                    {cleanedOptions.map((option) => (
                        <div
                            key={option.method}
                            className={`payment-option ${paymentMethod === option.method ? 'selected' : ''} ${
                                discountApplied && option.method === 'teocoin' ? 'disabled' : ''
                            }`}
                            onClick={() => {
                                // Prevent switching to TeoCoin if discount already applied
                                if (discountApplied && option.method === 'teocoin') {
                                    return;
                                }
                                // Prevent switching away from fiat if discount applied
                                if (discountApplied && paymentMethod === 'fiat') {
                                    return;
                                }
                                // TODO: Re-enable balance check after debugging
                                // if (option.method === 'teocoin' && !paymentSummary?.can_pay_with_teocoin) {
                                //     return;
                                // }
                                setPaymentMethod(option.method);
                            }}
                        >
                            <div className="option-header">
                                <input
                                    type="radio"
                                    name="payment"
                                    checked={paymentMethod === option.method}
                                    disabled={
                                        discountApplied && ((option.method === 'teocoin') || (paymentMethod === 'fiat'))
                                        // TODO: Re-enable balance check after debugging
                                        // || (option.method === 'teocoin' && !paymentSummary?.can_pay_with_teocoin)
                                    }
                                    onChange={() => {
                                        if (discountApplied && option.method === 'teocoin') return;
                                        if (discountApplied && paymentMethod === 'fiat') return;
                                        // TODO: Re-enable balance check after debugging
                                        // if (option.method === 'teocoin' && !paymentSummary?.can_pay_with_teocoin) return;
                                        setPaymentMethod(option.method);
                                    }}
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
                                    <div className="benefit">🪙 Use {option.price} TEO for {option.discount}% discount</div>
                                    <div className="benefit">💰 Save €{((course.price || paymentSummary?.pricing_options?.find(opt => opt.method === 'fiat')?.price || 0) * option.discount / 100).toFixed(2)} on this course</div>
                                    <div className="benefit">💳 Then pay remaining amount with card</div>
                                    <div className="balance">
                                        Your balance: {teoBalance} TEO
                                    </div>
                                    {teoBalance < parseFloat(option.price || 0) && (
                                        <div className="insufficient-balance-warning">
                                            ⚠️ Insufficient balance - Need {option.price} TEO, have {teoBalance} TEO
                                        </div>
                                    )}
                                    {discountApplied && (
                                        <div className="discount-locked">
                                            🔒 Discount already applied - complete with card payment
                                        </div>
                                    )}
                                    
                                    {/* Web3 Connection Status */}
                                    <div className="web3-status">
                                        {!walletConnected ? (
                                            <div className="wallet-required">
                                                <button onClick={connectWallet} className="connect-wallet-btn">
                                                    🦊 Connect MetaMask Wallet
                                                </button>
                                                <small>Required for TeoCoin transactions</small>
                                            </div>
                                        ) : (
                                            <div className="wallet-connected">
                                                <div className="wallet-info">
                                                    ✅ Wallet: {walletAddress.slice(0, 6)}...{walletAddress.slice(-4)}
                                                </div>
                                                <div className="network-info">
                                                    🌐 Network: Polygon Amoy
                                                </div>
                                                <div className="teo-info">
                                                    💰 TEO Balance: {teoBalance}
                                                </div>
                                                <div className="approval-info">
                                                    🔑 Approved: {teoAllowance} TEO
                                                    {approvalStatus === 'pending' && <span> (⏳ Pending...)</span>}
                                                    {approvalStatus === 'completed' && <span> (✅ Ready)</span>}
                                                    {approvalStatus === 'failed' && <span> (❌ Failed - Try again)</span>}
                                                </div>
                                                {approvalStatus === 'failed' && (
                                                    <div className="approval-help">
                                                        <small>� <strong>MetaMask RPC Issue Detected</strong></small><br/>
                                                        <small>📋 <strong>Try these solutions:</strong></small><br/>
                                                        <small>1. 🔄 Reset MetaMask: Settings → Advanced → Reset Account</small><br/>
                                                        <small>2. 🌐 Different browser/incognito window</small><br/>
                                                        <small>3. 📱 Use MetaMask mobile app instead</small><br/>
                                                        <small>4. 🔗 Try WalletConnect-compatible wallet</small><br/>
                                                        <small>5. ⚙️ Add backup RPC: https://polygon-amoy.drpc.org</small><br/>
                                                        <small><strong>Note:</strong> This is a known Polygon Amoy testnet issue</small>
                                                    </div>
                                                )}
                                            </div>
                                        )}
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
                    {/* Unified payment button that handles both fiat and TeoCoin flows */}
                    <button
                        onClick={handlePayment}
                        disabled={processing || (!stripe && paymentMethod === 'fiat')}
                        className={paymentMethod === 'teocoin' ? 'btn-crypto' : 'btn-primary'}
                    >
                        {processing ? '⏳ Processing...' : 
                         paymentMethod === 'teocoin' && !walletConnected ? '🦊 Connect MetaMask First' :
                         paymentMethod === 'teocoin' && discountApplied ? '✅ Discount Applied' :
                         paymentMethod === 'teocoin' && approvalStatus === 'pending' ? '⏳ Approving...' :
                         paymentMethod === 'teocoin' ? '🪙 Apply TeoCoin Discount' :
                         discountApplied ? '💳 Pay Discounted Amount' : '💳 Pay with Card'}
                    </button>
                    <button onClick={onClose} className="btn-secondary">
                        Cancel
                    </button>
                </div>

                {paymentMethod === 'teocoin' && (
                    <div className="teocoin-info">
                        ℹ️ This will apply your TeoCoin discount. You'll then pay the reduced amount with your card.
                    </div>
                )}

                {discountApplied && paymentMethod === 'fiat' && (
                    <div className="discount-applied-info">
                        ✅ TeoCoin discount applied! Complete your purchase at the reduced price.
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

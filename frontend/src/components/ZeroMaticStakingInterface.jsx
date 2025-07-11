import React, { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import { 
    getTeacherTierInfo,
    teacherStakeTokens,
    teacherUnstakeTokens,
    generateTeacherStakingMessage 
} from '../services/api/gasFreeV2';

/**
 * ZeroMaticStakingInterface - Gas-free teacher staking with anti-abuse protection
 * Teachers only sign messages, platform pays all gas fees
 */
const ZeroMaticStakingInterface = ({ 
    walletAddress, 
    web3Provider,
    onStakingUpdate 
}) => {
    const [teacherInfo, setTeacherInfo] = useState(null);
    const [stakingAmount, setStakingAmount] = useState('');
    const [unstakingAmount, setUnstakingAmount] = useState('');
    const [processing, setProcessing] = useState(false);
    const [restrictions, setRestrictions] = useState(null);
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(null);
    const [error, setError] = useState(null);

    // Tier information
    const tierInfo = {
        0: { name: 'Bronze', required: 0, commission: 25, color: '#CD7F32' },
        1: { name: 'Silver', required: 100, commission: 22, color: '#C0C0C0' },
        2: { name: 'Gold', required: 300, commission: 19, color: '#FFD700' },
        3: { name: 'Platinum', required: 600, commission: 16, color: '#E5E4E2' },
        4: { name: 'Diamond', required: 1000, commission: 15, color: '#B9F2FF' }
    };

    // Load teacher staking information
    const loadTeacherInfo = async () => {
        if (!walletAddress) return;
        
        setLoading(true);
        try {
            // Get tier info using API service
            const tierData = await getTeacherTierInfo(walletAddress);
            
            if (tierData.success) {
                setTeacherInfo(tierData.tier_info);
            } else {
                setError(tierData.error || 'Failed to load tier information');
            }
            
        } catch (error) {
            console.error('Error loading teacher info:', error);
            setError(error.message || 'Failed to load staking information');
        } finally {
            setLoading(false);
        }
    };

    // Process gas-free staking
    const processGasFreeStaking = async () => {
        if (!stakingAmount || parseFloat(stakingAmount) <= 0) {
            setError('Please enter a valid staking amount');
            return;
        }
        
        setProcessing(true);
        setError(null);
        setSuccess(null);
        
        try {
            console.log('🚀 Processing gas-free staking...');
            console.log(`💰 Amount: ${stakingAmount} TEO`);
            console.log(`👨‍🏫 Teacher: ${walletAddress}`);
            console.log('⛽ Gas cost for teacher: 0 MATIC (Platform pays ALL fees)');

            if (!window.ethereum) {
                throw new Error('MetaMask not found. Please install MetaMask.');
            }

            const provider = new ethers.BrowserProvider(window.ethereum);
            const signer = await provider.getSigner();
            
            // Create staking signature message
            const messageHash = ethers.solidityPackedKeccak256(
                ["bytes32"],
                [ethers.solidityPackedKeccak256(
                    ["address", "uint256", "string", "address", "uint256"],
                    [
                        walletAddress,
                        ethers.parseEther(stakingAmount),
                        "stake",
                        process.env.REACT_APP_STAKING_CONTRACT_V2_ADDRESS,
                        137 // Polygon chain ID
                    ]
                )]
            );
            
            // Add Ethereum signed message prefix
            const ethMessageHash = ethers.solidityPackedKeccak256(
                ["string", "bytes32"],
                ["\x19Ethereum Signed Message:\n32", messageHash]
            );
            
            // Teacher signs message (FREE - no gas cost)
            console.log('✍️ Please sign the staking message in MetaMask (no gas fees)...');
            const signature = await signer.signMessage(ethers.getBytes(messageHash));
            console.log('✅ Staking message signed successfully (cost: 0 MATIC)');
            
            // Send to backend (platform handles blockchain transaction)
            console.log('📤 Sending staking request to platform (platform pays gas)...');
            
            const result = await teacherStakeTokens({
                teacher_address: walletAddress,
                teo_amount: stakingAmount,
                teacher_signature: signature
            });
            
            if (result.success) {
                console.log('🎉 Gas-free staking successful!');
                
                setSuccess({
                    message: `Successfully staked ${result.amount_staked} TEO!`,
                    newTier: result.new_tier,
                    txHash: result.tx_hash,
                    teacherGasCost: '0 MATIC (Gas-free!)',
                    platformGasCost: result.platform_gas_cost
                });
                
                // Reset form
                setStakingAmount('');
                
                // Reload teacher info
                await loadTeacherInfo();
                
                // Callback to parent
                if (onStakingUpdate) {
                    onStakingUpdate(result);
                }
                
            } else {
                throw new Error(result.error || 'Failed to stake tokens');
            }
            
        } catch (error) {
            console.error('❌ Gas-free staking failed:', error);
            setError(error.message);
        } finally {
            setProcessing(false);
        }
    };

    // Process gas-free unstaking
    const processGasFreeUnstaking = async () => {
        if (!unstakingAmount || parseFloat(unstakingAmount) <= 0) {
            setError('Please enter a valid unstaking amount');
            return;
        }
        
        if (parseFloat(unstakingAmount) > teacherInfo.amount) {
            setError('Cannot unstake more than your staked amount');
            return;
        }
        
        setProcessing(true);
        setError(null);
        setSuccess(null);
        
        try {
            console.log('🚀 Processing gas-free unstaking...');
            console.log(`💰 Amount: ${unstakingAmount} TEO`);
            
            const provider = new ethers.BrowserProvider(window.ethereum);
            const signer = await provider.getSigner();
            
            // Create unstaking signature message
            const messageHash = ethers.solidityPackedKeccak256(
                ["bytes32"],
                [ethers.solidityPackedKeccak256(
                    ["address", "uint256", "string", "address", "uint256"],
                    [
                        walletAddress,
                        ethers.parseEther(unstakingAmount),
                        "unstake",
                        process.env.REACT_APP_STAKING_CONTRACT_V2_ADDRESS,
                        137
                    ]
                )]
            );
            
            const ethMessageHash = ethers.solidityPackedKeccak256(
                ["string", "bytes32"],
                ["\x19Ethereum Signed Message:\n32", messageHash]
            );
            
            console.log('✍️ Please sign the unstaking message in MetaMask (no gas fees)...');
            const signature = await signer.signMessage(ethers.getBytes(messageHash));
            console.log('✅ Unstaking message signed successfully (cost: 0 MATIC)');
            
            const result = await teacherUnstakeTokens({
                teacher_address: walletAddress,
                teo_amount: unstakingAmount,
                teacher_signature: signature
            });
            
            if (result.success) {
                setSuccess({
                    message: `Successfully unstaked ${result.amount_unstaked} TEO!`,
                    newTier: result.new_tier,
                    txHash: result.tx_hash
                });
                
                setUnstakingAmount('');
                await loadTeacherInfo();
                
                if (onStakingUpdate) {
                    onStakingUpdate(result);
                }
                
            } else {
                throw new Error(result.error || 'Failed to unstake tokens');
            }
            
        } catch (error) {
            console.error('❌ Gas-free unstaking failed:', error);
            setError(error.message);
        } finally {
            setProcessing(false);
        }
    };

    // Load teacher info on mount
    useEffect(() => {
        if (walletAddress) {
            loadTeacherInfo();
        }
    }, [walletAddress]);

    // Calculate potential tier after staking
    const calculatePotentialTier = (currentAmount, additionalAmount) => {
        const totalAmount = parseFloat(currentAmount) + parseFloat(additionalAmount || 0);
        
        for (let tier = 4; tier >= 0; tier--) {
            if (totalAmount >= tierInfo[tier].required) {
                return tier;
            }
        }
        return 0;
    };

    if (loading) {
        return (
            <div className="staking-container">
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Loading staking information...</p>
                </div>
            </div>
        );
    }

    const currentTier = teacherInfo?.tier || 0;
    const currentTierInfo = tierInfo[currentTier];
    const potentialTier = stakingAmount ? calculatePotentialTier(teacherInfo?.amount || 0, stakingAmount) : currentTier;
    const potentialTierInfo = tierInfo[potentialTier];

    return (
        <div className="staking-container">
            <div className="staking-header">
                <h3>🏆 Gas-Free Teacher Staking</h3>
                <p className="zero-cost-badge">
                    ⛽ <strong>0 MATIC</strong> gas fees for you!
                </p>
            </div>

            {/* Current Tier Status */}
            <div className="current-tier-section">
                <div className="tier-card" style={{ borderColor: currentTierInfo.color }}>
                    <div className="tier-header">
                        <h4 style={{ color: currentTierInfo.color }}>
                            {currentTierInfo.name} Tier
                        </h4>
                        <span className="commission-rate">
                            {currentTierInfo.commission}% Platform Commission
                        </span>
                    </div>
                    <div className="tier-details">
                        <div className="detail">
                            <span className="label">Staked Amount:</span>
                            <span className="value">{teacherInfo?.amount || 0} TEO</span>
                        </div>
                        <div className="detail">
                            <span className="label">Your Commission:</span>
                            <span className="value">{100 - currentTierInfo.commission}%</span>
                        </div>
                        <div className="detail">
                            <span className="label">Status:</span>
                            <span className="value">{teacherInfo?.active ? 'Active' : 'Inactive'}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Tier Progression */}
            <div className="tier-progression">
                <h4>Tier Progression</h4>
                <div className="tiers-list">
                    {Object.entries(tierInfo).map(([tier, info]) => {
                        const isCurrentTier = parseInt(tier) === currentTier;
                        const isPotentialTier = parseInt(tier) === potentialTier && potentialTier !== currentTier;
                        const isUnlocked = (teacherInfo?.amount || 0) >= info.required;
                        
                        return (
                            <div 
                                key={tier}
                                className={`tier-item ${isCurrentTier ? 'current' : ''} ${isPotentialTier ? 'potential' : ''} ${isUnlocked ? 'unlocked' : ''}`}
                                style={{ borderLeftColor: info.color }}
                            >
                                <div className="tier-name" style={{ color: info.color }}>
                                    {info.name}
                                    {isCurrentTier && <span className="current-badge">CURRENT</span>}
                                    {isPotentialTier && <span className="potential-badge">NEXT</span>}
                                </div>
                                <div className="tier-requirement">
                                    {info.required} TEO required
                                </div>
                                <div className="tier-commission">
                                    {100 - info.commission}% teacher commission
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Anti-Abuse Status */}
            {restrictions && (
                <div className="restrictions-section">
                    <h4>🛡️ Anti-Abuse Protection Status</h4>
                    <div className="restrictions-grid">
                        <div className="restriction-item">
                            <span className="label">Can Stake:</span>
                            <span className={`status ${restrictions.canStake ? 'allowed' : 'blocked'}`}>
                                {restrictions.canStake ? '✅ Allowed' : '❌ Blocked'}
                            </span>
                        </div>
                        <div className="restriction-item">
                            <span className="label">Can Unstake:</span>
                            <span className={`status ${restrictions.canUnstake ? 'allowed' : 'blocked'}`}>
                                {restrictions.canUnstake ? '✅ Allowed' : '❌ Blocked'}
                            </span>
                        </div>
                        <div className="restriction-item">
                            <span className="label">Stakes Used (7 days):</span>
                            <span className="value">{restrictions.stakesUsed7Days}/2</span>
                        </div>
                        <div className="restriction-item">
                            <span className="label">Unstakes Used (7 days):</span>
                            <span className="value">{restrictions.unstakesUsed7Days}/1</span>
                        </div>
                    </div>
                    
                    {!restrictions.canStake && (
                        <div className="restriction-warning">
                            <p>⏰ Staking temporarily restricted due to anti-abuse rules:</p>
                            <ul>
                                <li>Maximum 2 stakes per 7 days</li>
                                <li>3-day cooldown between stakes</li>
                            </ul>
                        </div>
                    )}
                    
                    {!restrictions.canUnstake && (
                        <div className="restriction-warning">
                            <p>🔒 Unstaking temporarily restricted:</p>
                            <ul>
                                <li>7-day minimum lockup period</li>
                                <li>7-day cooldown between unstakes</li>
                                <li>Maximum 1 unstake per 7 days</li>
                            </ul>
                        </div>
                    )}
                </div>
            )}

            {/* Staking Section */}
            <div className="staking-section">
                <h4>📈 Stake TEO Tokens</h4>
                <div className="staking-form">
                    <div className="input-group">
                        <input
                            type="number"
                            value={stakingAmount}
                            onChange={(e) => setStakingAmount(e.target.value)}
                            placeholder="Amount to stake (TEO)"
                            min="1"
                            step="1"
                            disabled={processing || !restrictions?.canStake}
                        />
                        <span className="currency">TEO</span>
                    </div>
                    
                    {stakingAmount && potentialTier > currentTier && (
                        <div className="tier-upgrade-preview">
                            <p>🎉 This will upgrade you to <strong style={{ color: potentialTierInfo.color }}>
                                {potentialTierInfo.name} Tier
                            </strong>!</p>
                            <p>New commission rate: <strong>{100 - potentialTierInfo.commission}%</strong></p>
                        </div>
                    )}
                    
                    <button
                        className="btn btn-primary stake-btn"
                        onClick={processGasFreeStaking}
                        disabled={processing || !stakingAmount || !restrictions?.canStake}
                    >
                        {processing ? 'Processing...' : 'Stake Tokens (Gas-Free)'}
                    </button>
                    
                    {!restrictions?.canStake && (
                        <p className="restriction-notice">
                            Staking temporarily restricted. See anti-abuse status above.
                        </p>
                    )}
                </div>
            </div>

            {/* Unstaking Section */}
            {teacherInfo?.amount > 0 && (
                <div className="unstaking-section">
                    <h4>📉 Unstake TEO Tokens</h4>
                    <div className="unstaking-form">
                        <div className="input-group">
                            <input
                                type="number"
                                value={unstakingAmount}
                                onChange={(e) => setUnstakingAmount(e.target.value)}
                                placeholder="Amount to unstake (TEO)"
                                min="1"
                                max={teacherInfo?.amount || 0}
                                step="1"
                                disabled={processing || !restrictions?.canUnstake}
                            />
                            <span className="currency">TEO</span>
                        </div>
                        
                        <p className="available-amount">
                            Available to unstake: {teacherInfo?.amount || 0} TEO
                        </p>
                        
                        <button
                            className="btn btn-secondary unstake-btn"
                            onClick={processGasFreeUnstaking}
                            disabled={processing || !unstakingAmount || !restrictions?.canUnstake}
                        >
                            {processing ? 'Processing...' : 'Unstake Tokens (Gas-Free)'}
                        </button>
                        
                        {!restrictions?.canUnstake && (
                            <p className="restriction-notice">
                                Unstaking temporarily restricted due to lockup period or cooldown.
                            </p>
                        )}
                    </div>
                </div>
            )}

            {/* How It Works */}
            <div className="how-it-works">
                <h4>🔧 How Gas-Free Staking Works:</h4>
                <div className="steps">
                    <div className="step">
                        <span className="number">1</span>
                        <span className="text">Enter amount & sign message (FREE)</span>
                    </div>
                    <div className="step">
                        <span className="number">2</span>
                        <span className="text">Platform pays gas fees (~$0.005)</span>
                    </div>
                    <div className="step">
                        <span className="number">3</span>
                        <span className="text">Your tier updates automatically!</span>
                    </div>
                </div>
                <div className="anti-abuse-note">
                    <p><strong>Anti-Abuse Protection:</strong> Time restrictions prevent gaming the tier system before course purchases.</p>
                </div>
            </div>

            {/* Success State */}
            {success && (
                <div className="success-state">
                    <div className="success-content">
                        <h3>🎉 Operation Successful!</h3>
                        <p>{success.message}</p>
                        {success.newTier && (
                            <div className="tier-update">
                                <p>New Tier: <strong style={{ color: tierInfo[success.newTier.tier].color }}>
                                    {success.newTier.tier_name}
                                </strong></p>
                                <p>Commission Rate: <strong>{success.newTier.commission_rate}%</strong></p>
                            </div>
                        )}
                        <div className="gas-info">
                            <p><strong>Your Gas Cost:</strong> {success.teacherGasCost}</p>
                        </div>
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
                        Dismiss
                    </button>
                </div>
            )}
        </div>
    );
};

export default ZeroMaticStakingInterface;

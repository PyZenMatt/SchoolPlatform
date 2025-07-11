import React, { useState } from 'react';
import { ethers } from 'ethers';

const TeoApprovalHelper = ({ studentAddress, onApprovalComplete }) => {
    const [approving, setApproving] = useState(false);
    const [approved, setApproved] = useState(false);
    const [error, setError] = useState(null);

    const TEO_CONTRACT_ADDRESS = '0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8';
    const GAS_FREE_CONTRACT_ADDRESS = '0x998BbCAABe181843b440D6079596baee6367CAd9';

    // Simple ERC20 ABI for approve function
    const ERC20_ABI = [
        "function approve(address spender, uint256 amount) external returns (bool)",
        "function allowance(address owner, address spender) external view returns (uint256)",
        "function balanceOf(address account) external view returns (uint256)"
    ];

    const checkApproval = async () => {
        try {
            if (typeof window.ethereum === 'undefined') {
                throw new Error('MetaMask not found');
            }

            const provider = new ethers.BrowserProvider(window.ethereum);
            const teoContract = new ethers.Contract(TEO_CONTRACT_ADDRESS, ERC20_ABI, provider);
            
            const allowance = await teoContract.allowance(studentAddress, GAS_FREE_CONTRACT_ADDRESS);
            const requiredApproval = ethers.parseEther("100"); // 100 TEO minimum
            
            return allowance >= requiredApproval;
        } catch (err) {
            console.error('Error checking approval:', err);
            return false;
        }
    };

    const approveTokens = async () => {
        setApproving(true);
        setError(null);

        try {
            if (typeof window.ethereum === 'undefined') {
                throw new Error('MetaMask not found. Please install MetaMask.');
            }

            // Request account access
            await window.ethereum.request({ method: 'eth_requestAccounts' });
            
            const provider = new ethers.BrowserProvider(window.ethereum);
            const signer = await provider.getSigner();
            
            // Check if we're on the right network
            const network = await provider.getNetwork();
            if (network.chainId !== 80002n) { // Polygon Amoy
                throw new Error('Please switch to Polygon Amoy testnet');
            }

            const teoContract = new ethers.Contract(TEO_CONTRACT_ADDRESS, ERC20_ABI, signer);
            
            // Approve 1000 TEO tokens (enough for many discounts)
            const approvalAmount = ethers.parseEther("1000");
            console.log('🎫 Requesting TEO approval...');
            
            const tx = await teoContract.approve(GAS_FREE_CONTRACT_ADDRESS, approvalAmount);
            console.log('⏳ Waiting for approval confirmation...');
            
            await tx.wait();
            console.log('✅ TEO approval successful!');
            
            setApproved(true);
            if (onApprovalComplete) {
                onApprovalComplete();
            }
            
        } catch (err) {
            console.error('Approval error:', err);
            setError(err.message || 'Approval failed');
        } finally {
            setApproving(false);
        }
    };

    return (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
            <h3 className="text-lg font-semibold text-yellow-800 mb-2">
                🎫 TEO Token Approval Required
            </h3>
            
            <div className="text-yellow-700 mb-3">
                <p>To use gas-free discounts, you need to approve TEO tokens once.</p>
                <p className="text-sm mt-1">
                    This allows the platform to spend your TEO tokens for discounts while paying all gas fees.
                </p>
            </div>

            <div className="space-y-2">
                <div className="text-sm text-gray-600">
                    <p><strong>TEO Contract:</strong> {TEO_CONTRACT_ADDRESS}</p>
                    <p><strong>Gas-Free Contract:</strong> {GAS_FREE_CONTRACT_ADDRESS}</p>
                    <p><strong>Approval Amount:</strong> 1000 TEO tokens</p>
                </div>

                {error && (
                    <div className="bg-red-100 border border-red-200 text-red-700 px-3 py-2 rounded">
                        ❌ {error}
                    </div>
                )}

                {approved ? (
                    <div className="bg-green-100 border border-green-200 text-green-700 px-3 py-2 rounded">
                        ✅ TEO tokens approved! You can now use gas-free discounts.
                    </div>
                ) : (
                    <button
                        onClick={approveTokens}
                        disabled={approving}
                        className={`w-full px-4 py-2 rounded font-medium ${
                            approving
                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                : 'bg-yellow-600 text-white hover:bg-yellow-700'
                        }`}
                    >
                        {approving ? (
                            <>
                                <span className="animate-spin inline-block mr-2">⏳</span>
                                Approving TEO Tokens...
                            </>
                        ) : (
                            '🎫 Approve TEO Tokens (One-time setup)'
                        )}
                    </button>
                )}
            </div>

            <div className="text-xs text-gray-500 mt-2">
                💡 You only need to do this once. After approval, all future discounts will be gas-free!
            </div>
        </div>
    );
};

export default TeoApprovalHelper;

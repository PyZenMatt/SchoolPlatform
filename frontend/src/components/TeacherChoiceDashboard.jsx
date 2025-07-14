import React, { useState, useEffect } from 'react';
import apiV2Client from '../services/core/apiV2Client';

/**
 * Teacher Choice Dashboard - Layer 2 Gas-Free TeoCoin System
 * Allows teachers to choose between TEO payment or full fiat payment
 * Platform pays all gas fees - teachers pay zero MATIC
 */
const TeacherChoiceDashboard = ({ user }) => {
    const [pendingChoices, setPendingChoices] = useState([]);
    const [choiceHistory, setChoiceHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(null);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('pending');

    useEffect(() => {
        if (user && user.role === 'teacher') {
            loadPendingChoices();
            loadChoiceHistory();
        }
    }, [user]);

    const loadPendingChoices = async () => {
        try {
            setLoading(true);
            const response = await apiV2Client.get('/teacher/choices/pending/');
            if (response.data.success) {
                setPendingChoices(response.data.pending_choices);
            }
        } catch (error) {
            console.error('Error loading pending choices:', error);
            setError('Failed to load pending choices');
        } finally {
            setLoading(false);
        }
    };

    const loadChoiceHistory = async () => {
        try {
            const response = await apiV2Client.get('/teacher/choices/history/');
            if (response.data.success) {
                setChoiceHistory(response.data.choice_history);
            }
        } catch (error) {
            console.error('Error loading choice history:', error);
        }
    };

    const handleAcceptTeo = async (requestId) => {
        try {
            setProcessing(requestId);
            const response = await apiV2Client.post('/teacher/choices/accept/', {
                request_id: requestId
            });

            if (response.data.success) {
                // Remove from pending and reload
                setPendingChoices(prev => prev.filter(choice => choice.request_id !== requestId));
                loadChoiceHistory();
                
                // Show success message
                alert(`✅ TEO payment accepted! You will receive ${response.data.teo_received} TEO (includes ${response.data.teo_bonus} TEO bonus)`);
            }
        } catch (error) {
            console.error('Error accepting TEO:', error);
            alert('❌ Failed to accept TEO payment');
        } finally {
            setProcessing(null);
        }
    };

    const handleDeclineTeo = async (requestId) => {
        try {
            setProcessing(requestId);
            const response = await apiV2Client.post('/teacher/choices/decline/', {
                request_id: requestId
            });

            if (response.data.success) {
                // Remove from pending and reload
                setPendingChoices(prev => prev.filter(choice => choice.request_id !== requestId));
                loadChoiceHistory();
                
                // Show success message
                alert(`✅ TEO declined! You will receive €${response.data.fiat_payment} fiat payment (platform absorbs TEO cost)`);
            }
        } catch (error) {
            console.error('Error declining TEO:', error);
            alert('❌ Failed to decline TEO payment');
        } finally {
            setProcessing(null);
        }
    };

    const formatTimeRemaining = (expiresAt) => {
        const now = new Date();
        const expiry = new Date(expiresAt);
        const remaining = expiry - now;
        
        if (remaining <= 0) return 'Expired';
        
        const hours = Math.floor(remaining / (1000 * 60 * 60));
        const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));
        
        return `${hours}h ${minutes}m remaining`;
    };

    if (!user || user.role !== 'teacher') {
        return (
            <div className="teacher-choice-dashboard">
                <div className="alert alert-warning">
                    This dashboard is only available for teachers.
                </div>
            </div>
        );
    }

    return (
        <div className="teacher-choice-dashboard">
            {/* Header */}
            <div className="dashboard-header">
                <h2>🎯 TeoCoin Choice Dashboard</h2>
                <p>Choose between TEO payments or fiat safety - Platform pays all gas fees!</p>
            </div>

            {/* Navigation Tabs */}
            <div className="choice-tabs">
                <button 
                    className={`tab-btn ${activeTab === 'pending' ? 'active' : ''}`}
                    onClick={() => setActiveTab('pending')}
                >
                    📋 Pending Choices ({pendingChoices.length})
                </button>
                <button 
                    className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
                    onClick={() => setActiveTab('history')}
                >
                    📊 Choice History
                </button>
            </div>

            {error && (
                <div className="alert alert-danger">
                    {error}
                </div>
            )}

            {/* Pending Choices Tab */}
            {activeTab === 'pending' && (
                <div className="pending-choices-section">
                    <h3>⏰ Pending Discount Choices</h3>
                    {loading ? (
                        <div className="loading">Loading pending choices...</div>
                    ) : pendingChoices.length === 0 ? (
                        <div className="no-choices">
                            <p>🎉 No pending choices! All caught up.</p>
                            <small>Students using discounts will appear here for your decision.</small>
                        </div>
                    ) : (
                        <div className="choices-grid">
                            {pendingChoices.map((choice) => (
                                <div key={choice.request_id} className="choice-card">
                                    {/* Choice Header */}
                                    <div className="choice-header">
                                        <h4>{choice.course_title}</h4>
                                        <div className="time-remaining">
                                            {formatTimeRemaining(choice.expires_at)}
                                        </div>
                                    </div>

                                    {/* Student Info */}
                                    <div className="student-info">
                                        <p><strong>Student:</strong> {choice.student_name}</p>
                                        <p><strong>Discount:</strong> {choice.discount_percent}% off €{choice.course_price}</p>
                                        <p><strong>TEO Cost:</strong> {choice.teo_cost} TEO</p>
                                    </div>

                                    {/* Choice Options */}
                                    <div className="choice-options">
                                        {/* Accept TEO Option */}
                                        <div className="choice-option accept-teo">
                                            <h5>✅ Accept TeoCoin Payment</h5>
                                            <div className="rewards">
                                                <p><strong>💰 Fiat:</strong> €{choice.choices.accept_teo.fiat_amount.toFixed(2)}</p>
                                                <p><strong>🪙 TEO:</strong> {choice.choices.accept_teo.teo_amount} TEO</p>
                                                <p><strong>🎁 Bonus:</strong> +{choice.choices.accept_teo.teo_bonus} TEO (25%)</p>
                                            </div>
                                            <ul className="benefits">
                                                {choice.choices.accept_teo.benefits.map((benefit, idx) => (
                                                    <li key={idx}>{benefit}</li>
                                                ))}
                                            </ul>
                                            <button 
                                                className="choice-btn accept-btn"
                                                onClick={() => handleAcceptTeo(choice.request_id)}
                                                disabled={processing === choice.request_id}
                                            >
                                                {processing === choice.request_id ? 'Processing...' : 'Accept TEO'}
                                            </button>
                                        </div>

                                        {/* Decline TEO Option */}
                                        <div className="choice-option decline-teo">
                                            <h5>💵 Decline TEO, Get Full Fiat</h5>
                                            <div className="rewards">
                                                <p><strong>💰 Fiat:</strong> €{choice.choices.decline_teo.fiat_amount.toFixed(2)}</p>
                                                <p><strong>🪙 TEO:</strong> {choice.choices.decline_teo.teo_amount} TEO</p>
                                            </div>
                                            <ul className="benefits">
                                                {choice.choices.decline_teo.benefits.map((benefit, idx) => (
                                                    <li key={idx}>{benefit}</li>
                                                ))}
                                            </ul>
                                            <button 
                                                className="choice-btn decline-btn"
                                                onClick={() => handleDeclineTeo(choice.request_id)}
                                                disabled={processing === choice.request_id}
                                            >
                                                {processing === choice.request_id ? 'Processing...' : 'Get Full Fiat'}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Choice History Tab */}
            {activeTab === 'history' && (
                <div className="choice-history-section">
                    <h3>📊 Your Choice History</h3>
                    {choiceHistory.summary && (
                        <div className="history-summary">
                            <div className="summary-card">
                                <h4>📈 Summary Statistics</h4>
                                <p><strong>Total Choices:</strong> {choiceHistory.summary.total_choices}</p>
                                <p><strong>TEO Acceptance Rate:</strong> {choiceHistory.summary.acceptance_rate.toFixed(1)}%</p>
                                <p><strong>Total TEO Accepted:</strong> {choiceHistory.summary.total_teo_accepted} TEO</p>
                                <p><strong>Total Fiat from Declines:</strong> €{choiceHistory.summary.total_fiat_from_declines}</p>
                            </div>
                        </div>
                    )}

                    <div className="history-list">
                        {choiceHistory.choice_history && choiceHistory.choice_history.length === 0 ? (
                            <p>No choice history yet.</p>
                        ) : (
                            choiceHistory.choice_history?.map((choice, idx) => (
                                <div key={idx} className="history-item">
                                    <div className="history-header">
                                        <h5>{choice.course_title}</h5>
                                        <span className={`choice-badge ${choice.choice}`}>
                                            {choice.choice === 'accepted_teo' ? '✅ Accepted TEO' : '💵 Took Fiat'}
                                        </span>
                                    </div>
                                    <div className="history-details">
                                        <p><strong>Date:</strong> {new Date(choice.date).toLocaleDateString()}</p>
                                        <p><strong>Discount:</strong> {choice.discount_percent}%</p>
                                        {choice.teo_received && (
                                            <p><strong>TEO Received:</strong> {choice.teo_received} TEO</p>
                                        )}
                                        {choice.fiat_received && (
                                            <p><strong>Fiat Received:</strong> €{choice.fiat_received}</p>
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}

            <style jsx>{`
                .teacher-choice-dashboard {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }

                .dashboard-header {
                    text-align: center;
                    margin-bottom: 30px;
                }

                .dashboard-header h2 {
                    color: #4CAF50;
                    margin-bottom: 10px;
                }

                .choice-tabs {
                    display: flex;
                    gap: 10px;
                    margin-bottom: 30px;
                    border-bottom: 2px solid #e0e0e0;
                }

                .tab-btn {
                    padding: 10px 20px;
                    border: none;
                    background: none;
                    cursor: pointer;
                    border-bottom: 3px solid transparent;
                    transition: all 0.3s ease;
                }

                .tab-btn.active {
                    border-bottom-color: #4CAF50;
                    color: #4CAF50;
                    font-weight: bold;
                }

                .choices-grid {
                    display: grid;
                    gap: 20px;
                    grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
                }

                .choice-card {
                    border: 2px solid #4CAF50;
                    border-radius: 10px;
                    padding: 20px;
                    background: white;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }

                .choice-header {
                    display: flex;
                    justify-content: between;
                    align-items: center;
                    margin-bottom: 15px;
                    padding-bottom: 10px;
                    border-bottom: 1px solid #e0e0e0;
                }

                .time-remaining {
                    background: #ff6b6b;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: bold;
                }

                .student-info {
                    margin-bottom: 20px;
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                }

                .choice-options {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                }

                .choice-option {
                    padding: 15px;
                    border-radius: 8px;
                    border: 2px solid;
                }

                .accept-teo {
                    border-color: #4CAF50;
                    background: #f0fff0;
                }

                .decline-teo {
                    border-color: #2196F3;
                    background: #f0f8ff;
                }

                .rewards {
                    margin: 10px 0;
                    padding: 10px;
                    background: rgba(255,255,255,0.8);
                    border-radius: 5px;
                }

                .benefits {
                    font-size: 12px;
                    margin: 10px 0;
                    padding-left: 15px;
                }

                .choice-btn {
                    width: 100%;
                    padding: 12px;
                    border: none;
                    border-radius: 5px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }

                .accept-btn {
                    background: #4CAF50;
                    color: white;
                }

                .accept-btn:hover {
                    background: #45a049;
                }

                .decline-btn {
                    background: #2196F3;
                    color: white;
                }

                .decline-btn:hover {
                    background: #1976D2;
                }

                .choice-btn:disabled {
                    background: #ccc;
                    cursor: not-allowed;
                }

                .no-choices {
                    text-align: center;
                    padding: 40px;
                    background: #f8f9fa;
                    border-radius: 10px;
                }

                .history-summary {
                    margin-bottom: 30px;
                }

                .summary-card {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    border-left: 5px solid #4CAF50;
                }

                .history-item {
                    padding: 15px;
                    border-bottom: 1px solid #e0e0e0;
                    margin-bottom: 15px;
                }

                .history-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 10px;
                }

                .choice-badge {
                    padding: 5px 10px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: bold;
                }

                .choice-badge.accepted_teo {
                    background: #4CAF50;
                    color: white;
                }

                .choice-badge.declined_teo {
                    background: #2196F3;
                    color: white;
                }

                .alert {
                    padding: 15px;
                    margin-bottom: 20px;
                    border-radius: 5px;
                }

                .alert-warning {
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                }

                .alert-danger {
                    background: #f8d7da;
                    border: 1px solid #f5c6cb;
                    color: #721c24;
                }

                .loading {
                    text-align: center;
                    padding: 40px;
                    color: #666;
                }
            `}</style>
        </div>
    );
};

export default TeacherChoiceDashboard;

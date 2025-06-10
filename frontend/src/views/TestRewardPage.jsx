import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import RewardSystem from '../components/blockchain/RewardSystem';
import WalletConnection from '../components/blockchain/WalletConnectionNew';
import TeoCoinBalance from '../components/blockchain/TeoCoinBalance';

const TestRewardPage = () => {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Get user data from localStorage or context
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            TeoArt Reward System Test
          </h1>
          <p className="mt-2 text-gray-600">
            Test and monitor the automated reward system functionality
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Wallet & Balance */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Wallet Connection</CardTitle>
              </CardHeader>
              <CardContent>
                <WalletConnection user={user} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>TeoCoin Balance</CardTitle>
              </CardHeader>
              <CardContent>
                <TeoCoinBalance user={user} />
              </CardContent>
            </Card>

            {/* User Info */}
            {user && (
              <Card>
                <CardHeader>
                  <CardTitle>User Info</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div><strong>Username:</strong> {user.username}</div>
                    <div><strong>Email:</strong> {user.email}</div>
                    <div><strong>User ID:</strong> {user.id}</div>
                    <div><strong>Role:</strong> {user.role || 'Student'}</div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right Column - Reward System */}
          <div className="lg:col-span-2">
            <RewardSystem user={user} />
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8">
          <Card>
            <CardHeader>
              <CardTitle>How to Test the Reward System</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose max-w-none">
                <ol className="list-decimal list-inside space-y-2">
                  <li><strong>Connect your wallet</strong> using the wallet connection component above</li>
                  <li><strong>Test Lesson Completion:</strong> Enter a lesson ID and click "Trigger Lesson Reward" to simulate completing a lesson</li>
                  <li><strong>Test Course Completion:</strong> Enter a course ID and click "Check Course Completion" to check if you've completed all lessons</li>
                  <li><strong>Test Achievements:</strong> Select an achievement type and trigger it to see achievement rewards</li>
                  <li><strong>Monitor Balance:</strong> Watch your TeoCoin balance update in real-time</li>
                  <li><strong>View History:</strong> Check your recent rewards in the summary section</li>
                </ol>
                
                <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-semibold text-blue-800 mb-2">Available Achievement Types:</h4>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• <code>first_course_completed</code> - Bonus for completing your first course</li>
                    <li>• <code>perfect_scores</code> - Reward for achieving perfect scores</li>
                    <li>• <code>fast_completion</code> - Bonus for quick lesson completion</li>
                    <li>• <code>helpful_peer</code> - Reward for helping other students</li>
                    <li>• <code>consecutive_logins</code> - Bonus for daily login streaks</li>
                  </ul>
                </div>

                <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
                  <h4 className="font-semibold text-yellow-800 mb-2">Notes:</h4>
                  <ul className="text-sm text-yellow-700 space-y-1">
                    <li>• Rewards are calculated as percentages of course prices</li>
                    <li>• Each course has a maximum reward budget (25% of course price)</li>
                    <li>• Blockchain rewards require a connected wallet</li>
                    <li>• Traditional TeoCoins are always awarded regardless of wallet status</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default TestRewardPage;

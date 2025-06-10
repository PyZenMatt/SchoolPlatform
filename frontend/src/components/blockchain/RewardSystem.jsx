import React, { useState, useEffect } from 'react';
import { Card, Button, Form, Badge, Row, Col } from 'react-bootstrap';
import { blockchainAPI } from '../../services/api/blockchainAPI';

const RewardSystem = ({ user }) => {
  const [rewardHistory, setRewardHistory] = useState([]);
  const [rewardSummary, setRewardSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [selectedLesson, setSelectedLesson] = useState('');
  const [achievementType, setAchievementType] = useState('');

  // Fetch reward summary on component mount
  useEffect(() => {
    fetchRewardSummary();
  }, []);

  const fetchRewardSummary = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/rewards/summary/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setRewardSummary(data.reward_summary);
      }
    } catch (error) {
      console.error('Error fetching reward summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const triggerLessonReward = async () => {
    if (!selectedLesson) {
      alert('Please enter a lesson ID');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch('/api/v1/rewards/lesson-completion/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          lesson_id: selectedLesson,
          course_id: selectedCourse || undefined,
        }),
      });

      const data = await response.json();
      if (response.ok) {
        alert(data.message);
        fetchRewardSummary(); // Refresh summary
      } else {
        alert(`Error: ${data.error || data.message}`);
      }
    } catch (error) {
      console.error('Error triggering lesson reward:', error);
      alert('Failed to trigger lesson reward');
    } finally {
      setLoading(false);
    }
  };

  const triggerCourseCompletionCheck = async () => {
    if (!selectedCourse) {
      alert('Please enter a course ID');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch('/api/v1/rewards/course-completion/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          course_id: selectedCourse,
        }),
      });

      const data = await response.json();
      if (response.ok) {
        alert(data.message);
        fetchRewardSummary(); // Refresh summary
      } else {
        alert(`Error: ${data.error || data.message}`);
      }
    } catch (error) {
      console.error('Error checking course completion:', error);
      alert('Failed to check course completion');
    } finally {
      setLoading(false);
    }
  };

  const triggerAchievementReward = async () => {
    if (!achievementType) {
      alert('Please enter an achievement type');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch('/api/v1/rewards/achievement/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          achievement_type: achievementType,
          course_id: selectedCourse || undefined,
        }),
      });

      const data = await response.json();
      if (response.ok) {
        alert(data.message);
        fetchRewardSummary(); // Refresh summary
      } else {
        alert(`Error: ${data.error || data.message}`);
      }
    } catch (error) {
      console.error('Error triggering achievement reward:', error);
      alert('Failed to trigger achievement reward');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Reward Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trophy className="h-5 w-5 text-yellow-600" />
            Reward Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center">Loading...</div>
          ) : rewardSummary ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <Coins className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                <div className="font-semibold text-lg">{rewardSummary.total_reward_earned || 0}</div>
                <div className="text-sm text-gray-600">Total Earned</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <Award className="h-8 w-8 text-green-600 mx-auto mb-2" />
                <div className="font-semibold text-lg">{rewardSummary.lesson_rewards || 0}</div>
                <div className="text-sm text-gray-600">Lesson Rewards</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <Trophy className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                <div className="font-semibold text-lg">{rewardSummary.course_bonuses || 0}</div>
                <div className="text-sm text-gray-600">Course Bonuses</div>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <History className="h-8 w-8 text-orange-600 mx-auto mb-2" />
                <div className="font-semibold text-lg">{rewardSummary.achievements || 0}</div>
                <div className="text-sm text-gray-600">Achievements</div>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500">No reward data available</div>
          )}
        </CardContent>
      </Card>

      {/* Test Reward Triggers */}
      <Card>
        <CardHeader>
          <CardTitle>Test Reward System</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Common inputs */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Course ID (optional)</label>
              <Input
                type="number"
                placeholder="Enter course ID"
                value={selectedCourse}
                onChange={(e) => setSelectedCourse(e.target.value)}
              />
            </div>
          </div>

          {/* Lesson Completion Test */}
          <div className="border p-4 rounded-lg">
            <h4 className="font-medium mb-2">Test Lesson Completion Reward</h4>
            <div className="flex gap-2">
              <Input
                placeholder="Lesson ID"
                value={selectedLesson}
                onChange={(e) => setSelectedLesson(e.target.value)}
                className="flex-1"
              />
              <Button onClick={triggerLessonReward} disabled={loading}>
                Trigger Lesson Reward
              </Button>
            </div>
          </div>

          {/* Course Completion Test */}
          <div className="border p-4 rounded-lg">
            <h4 className="font-medium mb-2">Test Course Completion Check</h4>
            <Button 
              onClick={triggerCourseCompletionCheck} 
              disabled={loading || !selectedCourse}
              className="w-full"
            >
              Check Course Completion
            </Button>
          </div>

          {/* Achievement Test */}
          <div className="border p-4 rounded-lg">
            <h4 className="font-medium mb-2">Test Achievement Reward</h4>
            <div className="flex gap-2">
              <select
                value={achievementType}
                onChange={(e) => setAchievementType(e.target.value)}
                className="flex-1 px-3 py-2 border rounded-md"
              >
                <option value="">Select Achievement Type</option>
                <option value="first_course_completed">First Course Completed</option>
                <option value="perfect_scores">Perfect Scores</option>
                <option value="fast_completion">Fast Completion</option>
                <option value="helpful_peer">Helpful Peer</option>
                <option value="consecutive_logins">Consecutive Logins</option>
              </select>
              <Button onClick={triggerAchievementReward} disabled={loading || !achievementType}>
                Trigger Achievement
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Rewards */}
      {rewardSummary && rewardSummary.recent_rewards && rewardSummary.recent_rewards.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Rewards</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {rewardSummary.recent_rewards.map((reward, index) => (
                <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                  <div>
                    <Badge variant="outline" className="mr-2">
                      {reward.transaction_type?.replace('_', ' ').toUpperCase()}
                    </Badge>
                    <span className="text-sm text-gray-600">
                      {new Date(reward.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="font-semibold text-green-600">
                    +{reward.amount} TC
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default RewardSystem;

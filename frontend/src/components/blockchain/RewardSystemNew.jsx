import React, { useState, useEffect } from 'react';
import { Card, Button, Form, Badge, Row, Col, Spinner } from 'react-bootstrap';
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
    <div className="mb-4">
      {/* Reward Summary */}
      <Card className="mb-4">
        <Card.Header>
          <Card.Title className="d-flex align-items-center gap-2">
            <i className="feather icon-award text-warning me-2"></i>
            Reward Summary
          </Card.Title>
        </Card.Header>
        <Card.Body>
          {loading ? (
            <div className="text-center py-3">
              <Spinner animation="border" variant="primary" />
            </div>
          ) : rewardSummary ? (
            <Row className="g-3">
              <Col md={4}>
                <div className="border rounded p-3 text-center">
                  <div className="mb-2">
                    <i className="feather icon-book text-primary" style={{fontSize: '2rem'}}></i>
                  </div>
                  <h5>{rewardSummary.lesson_rewards || 0}</h5>
                  <p className="text-muted mb-0">Lesson Rewards</p>
                </div>
              </Col>
              <Col md={4}>
                <div className="border rounded p-3 text-center">
                  <div className="mb-2">
                    <i className="feather icon-award text-success" style={{fontSize: '2rem'}}></i>
                  </div>
                  <h5>{rewardSummary.course_rewards || 0}</h5>
                  <p className="text-muted mb-0">Course Rewards</p>
                </div>
              </Col>
              <Col md={4}>
                <div className="border rounded p-3 text-center">
                  <div className="mb-2">
                    <i className="feather icon-star text-warning" style={{fontSize: '2rem'}}></i>
                  </div>
                  <h5>{rewardSummary.achievement_rewards || 0}</h5>
                  <p className="text-muted mb-0">Achievement Rewards</p>
                </div>
              </Col>
            </Row>
          ) : (
            <div className="text-center py-3">
              <p className="text-muted mb-0">No reward data available</p>
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Reward Tools */}
      <Card className="mb-4">
        <Card.Header>
          <Card.Title className="d-flex align-items-center gap-2">
            <i className="feather icon-tool text-primary me-2"></i>
            Reward Tools
          </Card.Title>
        </Card.Header>
        <Card.Body>
          <Row className="g-3">
            <Col md={4}>
              <Form.Group className="mb-3">
                <Form.Label>Lesson ID</Form.Label>
                <Form.Control
                  type="text"
                  value={selectedLesson}
                  onChange={(e) => setSelectedLesson(e.target.value)}
                  placeholder="Enter lesson ID"
                />
              </Form.Group>
              <Button 
                variant="primary" 
                onClick={triggerLessonReward}
                disabled={loading || !selectedLesson}
                className="w-100"
              >
                <i className="feather icon-book me-2"></i>
                Trigger Lesson Reward
              </Button>
            </Col>

            <Col md={4}>
              <Form.Group className="mb-3">
                <Form.Label>Course ID</Form.Label>
                <Form.Control
                  type="text"
                  value={selectedCourse}
                  onChange={(e) => setSelectedCourse(e.target.value)}
                  placeholder="Enter course ID"
                />
              </Form.Group>
              <Button 
                variant="success" 
                onClick={triggerCourseCompletionCheck}
                disabled={loading || !selectedCourse}
                className="w-100"
              >
                <i className="feather icon-award me-2"></i>
                Check Course Completion
              </Button>
            </Col>

            <Col md={4}>
              <Form.Group className="mb-3">
                <Form.Label>Achievement Type</Form.Label>
                <Form.Select
                  value={achievementType}
                  onChange={(e) => setAchievementType(e.target.value)}
                >
                  <option value="">Select achievement type</option>
                  <option value="first_course">First Course</option>
                  <option value="first_exercise">First Exercise</option>
                  <option value="profile_complete">Profile Complete</option>
                  <option value="social_share">Social Share</option>
                </Form.Select>
              </Form.Group>
              <Button 
                variant="warning" 
                onClick={triggerAchievementReward}
                disabled={loading || !achievementType}
                className="w-100"
              >
                <i className="feather icon-star me-2"></i>
                Trigger Achievement
              </Button>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Transaction History (Coming Soon) */}
      <Card>
        <Card.Header>
          <Card.Title className="d-flex align-items-center gap-2">
            <i className="feather icon-list text-secondary me-2"></i>
            Reward History
          </Card.Title>
        </Card.Header>
        <Card.Body>
          <div className="text-center py-4">
            <Badge bg="secondary" className="px-3 py-2 mb-2">Coming Soon</Badge>
            <p className="text-muted mb-0">Transaction history will be available in a future update</p>
          </div>
        </Card.Body>
      </Card>
    </div>
  );
};

export default RewardSystem;

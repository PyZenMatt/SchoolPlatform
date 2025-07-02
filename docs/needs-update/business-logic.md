# Business Logic Documentation

## Overview

The TeoArt School Platform implements a comprehensive learning management system with an integrated blockchain-based reward system using TeoCoin.

## Core Business Rules

### User Management

#### User Roles
- **Students**: Can enroll in courses, submit exercises, earn TeoCoins
- **Teachers**: Can create courses/lessons, grade exercises (must be approved by admin)
- **Administrators**: Full platform access, can approve teachers, manage system

#### Teacher Approval Process
1. User registers with 'teacher' role
2. Account created with `is_approved = False`
3. Admin reviews and approves teacher accounts
4. Approved teachers can create and manage content

### Course Structure

#### Hierarchy
```
Course → Lessons → Exercises
```

#### Enrollment
- Students can enroll in courses
- Enrollment tracks progress and completion status
- Course completion requires all lessons to be completed

### TeoCoin Reward System

#### Earning TeoCoins
- **Lesson Completion**: 10 TeoCoins (configurable)
- **Exercise Submission**: 15 TeoCoins (configurable)
- **Course Completion**: 50 TeoCoins (configurable)
- **Achievements**: 25 TeoCoins (configurable)

#### Transaction Types
- `earned_lesson`: Automatic reward for lesson completion
- `earned_exercise`: Automatic reward for exercise submission
- `earned_course`: Automatic reward for course completion
- `transfer_sent/received`: User-to-user transfers
- `manual_reward`: Admin-issued rewards
- `bulk_reward`: Batch admin rewards

#### Budget Management
- Each course has a TeoCoin budget
- Rewards are distributed until budget is exhausted
- Prevents infinite reward exploitation

### Exercise Grading

#### Submission Workflow
1. Student submits exercise with files/text
2. Submission status: 'pending'
3. Teacher reviews and grades
4. Status changes to: 'approved', 'needs_revision', or 'rejected'
5. Student receives notification and TeoCoins (if approved)

#### Grading Criteria
- Teachers can provide feedback and scores
- Multiple submission attempts allowed for revisions
- Progress tracked at lesson and course level

### Progress Tracking

#### Lesson Progress
- Marked complete when user views lesson content
- Triggers TeoCoin reward (budget permitting)
- Updates course progress percentage

#### Course Progress
- Calculated based on completed lessons
- Course marked complete when all lessons finished
- Triggers course completion reward

### Achievement System

#### Achievement Types
- **Learning Milestones**: First lesson, first course, etc.
- **Streak Achievements**: Consecutive learning days
- **Mastery Achievements**: Complete multiple courses
- **Community Achievements**: Helping others, engagement
- **Time-based**: Early bird, night owl activities

#### Achievement Triggers
- Automatic detection based on user activity
- Manual admin assignment for special achievements
- One-time rewards per achievement type per user

### Notification System

#### Notification Types
- Exercise graded
- Course/lesson completion
- Achievement unlocked
- TeoCoin transactions
- System announcements

#### Delivery
- In-platform notifications
- Email notifications (configurable)
- Real-time updates via WebSocket

### Data Privacy and Security

#### User Data Protection
- Secure authentication with JWT tokens
- Password hashing using Django's built-in system
- File upload validation and sanitization
- CORS protection for API endpoints

#### Permission System
- Role-based access control
- API endpoint protection
- File access restrictions
- Admin-only functions clearly separated

### Blockchain Integration

#### TeoCoin Smart Contract
- ERC-20 compatible token
- Minting controlled by platform
- Transfer functionality
- Balance tracking

#### Web3 Integration
- MetaMask wallet connection
- Real-time balance synchronization
- Transaction history on blockchain
- Decentralized verification

## Performance Considerations

### Caching Strategy
- User profiles cached for 1 hour
- Course lists cached for 24 hours
- Lesson content cached for 24 hours
- TeoCoin balances cached for 5 minutes

### Database Optimization
- Proper indexing on frequently queried fields
- Pagination for large datasets
- Efficient queries with select_related/prefetch_related
- Regular database maintenance

### File Management
- Upload size limits (10MB default)
- File type validation
- Efficient storage with proper organization
- CDN integration for static assets

## Business Metrics

### Key Performance Indicators
- User engagement (lessons completed per day)
- Course completion rates
- TeoCoin circulation
- Teacher approval response time
- Student satisfaction scores

### Analytics Tracking
- User activity logging
- Learning path analysis
- Reward effectiveness measurement
- System performance monitoring

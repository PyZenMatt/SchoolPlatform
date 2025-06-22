# 🚀 Amoy TeoCoin Implementation Guide: Complete System Development

## 🎯 **YOUR CURRENT SITUATION** (ANALYZED)

✅ **What You Already Have:**
- **Django Backend** with Web3.py integration
- **TeoCoin2 Contract** deployed at `0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8`
- **React Frontend** with Ethers.js (not Web3.js)
- **Complete TeoCoin Service** in `blockchain/blockchain.py`
- **Frontend Web3 Service** in `frontend/src/services/api/web3Service.js`
- **Database Models** and migration system
- **Reward System** partially implemented

🔧 **What You Need to Complete:**
- **Auto-earning triggers** for courses, exercises, referrals
- **Real-time balance updates** and notifications
- **Complete user onboarding** flow
- **Error handling** and edge cases
- **Production deployment** setup

---

## 📋 **STEP-BY-STEP IMPLEMENTATION CHECKLIST**

### **PHASE 1: VERIFY YOUR CURRENT SETUP**

#### **1.1 Your Current TeoCoin Contract Analysis**
✅ **Contract: TeoCoin2 at `0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8`**

Based on your `teocoin_abi.py`, your contract has:
```
✅ CURRENT FEATURES:
├── ✅ Basic ERC-20 functionality (transfer, approve, balanceOf)
├── ✅ Platform minting capability (TokensMinted events)
├── ✅ Event emissions (Transfer, TokensMinted, Approval)
├── ✅ 18 decimals standard
└── ✅ Standard ERC-20 interface

🔍 MISSING FEATURES CHECK:
├── ❓ Role-based access control (need to verify)
├── ❓ Pausable functionality (need to verify)
├── ❓ platformMint function with reason parameter
├── ❓ Emergency functions
└── ❓ Upgrade proxy (need to verify)
```

**Let's verify what your contract actually has:**

#### **1.2 YOUR CONTRACT ANALYSIS RESULTS** ✅

🎉 **GREAT NEWS: Your TeoCoin2 is ready for implementation!**

**Contract:** `0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8`
**Total Supply:** 10,276.273 TEO (actively minted!)
**Status:** ✅ **PRODUCTION READY**

```
✅ ESSENTIAL FEATURES WORKING:
├── ✅ mint() function - for rewarding users
├── ✅ burn() function - for token management  
├── ✅ balanceOf() - for checking user balances
├── ✅ transfer() - for user-to-user transfers
├── ✅ TokensMinted events - for backend tracking
├── ✅ Admin system configured with reward pool
└── ✅ Polygon Amoy network integration

⚠️ MISSING ADVANCED FEATURES:
├── ❌ pause/unpause - emergency controls (optional)
├── ❌ hasRole/grantRole - advanced permissions (optional)
└── 💡 These are nice-to-have, not blockers!

🚀 IMPLEMENTATION STATUS: READY TO BUILD!
```

#### **1.3 IMMEDIATE IMPLEMENTATION FOCUS** 🎯

**Your setup is working! Let's focus on completing the user experience:**

```
� READY TO IMPLEMENT:

User Earning System:
├── ✅ Backend TeoCoin service working
├── ✅ Frontend Web3 service (Ethers.js) ready
├── ✅ Contract can mint rewards
├── 🔧 Need: Course completion triggers
├── 🔧 Need: Exercise submission rewards
├── 🔧 Need: Real-time notifications
└── 🔧 Need: Auto-balance updates

User Dashboard:
├── ✅ MetaMask integration exists
├── ✅ Amoy network switching ready
├── 🔧 Need: Complete dashboard UI
├── 🔧 Need: Transaction history
└── 🔧 Need: Earning opportunities display

Production Features:
├── 🔧 Need: Error handling improvements
├── 🔧 Need: Gas optimization
├── 🔧 Need: User onboarding flow
└── 🔧 Need: Testing & validation
```

**SKIP the contract upgrade section - your contract works perfectly!**

---

### **PHASE 2: BACKEND IMPLEMENTATION**

#### **2.1 Django Earning System Implementation**
**Build on your existing TeoCoinService - add earning triggers**

```python
# File: services/teo_earning_service.py
# This builds on your existing blockchain/blockchain.py

from django.conf import settings
from blockchain.blockchain import TeoCoinService
from courses.models import Course, Enrollment, Exercise, QuizSubmission
from users.models import User
from django.db import models
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class TeoEarning(models.Model):
    """Track all TEO earnings for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teo_earnings')
    earning_type = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    source_id = models.IntegerField(null=True, blank=True)  # course_id, exercise_id, etc.
    transaction_hash = models.CharField(max_length=66, null=True, blank=True)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'teo_earnings'

class TeoEarningService:
    """Enhanced earning service using your existing TeoCoinService"""
    
    # Earning rates - adjust these as needed
    EARNING_RATES = {
        'welcome_bonus': Decimal('20.0'),
        'course_completion': Decimal('0.10'),  # 10% of course price
        'exercise_submission': Decimal('2.0'),
        'quiz_perfect': Decimal('5.0'),
        'referral_student': Decimal('25.0'),
        'referral_teacher': Decimal('50.0'),
        'course_review': Decimal('10.0'),
        'weekly_streak': Decimal('15.0'),
        'monthly_streak': Decimal('50.0'),
    }
    
    def __init__(self):
        self.teo_service = TeoCoinService()
    
    def reward_course_completion(self, user_id: int, course_id: int) -> bool:
        """Reward user for completing a course"""
        try:
            user = User.objects.get(id=user_id)
            course = Course.objects.get(id=course_id)
            
            # Check if already rewarded
            existing = TeoEarning.objects.filter(
                user=user,
                earning_type='course_completion',
                source_id=course_id
            ).exists()
            
            if existing:
                logger.info(f"User {user_id} already rewarded for course {course_id}")
                return True
            
            # Calculate reward (10% of course price in TEO)
            teo_amount = course.price * self.EARNING_RATES['course_completion']
            
            # Get user's wallet address (you might have this in a different field)
            wallet_address = getattr(user, 'wallet_address', None) or getattr(user, 'amoy_address', None)
            
            if not wallet_address:
                logger.error(f"User {user_id} has no wallet address")
                return False
            
            # Mint TEO using your existing service
            tx_hash = self.teo_service.mint_tokens(
                to_address=wallet_address,
                amount=float(teo_amount),
                reason=f"Course completion: {course.title}"
            )
            
            # Record the earning
            TeoEarning.objects.create(
                user=user,
                earning_type='course_completion',
                amount=teo_amount,
                source_id=course_id,
                transaction_hash=tx_hash,
                reason=f"Completed course: {course.title}"
            )
            
            logger.info(f"Rewarded {teo_amount} TEO to user {user_id} for course {course_id}")
            
            # Send notification (implement this based on your notification system)
            self.send_earning_notification(user, teo_amount, 'course_completion', course.title)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to reward course completion: {e}")
            return False
    
    def reward_exercise_submission(self, user_id: int, exercise_id: int) -> bool:
        """Reward user for submitting an exercise"""
        try:
            user = User.objects.get(id=user_id)
            exercise = Exercise.objects.get(id=exercise_id)
            
            # Check if already rewarded for this exercise
            existing = TeoEarning.objects.filter(
                user=user,
                earning_type='exercise_submission',
                source_id=exercise_id
            ).exists()
            
            if existing:
                return True
            
            teo_amount = self.EARNING_RATES['exercise_submission']
            wallet_address = getattr(user, 'wallet_address', None) or getattr(user, 'amoy_address', None)
            
            if not wallet_address:
                logger.error(f"User {user_id} has no wallet address")
                return False
            
            # Mint TEO
            tx_hash = self.teo_service.mint_tokens(
                to_address=wallet_address,
                amount=float(teo_amount),
                reason=f"Exercise submission: {exercise.title}"
            )
            
            # Record earning
            TeoEarning.objects.create(
                user=user,
                earning_type='exercise_submission',
                amount=teo_amount,
                source_id=exercise_id,
                transaction_hash=tx_hash,
                reason=f"Submitted exercise: {exercise.title}"
            )
            
            self.send_earning_notification(user, teo_amount, 'exercise_submission', exercise.title)
            return True
            
        except Exception as e:
            logger.error(f"Failed to reward exercise submission: {e}")
            return False
    
    def give_welcome_bonus(self, user_id: int) -> bool:
        """Give one-time welcome bonus"""
        try:
            user = User.objects.get(id=user_id)
            
            # Check if already received
            existing = TeoEarning.objects.filter(
                user=user,
                earning_type='welcome_bonus'
            ).exists()
            
            if existing:
                return True
            
            wallet_address = getattr(user, 'wallet_address', None) or getattr(user, 'amoy_address', None)
            
            if not wallet_address:
                logger.error(f"User {user_id} has no wallet address for welcome bonus")
                return False
            
            teo_amount = self.EARNING_RATES['welcome_bonus']
            
            # Mint welcome TEO
            tx_hash = self.teo_service.mint_tokens(
                to_address=wallet_address,
                amount=float(teo_amount),
                reason="Welcome to SchoolPlatform!"
            )
            
            # Record earning
            TeoEarning.objects.create(
                user=user,
                earning_type='welcome_bonus',
                amount=teo_amount,
                source_id=None,
                transaction_hash=tx_hash,
                reason="Welcome bonus for joining SchoolPlatform"
            )
            
            self.send_earning_notification(user, teo_amount, 'welcome_bonus', "Welcome!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to give welcome bonus: {e}")
            return False
    
    def send_earning_notification(self, user, amount, earning_type, context):
        """Send notification to user about TEO earning"""
        # Implement based on your notification system
        # Could be email, websocket, push notification, etc.
        
        message = f"🎉 You earned {amount} TEO for {context}!"
        
        # Example: if you have a notification system
        # from notifications.models import Notification
        # Notification.objects.create(
        #     user=user,
        #     message=message,
        #     notification_type='teo_earned'
        # )
        
        logger.info(f"Notification sent to {user.username}: {message}")

# Service instance
teo_earning_service = TeoEarningService()
```

#### **2.2 Django Signals for Auto-Earning**
**Hook earning triggers into your existing course/exercise system**

```python
# File: courses/signals.py
# Add earning triggers to your existing course completion logic

from django.db.models.signals import post_save
from django.dispatch import receiver
from courses.models import Enrollment, ExerciseSubmission, QuizSubmission
from services.teo_earning_service import teo_earning_service
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Enrollment)
def handle_course_enrollment(sender, instance, created, **kwargs):
    """Trigger welcome bonus when user enrolls in first course"""
    if created:
        # Check if this is user's first enrollment
        user_enrollment_count = Enrollment.objects.filter(user=instance.user).count()
        
        if user_enrollment_count == 1:
            # Give welcome bonus for first course enrollment
            logger.info(f"Giving welcome bonus to new user: {instance.user.username}")
            teo_earning_service.give_welcome_bonus(instance.user.id)

@receiver(post_save, sender=Enrollment)
def handle_course_completion(sender, instance, **kwargs):
    """Trigger TEO reward when course is completed"""
    if instance.completed and instance.completion_date:
        # Check if this completion is new (not already rewarded)
        logger.info(f"Course completed: User {instance.user.username}, Course {instance.course.title}")
        teo_earning_service.reward_course_completion(instance.user.id, instance.course.id)

@receiver(post_save, sender=ExerciseSubmission)
def handle_exercise_submission(sender, instance, created, **kwargs):
    """Trigger TEO reward when exercise is submitted"""
    if created:
        logger.info(f"Exercise submitted: User {instance.user.username}, Exercise {instance.exercise.title}")
        teo_earning_service.reward_exercise_submission(instance.user.id, instance.exercise.id)

@receiver(post_save, sender=QuizSubmission)
def handle_quiz_completion(sender, instance, created, **kwargs):
    """Trigger bonus TEO for perfect quiz scores"""
    if created and instance.score == 100:
        logger.info(f"Perfect quiz score: User {instance.user.username}, Quiz {instance.quiz.title}")
        # You can implement quiz perfect score bonus here
        # teo_earning_service.reward_perfect_quiz(instance.user.id, instance.quiz.id)

# Add to your courses/apps.py to register signals:
"""
from django.apps import AppConfig

class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses'
    
    def ready(self):
        import courses.signals  # Import signals
"""
```
#### **2.3 Django Management Commands for Testing**
**Easy testing of your earning system**

```python
# File: courses/management/commands/test_teo_earnings.py

from django.core.management.base import BaseCommand
from users.models import User
from courses.models import Course, Enrollment, Exercise, ExerciseSubmission
from services.teo_earning_service import teo_earning_service
from blockchain.blockchain import TeoCoinService

class Command(BaseCommand):
    help = 'Test TEO earning system with sample data'
    
    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=int, help='User ID to test with')
        parser.add_argument('--course-id', type=int, help='Course ID to test with')
        parser.add_argument('--exercise-id', type=int, help='Exercise ID to test with')
        parser.add_argument('--check-balance', action='store_true', help='Check user TEO balance')
        parser.add_argument('--welcome-bonus', action='store_true', help='Give welcome bonus')
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Testing TEO Earning System'))
        
        # Test blockchain connection
        try:
            teo_service = TeoCoinService()
            if teo_service.w3.is_connected():
                self.stdout.write(self.style.SUCCESS('✅ Blockchain connection: OK'))
            else:
                self.stdout.write(self.style.ERROR('❌ Blockchain connection: FAILED'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Blockchain error: {e}'))
            return
        
        # Check user balance
        if options['check_balance'] and options['user_id']:
            try:
                user = User.objects.get(id=options['user_id'])
                wallet_address = getattr(user, 'wallet_address', None) or getattr(user, 'amoy_address', None)
                
                if wallet_address:
                    balance = teo_service.get_balance(wallet_address)
                    self.stdout.write(f"💰 User {user.username} TEO balance: {balance}")
                else:
                    self.stdout.write(f"⚠️  User {user.username} has no wallet address")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ User {options["user_id"]} not found'))
        
        # Test welcome bonus
        if options['welcome_bonus'] and options['user_id']:
            try:
                success = teo_earning_service.give_welcome_bonus(options['user_id'])
                if success:
                    self.stdout.write(self.style.SUCCESS(f'✅ Welcome bonus given to user {options["user_id"]}'))
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Failed to give welcome bonus'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Welcome bonus error: {e}'))
        
        # Test course completion reward
        if options['course_id'] and options['user_id']:
            try:
                success = teo_earning_service.reward_course_completion(
                    options['user_id'], 
                    options['course_id']
                )
                if success:
                    self.stdout.write(self.style.SUCCESS(f'✅ Course completion reward given'))
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Failed to give course completion reward'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Course completion error: {e}'))
        
        # Test exercise submission reward
        if options['exercise_id'] and options['user_id']:
            try:
                success = teo_earning_service.reward_exercise_submission(
                    options['user_id'], 
                    options['exercise_id']
                )
                if success:
                    self.stdout.write(self.style.SUCCESS(f'✅ Exercise submission reward given'))
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Failed to give exercise submission reward'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Exercise submission error: {e}'))
        
        self.stdout.write(self.style.SUCCESS('✨ TEO earning system test complete!'))

# Usage examples:
# python manage.py test_teo_earnings --user-id 1 --check-balance
# python manage.py test_teo_earnings --user-id 1 --welcome-bonus
# python manage.py test_teo_earnings --user-id 1 --course-id 1
# python manage.py test_teo_earnings --user-id 1 --exercise-id 1
```

#### **2.3 TEO Earning System**
```typescript
// File: services/teo-earning.service.ts

export class TeoEarningService {
    private blockchainService: AmoyBlockchainService;
    
    // Define earning rates
    private static readonly EARNING_RATES = {
        WELCOME_BONUS: 20,              // One-time welcome
        COURSE_PURCHASE: 0.05,          // 5% of course price in TEO
        COURSE_COMPLETION: 0.10,        // 10% of course price in TEO
        EXERCISE_SUBMISSION: 2,         // 2 TEO per exercise
        QUIZ_PERFECT_SCORE: 5,          // 5 TEO bonus for perfect score
        REFERRAL_STUDENT: 25,           // 25 TEO per student referral
        REFERRAL_TEACHER: 50,           // 50 TEO per teacher referral
        WEEKLY_STREAK: 15,              // 15 TEO for 7-day learning streak
        MONTHLY_STREAK: 50,             // 50 TEO for 30-day learning streak
        COURSE_REVIEW: 10,              // 10 TEO for detailed course review
        FORUM_HELP: 3,                  // 3 TEO per helpful forum answer
    };
    
    constructor() {
        this.blockchainService = new AmoyBlockchainService();
    }
    
    // Handle course completion reward
    async rewardCourseCompletion(userId: number, courseId: number): Promise<void> {
        try {
            const user = await User.findByPk(userId);
            const course = await Course.findByPk(courseId);
            
            if (!user || !course) {
                throw new Error('User or course not found');
            }
            
            // Calculate TEO reward
            const teoAmount = course.price * this.EARNING_RATES.COURSE_COMPLETION;
            
            // Mint TEO to user
            const txHash = await this.blockchainService.mintTeoToUser(
                user.amoy_address,
                teoAmount,
                `Course completion: ${course.title}`
            );
            
            // Record in database
            await TeoEarning.create({
                user_id: userId,
                earning_type: 'course_completion',
                amount: teoAmount,
                source_id: courseId,
                transaction_hash: txHash
            });
            
            // Send notification
            await this.sendEarningNotification(user, teoAmount, 'course_completion', course.title);
            
        } catch (error) {
            console.error('Course completion reward failed:', error);
            throw error;
        }
    }
    
    // Handle exercise submission reward
    async rewardExerciseSubmission(userId: number, exerciseId: number): Promise<void> {
        const user = await User.findByPk(userId);
        const exercise = await Exercise.findByPk(exerciseId);
        
        if (!user?.amoy_address) {
            throw new Error('User has no Amoy address');
        }
        
        let teoAmount = this.EARNING_RATES.EXERCISE_SUBMISSION;
        
        // Quality bonus calculation
        const submissionQuality = await this.assessSubmissionQuality(exerciseId);
        if (submissionQuality === 'excellent') {
            teoAmount *= 1.5; // 50% bonus for excellent submissions
        } else if (submissionQuality === 'good') {
            teoAmount *= 1.2; // 20% bonus for good submissions
        }
        
        const txHash = await this.blockchainService.mintTeoToUser(
            user.amoy_address,
            teoAmount,
            `Exercise submission: ${exercise.title}`
        );
        
        await TeoEarning.create({
            user_id: userId,
            earning_type: 'exercise_submission',
            amount: teoAmount,
            source_id: exerciseId,
            transaction_hash: txHash
        });
    }
    
    // Welcome bonus for new users
    async giveWelcomeBonus(userId: number): Promise<void> {
        const user = await User.findByPk(userId);
        
        if (!user?.amoy_address) {
            throw new Error('User needs Amoy wallet setup first');
        }
        
        // Check if already received welcome bonus
        const existingBonus = await TeoEarning.findOne({
            where: {
                user_id: userId,
                earning_type: 'welcome_bonus'
            }
        });
        
        if (existingBonus) {
            return; // Already received
        }
        
        const teoAmount = this.EARNING_RATES.WELCOME_BONUS;
        
        const txHash = await this.blockchainService.mintTeoToUser(
            user.amoy_address,
            teoAmount,
            'Welcome to SchoolPlatform!'
        );
        
        await TeoEarning.create({
            user_id: userId,
            earning_type: 'welcome_bonus',
            amount: teoAmount,
            source_id: null,
            transaction_hash: txHash
        });
        
        await this.sendWelcomeNotification(user, teoAmount);
    }
    
    // Auto-trigger earning events
    async setupEarningTriggers(): Promise<void> {
        // Hook into existing platform events
        
        // Course completion trigger
        EventEmitter.on('course:completed', async (data) => {
            await this.rewardCourseCompletion(data.userId, data.courseId);
        });
        
        // Exercise submission trigger
        EventEmitter.on('exercise:submitted', async (data) => {
            await this.rewardExerciseSubmission(data.userId, data.exerciseId);
        });
        
        // Quiz completion trigger
        EventEmitter.on('quiz:completed', async (data) => {
            if (data.score === 100) {
                await this.rewardPerfectQuiz(data.userId, data.quizId);
            }
        });
        
        // User registration trigger
        EventEmitter.on('user:registered', async (data) => {
            // Wait for wallet setup, then give welcome bonus
            setTimeout(async () => {
                await this.giveWelcomeBonus(data.userId);
            }, 5000);
        });
    }
    
    private async assessSubmissionQuality(exerciseId: number): Promise<string> {
        // Implement your quality assessment logic
        // Could be based on: completion time, correctness, effort, etc.
        // Return: 'excellent', 'good', 'average', 'poor'
        return 'good'; // Placeholder
    }
    
    private async sendEarningNotification(user: any, amount: number, type: string, context: string): Promise<void> {
        // Send real-time notification
        io.to(`user_${user.id}`).emit('teo_earned', {
            amount,
            type,
            context,
            balance: await this.blockchainService.getUserBalance(user.amoy_address)
        });
        
        // Send email notification
        await EmailService.send({
            to: user.email,
            subject: `🎉 You earned ${amount} TEO!`,
            template: 'teo_earned',
            data: { user, amount, type, context }
        });
    }
}
```

---

### **PHASE 3: FRONTEND IMPLEMENTATION**

### **PHASE 3: REACT FRONTEND COMPLETION**

#### **3.1 Enhance Your Existing Web3Service**
**Build on your current `frontend/src/services/api/web3Service.js`**

```javascript
// Add to your existing web3Service.js file
// This extends your current TeoCoin integration

class Web3Service {
  // ...your existing constructor and methods...

  /**
   * Get user's TEO balance and update UI
   */
  async getTeoBalance() {
    try {
      if (!this.contract || !this.userAddress) {
        console.warn('Contract or user address not available');
        return 0;
      }

      const balance = await this.contract.balanceOf(this.userAddress);
      const formattedBalance = parseFloat(ethers.formatEther(balance));
      
      // Emit event for components to react
      window.dispatchEvent(new CustomEvent('teo:balanceUpdated', {
        detail: { balance: formattedBalance, address: this.userAddress }
      }));
      
      return formattedBalance;
    } catch (error) {
      console.error('Failed to get TEO balance:', error);
      return 0;
    }
  }

  /**
   * Watch for incoming TEO transactions (mints from rewards)
   */
  async startBalanceWatcher() {
    if (!this.contract || !this.userAddress) return;

    try {
      // Listen for Transfer events TO this user (rewards)
      const transferFilter = this.contract.filters.Transfer(null, this.userAddress);
      
      this.contract.on(transferFilter, (from, to, amount, event) => {
        const teoAmount = parseFloat(ethers.formatEther(amount));
        
        console.log(`🎉 Received ${teoAmount} TEO from ${from}`);
        
        // Update balance immediately
        this.getTeoBalance();
        
        // Emit earning event
        window.dispatchEvent(new CustomEvent('teo:earned', {
          detail: {
            amount: teoAmount,
            from: from,
            transactionHash: event.transactionHash,
            timestamp: new Date()
          }
        }));
      });

      // Listen for TokensMinted events specifically
      const mintFilter = this.contract.filters.TokensMinted(this.userAddress);
      
      this.contract.on(mintFilter, (mintedTo, quantityMinted, event) => {
        const teoAmount = parseFloat(ethers.formatEther(quantityMinted));
        
        console.log(`🪙 Minted ${teoAmount} TEO to your account!`);
        
        // Show notification
        this.showTeoEarningNotification(teoAmount, 'Platform Reward');
        
        // Update balance
        this.getTeoBalance();
      });

      console.log('✅ TEO balance watcher started');
    } catch (error) {
      console.error('Failed to start balance watcher:', error);
    }
  }

  /**
   * Show TEO earning notification
   */
  showTeoEarningNotification(amount, reason) {
    // Create a nice notification
    const notification = {
      type: 'teo_earned',
      title: '🎉 TEO Earned!',
      message: `You received ${amount} TEO for ${reason}`,
      amount: amount,
      timestamp: new Date()
    };

    // Emit notification event
    window.dispatchEvent(new CustomEvent('notification:show', {
      detail: notification
    }));

    // Store in localStorage for persistence
    const notifications = JSON.parse(localStorage.getItem('teo_notifications') || '[]');
    notifications.unshift(notification);
    notifications.splice(10); // Keep only last 10
    localStorage.setItem('teo_notifications', JSON.stringify(notifications));
  }

  /**
   * Get user's TEO earning history from backend
   */
  async getTeoEarningsHistory() {
    try {
      const response = await fetch('/api/teo/earnings-history/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        return await response.json();
      } else {
        console.error('Failed to fetch earnings history');
        return [];
      }
    } catch (error) {
      console.error('Error fetching earnings history:', error);
      return [];
    }
  }

  /**
   * Save user's wallet address to backend
   */
  async saveWalletAddress() {
    if (!this.userAddress) return;

    try {
      const response = await fetch('/api/users/wallet/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          amoy_address: this.userAddress
        })
      });

      if (response.ok) {
        console.log('✅ Wallet address saved to backend');
        
        // Check for welcome bonus
        await this.checkWelcomeBonus();
      } else {
        console.error('Failed to save wallet address');
      }
    } catch (error) {
      console.error('Error saving wallet address:', error);
    }
  }

  /**
   * Check and trigger welcome bonus
   */
  async checkWelcomeBonus() {
    try {
      const response = await fetch('/api/teo/welcome-bonus/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        if (result.bonus_given) {
          this.showTeoEarningNotification(result.amount, 'Welcome Bonus');
        }
      }
    } catch (error) {
      console.error('Error checking welcome bonus:', error);
    }
  }

  // Enhance your existing connectToAmoy method
  async connectToAmoy() {
    // ...your existing connectToAmoy logic...
    
    // After successful connection, add these:
    await this.saveWalletAddress();
    await this.startBalanceWatcher();
    await this.getTeoBalance();
  }
}

// Export enhanced service
export default new Web3Service();
```

#### **3.2 React TEO Dashboard Component**
**Create a modern dashboard that works with your setup**

```jsx
// File: frontend/src/components/TeoCoinDashboard.jsx

import React, { useState, useEffect } from 'react';
import { Card, Button, Alert, Badge, Spinner } from 'react-bootstrap';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import Web3Service from '../services/api/web3Service';

const TeoCoinDashboard = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [userAddress, setUserAddress] = useState('');
  const [teoBalance, setTeoBalance] = useState(0);
  const [earningsHistory, setEarningsHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    setupEventListeners();
    checkExistingConnection();
    loadNotifications();
    
    return () => {
      cleanup();
    };
  }, []);

  const setupEventListeners = () => {
    // TEO balance updates
    window.addEventListener('teo:balanceUpdated', handleBalanceUpdate);
    
    // TEO earning events
    window.addEventListener('teo:earned', handleTeoEarned);
    
    // Notifications
    window.addEventListener('notification:show', handleNotification);
    
    // Wallet events
    window.addEventListener('wallet:accountChanged', handleAccountChanged);
    window.addEventListener('wallet:disconnected', handleDisconnected);
  };

  const cleanup = () => {
    window.removeEventListener('teo:balanceUpdated', handleBalanceUpdate);
    window.removeEventListener('teo:earned', handleTeoEarned);
    window.removeEventListener('notification:show', handleNotification);
    window.removeEventListener('wallet:accountChanged', handleAccountChanged);
    window.removeEventListener('wallet:disconnected', handleDisconnected);
  };

  const checkExistingConnection = async () => {
    try {
      if (Web3Service.userAddress) {
        setIsConnected(true);
        setUserAddress(Web3Service.userAddress);
        await loadDashboardData();
      }
    } catch (error) {
      console.log('No existing connection');
    }
  };

  const connectWallet = async () => {
    setLoading(true);
    setError('');

    try {
      await Web3Service.connectToAmoy();
      setIsConnected(true);
      setUserAddress(Web3Service.userAddress);
      await loadDashboardData();
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const loadDashboardData = async () => {
    try {
      // Load TEO balance
      const balance = await Web3Service.getTeoBalance();
      setTeoBalance(balance);

      // Load earnings history
      const history = await Web3Service.getTeoEarningsHistory();
      setEarningsHistory(history);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  };

  const loadNotifications = () => {
    const saved = JSON.parse(localStorage.getItem('teo_notifications') || '[]');
    setNotifications(saved);
  };

  const handleBalanceUpdate = (event) => {
    setTeoBalance(event.detail.balance);
  };

  const handleTeoEarned = (event) => {
    const { amount, transactionHash } = event.detail;
    
    // Show success message
    setNotifications(prev => [{
      type: 'success',
      title: '🎉 TEO Earned!',
      message: `You received ${amount} TEO`,
      timestamp: new Date(),
      transactionHash
    }, ...prev.slice(0, 9)]);
    
    // Refresh data
    loadDashboardData();
  };

  const handleNotification = (event) => {
    setNotifications(prev => [event.detail, ...prev.slice(0, 9)]);
  };

  const handleAccountChanged = (event) => {
    setUserAddress(event.detail.address);
    loadDashboardData();
  };

  const handleDisconnected = () => {
    setIsConnected(false);
    setUserAddress('');
    setTeoBalance(0);
    setEarningsHistory([]);
  };

  const clearNotifications = () => {
    setNotifications([]);
    localStorage.removeItem('teo_notifications');
  };

  if (!isConnected) {
    return (
      <Card className="text-center p-4">
        <Card.Body>
          <h2 className="mb-3">🪙 Connect Your Wallet</h2>
          <p className="text-muted mb-4">
            Connect your MetaMask wallet to start earning TeoCoin rewards
          </p>
          
          {error && (
            <Alert variant="danger" className="mb-3">
              {error}
            </Alert>
          )}
          
          <Button 
            variant="primary" 
            size="lg"
            onClick={connectWallet}
            disabled={loading}
            className="mb-3"
          >
            {loading ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Connecting...
              </>
            ) : (
              'Connect MetaMask'
            )}
          </Button>
          
          <div className="mt-3 text-muted small">
            <div>🔗 Network: Polygon Amoy Testnet</div>
            <div>🪙 Token: TeoCoin (TEO)</div>
          </div>
        </Card.Body>
      </Card>
    );
  }

  return (
    <div className="teo-dashboard">
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="h3 mb-0">🪙 TeoCoin Dashboard</h1>
        <div className="d-flex align-items-center gap-2">
          <Badge bg="success">Connected</Badge>
          <code className="text-muted">
            {userAddress.slice(0, 6)}...{userAddress.slice(-4)}
          </code>
        </div>
      </div>

      {/* Balance Card */}
      <Card className="mb-4">
        <Card.Body>
          <div className="row align-items-center">
            <div className="col-md-6">
              <h5 className="card-title">Current Balance</h5>
              <div className="display-4 text-primary mb-2">
                {teoBalance.toFixed(2)} <small className="text-muted">TEO</small>
              </div>
              <div className="text-muted">
                ≈ €{(teoBalance * 0.5).toFixed(2)} <small>(estimated value)</small>
              </div>
            </div>
            <div className="col-md-6">
              <div className="text-end">
                <Button 
                  variant="outline-primary" 
                  onClick={loadDashboardData}
                  size="sm"
                >
                  🔄 Refresh
                </Button>
              </div>
            </div>
          </div>
        </Card.Body>
      </Card>

      {/* Earning Opportunities */}
      <Card className="mb-4">
        <Card.Header>
          <h5 className="mb-0">🎯 Earn More TEO</h5>
        </Card.Header>
        <Card.Body>
          <div className="row g-3">
            <div className="col-md-6 col-lg-3">
              <div className="p-3 border rounded text-center">
                <div className="h2">📚</div>
                <div className="fw-bold">Complete Course</div>
                <div className="text-success small">+10% of price</div>
              </div>
            </div>
            <div className="col-md-6 col-lg-3">
              <div className="p-3 border rounded text-center">
                <div className="h2">✏️</div>
                <div className="fw-bold">Submit Exercise</div>
                <div className="text-success small">+2 TEO</div>
              </div>
            </div>
            <div className="col-md-6 col-lg-3">
              <div className="p-3 border rounded text-center">
                <div className="h2">🎯</div>
                <div className="fw-bold">Perfect Quiz</div>
                <div className="text-success small">+5 TEO</div>
              </div>
            </div>
            <div className="col-md-6 col-lg-3">
              <div className="p-3 border rounded text-center">
                <div className="h2">👥</div>
                <div className="fw-bold">Refer Friend</div>
                <div className="text-success small">+25 TEO</div>
              </div>
            </div>
          </div>
        </Card.Body>
      </Card>

      {/* Recent Activity */}
      <div className="row">
        <div className="col-md-8">
          <Card>
            <Card.Header>
              <h5 className="mb-0">📊 Earnings History</h5>
            </Card.Header>
            <Card.Body>
              {earningsHistory.length > 0 ? (
                <div className="list-group list-group-flush">
                  {earningsHistory.slice(0, 10).map((earning, index) => (
                    <div key={index} className="list-group-item d-flex justify-content-between align-items-center">
                      <div>
                        <div className="fw-bold">{getEarningIcon(earning.earning_type)} {earning.reason}</div>
                        <div className="text-muted small">
                          {new Date(earning.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="text-end">
                        <div className="text-success fw-bold">+{earning.amount} TEO</div>
                        {earning.transaction_hash && (
                          <a 
                            href={`https://amoy.polygonscan.com/tx/${earning.transaction_hash}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-muted small"
                          >
                            View on Explorer
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-muted p-4">
                  <div className="h1">🎁</div>
                  <div>Start earning TEO by completing courses and exercises!</div>
                </div>
              )}
            </Card.Body>
          </Card>
        </div>

        <div className="col-md-4">
          <Card>
            <Card.Header className="d-flex justify-content-between align-items-center">
              <h5 className="mb-0">🔔 Recent Activity</h5>
              {notifications.length > 0 && (
                <Button variant="outline-secondary" size="sm" onClick={clearNotifications}>
                  Clear
                </Button>
              )}
            </Card.Header>
            <Card.Body>
              {notifications.length > 0 ? (
                <div className="list-group list-group-flush">
                  {notifications.slice(0, 5).map((notification, index) => (
                    <div key={index} className="list-group-item border-0 px-0">
                      <div className="d-flex align-items-start gap-2">
                        <div className="flex-shrink-0">
                          {notification.type === 'teo_earned' ? '🎉' : '📝'}
                        </div>
                        <div className="flex-grow-1 small">
                          <div className="fw-bold">{notification.title}</div>
                          <div className="text-muted">{notification.message}</div>
                          <div className="text-muted small">
                            {new Date(notification.timestamp).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-muted p-3">
                  <div>No recent activity</div>
                </div>
              )}
            </Card.Body>
          </Card>
        </div>
      </div>
    </div>
  );
};

// Helper function for earning type icons
const getEarningIcon = (type) => {
  const icons = {
    'welcome_bonus': '🎉',
    'course_completion': '🎓',
    'exercise_submission': '✏️',
    'quiz_perfect': '🎯',
    'referral_student': '👥',
    'referral_teacher': '👨‍🏫',
    'course_review': '⭐',
    'weekly_streak': '🔥',
    'monthly_streak': '💎'
  };
  return icons[type] || '💰';
};

export default TeoCoinDashboard;
```
```tsx
// File: frontend/components/TeoCoinDashboard.tsx

import React, { useState, useEffect } from 'react';
import { WalletService } from '../services/wallet.service';

interface TeoStats {
    balance: number;
    totalEarned: number;
    recentTransactions: Transaction[];
    stakingTier: number;
    nextTierRequirement: number;
}

export const TeoCoinDashboard: React.FC = () => {
    const [walletService] = useState(new WalletService());
    const [isConnected, setIsConnected] = useState(false);
    const [userAddress, setUserAddress] = useState<string>('');
    const [teoStats, setTeoStats] = useState<TeoStats | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string>('');
    
    useEffect(() => {
        setupEventListeners();
        checkExistingConnection();
    }, []);
    
    const setupEventListeners = () => {
        window.addEventListener('wallet:accountChanged', handleAccountChanged);
        window.addEventListener('wallet:disconnected', handleDisconnected);
        window.addEventListener('wallet:wrongNetwork', handleWrongNetwork);
        window.addEventListener('teo_earned', handleTeoEarned);
        
        return () => {
            window.removeEventListener('wallet:accountChanged', handleAccountChanged);
            window.removeEventListener('wallet:disconnected', handleDisconnected);
            window.removeEventListener('wallet:wrongNetwork', handleWrongNetwork);
            window.removeEventListener('teo_earned', handleTeoEarned);
        };
    };
    
    const checkExistingConnection = async () => {
        // Check if already connected
        if (window.ethereum && window.ethereum.selectedAddress) {
            try {
                const address = await walletService.connectWallet();
                setIsConnected(true);
                setUserAddress(address);
                await loadTeoStats();
            } catch (error) {
                console.log('Auto-connection failed:', error);
            }
        }
    };
    
    const connectWallet = async () => {
        setLoading(true);
        setError('');
        
        try {
            const address = await walletService.connectWallet();
            setIsConnected(true);
            setUserAddress(address);
            
            // Save address to backend
            await saveUserAddress(address);
            
            // Load user stats
            await loadTeoStats();
            
            // Give welcome bonus if new user
            await checkWelcomeBonus();
            
        } catch (error: any) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };
    
    const loadTeoStats = async () => {
        try {
            const [balance, stats] = await Promise.all([
                walletService.getBalance(),
                fetch('/api/teo/stats').then(r => r.json())
            ]);
            
            setTeoStats({
                balance,
                totalEarned: stats.totalEarned,
                recentTransactions: stats.recentTransactions,
                stakingTier: stats.stakingTier,
                nextTierRequirement: stats.nextTierRequirement
            });
        } catch (error) {
            console.error('Failed to load TEO stats:', error);
        }
    };
    
    const saveUserAddress = async (address: string) => {
        try {
            await fetch('/api/user/wallet', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amoyAddress: address })
            });
        } catch (error) {
            console.error('Failed to save wallet address:', error);
        }
    };
    
    const checkWelcomeBonus = async () => {
        try {
            await fetch('/api/teo/welcome-bonus', { method: 'POST' });
        } catch (error) {
            console.error('Welcome bonus check failed:', error);
        }
    };
    
    const handleAccountChanged = (event: any) => {
        setUserAddress(event.detail.address);
        loadTeoStats();
    };
    
    const handleDisconnected = () => {
        setIsConnected(false);
        setUserAddress('');
        setTeoStats(null);
    };
    
    const handleWrongNetwork = (event: any) => {
        setError(`Please switch to ${event.detail.expectedNetwork}`);
    };
    
    const handleTeoEarned = (event: any) => {
        const { amount, type, context } = event.detail;
        
        // Show notification
        showNotification(`🎉 You earned ${amount} TEO for ${context}!`);
        
        // Refresh stats
        loadTeoStats();
    };
    
    if (!isConnected) {
        return (
            <div className="teo-dashboard-connection">
                <div className="connection-card">
                    <h2>Connect Your Wallet</h2>
                    <p>Connect your MetaMask wallet to start earning TeoCoin</p>
                    
                    {error && (
                        <div className="error-message">
                            {error}
                        </div>
                    )}
                    
                    <button 
                        onClick={connectWallet}
                        disabled={loading}
                        className="connect-button"
                    >
                        {loading ? 'Connecting...' : 'Connect MetaMask'}
                    </button>
                    
                    <div className="network-info">
                        <p>🔗 Network: Polygon Amoy Testnet</p>
                        <p>🪙 Token: TeoCoin (TEO)</p>
                    </div>
                </div>
            </div>
        );
    }
    
    return (
        <div className="teo-dashboard">
            <div className="dashboard-header">
                <h1>🪙 Your TeoCoin Dashboard</h1>
                <div className="wallet-info">
                    <span>Connected: {userAddress.slice(0, 6)}...{userAddress.slice(-4)}</span>
                    <span className="network-badge">Amoy Testnet</span>
                </div>
            </div>
            
            {teoStats && (
                <div className="dashboard-content">
                    <div className="stats-grid">
                        <div className="stat-card balance-card">
                            <h3>Current Balance</h3>
                            <div className="balance-amount">
                                {teoStats.balance.toFixed(2)} TEO
                            </div>
                            <div className="balance-usd">
                                ≈ €{(teoStats.balance * 0.5).toFixed(2)}
                            </div>
                        </div>
                        
                        <div className="stat-card earnings-card">
                            <h3>Total Earned</h3>
                            <div className="earnings-amount">
                                {teoStats.totalEarned.toFixed(2)} TEO
                            </div>
                            <div className="earnings-count">
                                {teoStats.recentTransactions.length} transactions
                            </div>
                        </div>
                        
                        <div className="stat-card tier-card">
                            <h3>Staking Tier</h3>
                            <div className="tier-name">
                                {getTierName(teoStats.stakingTier)}
                            </div>
                            <div className="tier-progress">
                                Progress to next tier: {teoStats.nextTierRequirement} TEO needed
                            </div>
                        </div>
                    </div>
                    
                    <div className="earning-opportunities">
                        <h3>🎯 Earn More TEO</h3>
                        <div className="opportunities-grid">
                            <div className="opportunity">
                                <span className="opportunity-icon">📚</span>
                                <span className="opportunity-text">Complete a course</span>
                                <span className="opportunity-reward">+10% of course price</span>
                            </div>
                            <div className="opportunity">
                                <span className="opportunity-icon">✏️</span>
                                <span className="opportunity-text">Submit exercise</span>
                                <span className="opportunity-reward">+2 TEO</span>
                            </div>
                            <div className="opportunity">
                                <span className="opportunity-icon">🎯</span>
                                <span className="opportunity-text">Perfect quiz score</span>
                                <span className="opportunity-reward">+5 TEO</span>
                            </div>
                            <div className="opportunity">
                                <span className="opportunity-icon">👥</span>
                                <span className="opportunity-text">Refer a friend</span>
                                <span className="opportunity-reward">+25 TEO</span>
                            </div>
                        </div>
                    </div>
                    
                    <div className="recent-transactions">
                        <h3>📊 Recent Activity</h3>
                        <div className="transactions-list">
                            {teoStats.recentTransactions.map((tx, index) => (
                                <div key={index} className="transaction-item">
                                    <div className="transaction-icon">
                                        {getTransactionIcon(tx.type)}
                                    </div>
                                    <div className="transaction-details">
                                        <div className="transaction-description">
                                            {tx.description}
                                        </div>
                                        <div className="transaction-date">
                                            {formatDate(tx.date)}
                                        </div>
                                    </div>
                                    <div className="transaction-amount">
                                        +{tx.amount} TEO
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// Helper functions
const getTierName = (tier: number): string => {
    const tierNames = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond'];
    return tierNames[tier] || 'Bronze';
};

const getTransactionIcon = (type: string): string => {
    const icons = {
        'course_completion': '🎓',
        'exercise': '✏️',
        'quiz': '🎯',
        'referral': '👥',
        'welcome': '🎉',
        'review': '⭐'
    };
    return icons[type] || '💰';
};

const formatDate = (date: string): string => {
    return new Date(date).toLocaleDateString();
};

const showNotification = (message: string): void => {
    // Implement your notification system
    console.log('Notification:', message);
};
```

---

### **PHASE 4: TESTING & VALIDATION**

#### **4.1 Testing Checklist**
```bash
# Create comprehensive test suite

# 1. Smart Contract Tests
npm run test:contracts

# 2. Backend Service Tests
npm run test:backend

# 3. Frontend Integration Tests
npm run test:frontend

# 4. End-to-End User Journey Tests
npm run test:e2e
```

#### **4.2 Manual Testing Scenarios**
```
🧪 MANUAL TESTING SCENARIOS:

User Onboarding:
├── [ ] User registers account
├── [ ] User connects MetaMask
├── [ ] Amoy network auto-switch works
├── [ ] TEO token appears in MetaMask
├── [ ] Welcome bonus is received
└── [ ] Dashboard loads correctly

Earning TEO:
├── [ ] Course completion triggers TEO mint
├── [ ] Exercise submission rewards work
├── [ ] Quiz bonuses are calculated correctly
├── [ ] Referral rewards are given
├── [ ] Real-time notifications work
└── [ ] Balance updates immediately

Transaction Monitoring:
├── [ ] All transactions appear in dashboard
├── [ ] Transaction hashes link to Amoy explorer
├── [ ] Failed transactions are handled gracefully
├── [ ] Gas fees are optimized
└── [ ] Event listeners work correctly

Error Handling:
├── [ ] MetaMask not installed
├── [ ] Wrong network detection
├── [ ] Insufficient gas
├── [ ] Contract interaction failures
└── [ ] Network connectivity issues
```

---

### **PHASE 5: PRODUCTION READINESS**

#### **5.1 Security Checklist**
```
🔒 SECURITY REQUIREMENTS:

Smart Contract Security:
├── [ ] Access controls implemented
├── [ ] Rate limiting on minting
├── [ ] Emergency pause functionality
├── [ ] Multi-signature for admin functions
├── [ ] Upgrade proxy protection
└── [ ] External audit completed

Backend Security:
├── [ ] Private key secure storage
├── [ ] API rate limiting
├── [ ] Input validation
├── [ ] SQL injection protection
├── [ ] XSS protection
└── [ ] CORS configuration

Frontend Security:
├── [ ] No private keys in client code
├── [ ] Secure communication with backend
├── [ ] Input sanitization
├── [ ] CSP headers
└── [ ] Environment variable protection
```

#### **5.2 Deployment Preparation**
```bash
# Production deployment checklist

# 1. Environment Configuration
cp .env.example .env.production
# Fill in production values:
# - Amoy/Polygon RPC URLs
# - Contract addresses
# - Database credentials
# - API keys

# 2. Database Migration
npm run migrate:production

# 3. Contract Verification
npm run verify:contracts

# 4. Performance Testing
npm run test:performance

# 5. Load Testing
npm run test:load

# 6. Monitoring Setup
npm run setup:monitoring
```

---

## 🚀 **NEXT STEPS FOR YOU**

Based on your current situation, here's what I recommend you work on next:

### **Immediate Actions (This Week):**
1. **Audit your current TeoCoin contract** - check if it has all needed functions
2. **Set up the backend blockchain service** - start with the AmoyBlockchainService
3. **Create the basic earning system** - implement course completion rewards
4. **Test MetaMask integration** - ensure Amoy network switching works

### **Short Term (Next 2-3 Weeks):**
1. **Complete the earning system** - all types of rewards
2. **Build the TeoCoin dashboard** - user-facing interface
3. **Implement transaction monitoring** - real-time updates
4. **Add comprehensive error handling**

### **Medium Term (Next Month):**
1. **Add staking functionality** (if needed)
2. **Implement discount system** (if needed)
3. **Comprehensive testing**
4. **Prepare for production**

### **Questions for You:**
1. **What specific features** are you missing in your current TeoCoin contract?
2. **Do you need staking/discount systems** or just the basic earning mechanism?
3. **What's your current backend setup** (Node.js, Python, etc.)?
4. **What frontend framework** are you using?
5. **How many users** are you planning to support initially?

Let me know what area you'd like to focus on first, and I'll provide detailed implementation guidance for that specific part!

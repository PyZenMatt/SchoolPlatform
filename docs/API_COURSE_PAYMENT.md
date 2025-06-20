# API Documentation - Course Payment System

## Overview

This document provides detailed API documentation for the TeoArt School Platform course payment system using the "approve + backend split" approach.

## Endpoints

### 1. Process Course Payment Direct

**Endpoint**: `POST /api/v1/blockchain/process-course-payment-direct/`

**Description**: Processes a direct course payment where the student approves tokens and the backend handles distribution.

#### Request

```json
{
    "course_id": "string",
    "student_address": "string",
    "price_in_teo": "string",
    "teacher_address": "string"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| course_id | string | Yes | Unique identifier for the course |
| student_address | string | Yes | Ethereum address of the student |
| price_in_teo | string | Yes | Course price in TEO tokens (wei format) |
| teacher_address | string | Yes | Ethereum address of the teacher |

#### Response

**Success (200)**:
```json
{
    "success": true,
    "message": "Payment processed successfully",
    "transaction_hash": "0x...",
    "teacher_amount": "950000000000000000000",
    "reward_pool_amount": "50000000000000000000",
    "course_id": "course_123"
}
```

**Error (400)**:
```json
{
    "success": false,
    "error": "Insufficient allowance",
    "details": "Student has not approved enough tokens"
}
```

**Error (500)**:
```json
{
    "success": false,
    "error": "Transaction failed",
    "details": "Network error or insufficient gas"
}
```

### 2. Get Reward Pool Address

**Endpoint**: `GET /api/v1/blockchain/reward-pool-address/`

**Description**: Returns the current reward pool address.

#### Response

```json
{
    "reward_pool_address": "0x..."
}
```

### 3. Check Payment Status

**Endpoint**: `GET /api/v1/blockchain/payment-status/{course_id}/{student_address}/`

**Description**: Checks the payment status for a specific course and student.

#### Response

```json
{
    "paid": true,
    "transaction_hash": "0x...",
    "payment_date": "2025-06-15T10:30:00Z",
    "amount_paid": "1000000000000000000000"
}
```

## Frontend Integration

### Web3Service Methods

#### processCoursePaymentDirect

```javascript
/**
 * Processes a direct course payment
 * @param {string} courseId - The course identifier
 * @param {string} priceInTeo - Price in TEO tokens (wei)
 * @param {string} teacherAddress - Teacher's wallet address
 * @returns {Promise<Object>} Payment result
 */
async processCoursePaymentDirect(courseId, priceInTeo, teacherAddress) {
    // Implementation details...
}
```

#### Example Usage

```javascript
import { web3Service } from './services/api/web3Service';

try {
    const result = await web3Service.processCoursePaymentDirect(
        'course_123',
        '1000000000000000000000', // 1000 TEO in wei
        '0x742d35Cc6635C0532925a3b8D6ac0C61d9c2c6b7'
    );
    
    console.log('Payment successful:', result);
} catch (error) {
    console.error('Payment failed:', error);
}
```

## Smart Contract Integration

### Required Contract Methods

#### TEO Token Contract

```solidity
// Approve tokens for spending
function approve(address spender, uint256 amount) external returns (bool);

// Check allowance
function allowance(address owner, address spender) external view returns (uint256);

// Transfer tokens from one address to another
function transferFrom(address from, address to, uint256 amount) external returns (bool);

// Check balance
function balanceOf(address account) external view returns (uint256);
```

### Transaction Flow

1. **Frontend**: Student calls `approve()` on TEO contract
2. **Backend**: Verifies approval with `allowance()`
3. **Backend**: Calls `transferFrom()` to move tokens to teacher
4. **Backend**: Calls `transferFrom()` to move tokens to reward pool
5. **Backend**: Records transaction in database

## Error Handling

### Error Codes

| Code | Description | Action |
|------|-------------|--------|
| INSUFFICIENT_FUNDS | Student doesn't have enough TEO | Show balance error |
| INSUFFICIENT_ALLOWANCE | Approval amount too low | Request new approval |
| TRANSACTION_FAILED | Blockchain transaction failed | Retry or contact support |
| NETWORK_ERROR | RPC connection issues | Check network connection |
| USER_REJECTED | User rejected MetaMask transaction | Allow user to retry |

### Frontend Error Handling

```javascript
try {
    await processCoursePaymentDirect(courseId, price, teacher);
} catch (error) {
    switch (error.code) {
        case 'INSUFFICIENT_FUNDS':
            showError('You don\'t have enough TEO tokens');
            break;
        case 'USER_REJECTED':
            showError('Transaction was cancelled');
            break;
        default:
            showError('Payment failed. Please try again.');
    }
}
```

## Database Schema

### CoursePayment Model

```python
class CoursePayment(models.Model):
    course_id = models.CharField(max_length=100)
    student_address = models.CharField(max_length=42)
    teacher_address = models.CharField(max_length=42)
    amount_teo = models.CharField(max_length=50)
    teacher_amount = models.CharField(max_length=50)
    reward_pool_amount = models.CharField(max_length=50)
    transaction_hash = models.CharField(max_length=66)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')
```

## Configuration

### Required Environment Variables

```bash
# Blockchain Configuration
TEO_CONTRACT_ADDRESS=0x...
BACKEND_WALLET_PRIVATE_KEY=0x...
BACKEND_WALLET_ADDRESS=0x...
REWARD_POOL_ADDRESS=0x...
POLYGON_RPC_URL=https://polygon-rpc.com
CHAIN_ID=137

# Payment Configuration
TEACHER_PERCENTAGE=0.95
REWARD_POOL_PERCENTAGE=0.05

# Gas Configuration
DEFAULT_GAS_LIMIT=100000
GAS_PRICE_GWEI=30
```

### Contract ABI

The TEO contract ABI should be stored in `blockchain/teocoin_abi.py`:

```python
TEOCOIN_ABI = [
    {
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    # ... other ABI definitions
]
```

## Testing

### Unit Tests

```python
class CoursePaymentTestCase(TestCase):
    def test_payment_distribution(self):
        """Test correct distribution of funds"""
        service = BlockchainService()
        result = service.student_pays_course_directly(
            student_address="0x123...",
            course_price="1000000000000000000000",  # 1000 TEO
            teacher_address="0x456..."
        )
        
        self.assertEqual(result['teacher_amount'], "950000000000000000000")
        self.assertEqual(result['reward_pool_amount'], "50000000000000000000")
    
    def test_insufficient_allowance(self):
        """Test handling of insufficient allowance"""
        # Test implementation...
```

### Integration Tests

```python
def test_full_payment_flow():
    """Test complete payment flow end-to-end"""
    # 1. Setup test data
    # 2. Mock blockchain responses
    # 3. Call API endpoint
    # 4. Verify database updates
    # 5. Verify blockchain calls
```

## Monitoring

### Key Metrics

- **Payment Success Rate**: Percentage of successful payments
- **Average Processing Time**: Time from approval to completion
- **Error Distribution**: Types and frequency of errors
- **Gas Usage**: Average gas consumption per transaction

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def process_payment(student_address, course_id, amount):
    logger.info(f"Starting payment process: {student_address} -> {course_id}")
    
    try:
        result = blockchain_service.process_payment(...)
        logger.info(f"Payment successful: {result['transaction_hash']}")
        return result
    except Exception as e:
        logger.error(f"Payment failed: {str(e)}", exc_info=True)
        raise
```

### Alerts

Set up monitoring alerts for:
- High error rates (>5%)
- Transaction failures
- Backend wallet low balance
- Unusual transaction patterns

## Security Considerations

### Best Practices

1. **Input Validation**: Always validate all input parameters
2. **Rate Limiting**: Implement rate limiting on payment endpoints
3. **Private Key Security**: Store private keys securely
4. **Gas Management**: Monitor backend wallet gas balance
5. **Transaction Monitoring**: Log all transactions for audit

### Access Control

```python
@require_http_methods(["POST"])
@csrf_exempt
@ratelimit(key='ip', rate='10/m', method='POST')
def process_course_payment_direct(request):
    # Implementation with security checks
```

## Deployment Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Smart contract addresses verified
- [ ] Backend wallet funded with gas
- [ ] Rate limiting configured
- [ ] Monitoring setup
- [ ] Error tracking enabled
- [ ] Backup procedures in place

---

**Version**: 2.0  
**Last Updated**: June 2025  
**Maintainer**: TeoArt Development Team

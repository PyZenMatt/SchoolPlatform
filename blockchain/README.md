# Blockchain Module

The blockchain module provides TeoCoin token integration for the School Platform, enabling a complete cryptocurrency reward system for educational activities.

## Overview

This module implements:
- **Token Management**: TeoCoin (TEO) token operations on Polygon Amoy testnet
- **Wallet Integration**: User wallet linking and management
- **Reward System**: Automated token minting for educational achievements
- **Transaction Tracking**: Complete audit trail of all blockchain operations
- **Balance Management**: Real-time balance queries with caching

## Architecture

### Core Components

- **`blockchain.py`**: Main blockchain service with Web3 integration
- **`blockchain_clean.py`**: Secure, production-ready blockchain service
- **`models.py`**: Database models for wallet management
- **`views.py`**: REST API endpoints for blockchain operations
- **`teocoin_abi.py`**: Smart contract ABI definitions
- **`admin.py`**: Django admin interface configuration

### Security Features

- **Private Key Protection**: Masked display in admin interface
- **Access Control**: Staff-only minting permissions
- **Input Validation**: Address format and amount validation
- **Audit Logging**: Complete transaction history
- **Error Handling**: Comprehensive exception management

## Course Payment Process (NEW DIRECT SYSTEM)

The course payment system has been completely refactored to implement a direct payment flow where **students pay both TEO tokens and gas fees directly from their wallet**.

### Payment Flow

1. **Student** pays **Teacher** directly (net amount after 15% commission)
2. **Student** pays **Platform Commission** directly to reward pool (15% of course price)  
3. **Student** pays **all gas fees** with MATIC from their wallet
4. **No involvement** of reward pool as payer/intermediary

### Example: 15 TEO Course Purchase

```
Course Price: 15 TEO
├── Teacher receives: 12.75 TEO (85%)
├── Platform commission: 2.25 TEO (15%)
└── Gas fees: Paid by student with MATIC

Transactions on blockchain:
1. transfer(teacher_address, 12.75 TEO) - Student → Teacher
2. transfer(reward_pool_address, 2.25 TEO) - Student → Commission
```

### Security & Transparency Benefits

- **Full Control**: Student maintains complete control of their funds
- **Transparency**: All payments visible on blockchain
- **No Intermediary**: Direct wallet-to-wallet transfers
- **Immediate Payment**: Teacher receives funds instantly
- **No Pool Risk**: No dependency on reward pool balance for payments

### API Endpoints

### Wallet Management

#### `GET /blockchain/balance/`
Get current TeoCoin balance for authenticated user.

**Response:**
```json
{
  "balance": "100.0",
  "wallet_address": "0x...",
  "token_info": {...},
  "user_id": 1,
  "username": "student"
}
```

#### `POST /blockchain/link-wallet/`
Link external wallet to user account.

**Request:**
```json
{
  "wallet_address": "0x742d35Cc6634C0532925a3b8D..."
}
```

### Course Payment System

#### `POST /blockchain/process-course-payment-direct/`
Initialize direct course payment process (NEW).

**Request:**
```json
{
  "student_address": "0x742d35Cc6634C0532925a3b8D...",
  "teacher_address": "0xE2fA8AfbF1B795f5dEd1a33aa...",
  "course_price": "15.0",
  "course_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "reward_pool_address": "0x3b72a4E942CF1467134510cA...",
  "message": "Direct payment process initialized"
}
```

#### `POST /blockchain/confirm-course-payment/`
Confirm successful direct course payment (NEW).

**Request:**
```json
{
  "student_address": "0x742d35Cc6634C0532925a3b8D...",
  "teacher_address": "0xE2fA8AfbF1B795f5dEd1a33aa...",
  "course_price": "15.0",
  "course_id": 1,
  "teacher_tx_hash": "0xf601f2ef824002fca633d7a54...",
  "commission_tx_hash": "0xb37205cbc73f151f9e1a42a49...",
  "teacher_amount": "12.75",
  "commission_amount": "2.25"
}
```

### Token Operations

#### `POST /blockchain/reward/`
Mint tokens as reward (staff only).

**Request:**
```json
{
  "user_id": 1,
  "amount": "10.5",
  "reason": "Course completion bonus"
}
```

#### `GET /blockchain/transactions/`
Get transaction history for user.

#### `POST /blockchain/check-status/`
Check blockchain transaction status.

#### `GET /blockchain/token-info/`
Get public token information (no auth required).

## Database Models

### UserWallet
Stores user wallet information with security considerations.

```python
class UserWallet(models.Model):
    user = models.OneToOneField(User, ...)
    address = models.CharField(max_length=42, unique=True)
    private_key = models.CharField(max_length=66)  # ⚠️ Security Warning
    created_at = models.DateTimeField(auto_now_add=True)
```

**⚠️ Security Warning**: Private keys are currently stored in plain text. For production:
- Implement encryption for private key storage
- Use Hardware Security Modules (HSM) or Key Management Services (KMS)
- Consider deterministic wallet generation
- Implement proper key rotation

## Smart Contract Integration

### TeoCoin2 Contract
- **Network**: Polygon Amoy Testnet
- **Address**: `0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8`
- **Standard**: ERC-20 compatible
- **Features**: Minting, transfers, balance queries

### Key Functions
- `mint(address to, uint256 amount)`: Create new tokens
- `balanceOf(address account)`: Query balance
- `transfer(address to, uint256 amount)`: Transfer tokens

## Testing

### Test Structure
- **`tests/`**: Comprehensive test suite
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end blockchain operations
- **Security Tests**: Validation and access control

### Removed Tests
Dangerous or obsolete tests have been removed:
- `debug_*`: Debug scripts with sensitive data
- `test_admin_wallet_*`: Admin wallet exposure tests
- `test_direct_mint.py`: Direct minting without validation
- `test_high_gas_*`: High gas price tests

## Configuration

### Environment Variables
Required environment variables (see `.env.example`):

```bash
# Blockchain Configuration
POLYGON_AMOY_RPC_URL=https://rpc-amoy.polygon.technology/
TEOCOIN_CONTRACT_ADDRESS=0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8
ADMIN_WALLET_ADDRESS=0x...
ADMIN_PRIVATE_KEY=0x...  # ⚠️ Keep secure!

# Gas Configuration
GAS_LIMIT=100000
GAS_PRICE=20000000000  # 20 Gwei
```

### Django Settings
Add to your Django settings:

```python
INSTALLED_APPS = [
    ...
    'blockchain',
    ...
]

# Blockchain settings
BLOCKCHAIN_NETWORK = 'polygon_amoy'
TOKEN_DECIMALS = 18
```

## Security Considerations

### Current Limitations
1. **Private Key Storage**: Keys stored in plain text database
2. **Network Security**: Testnet only - not production ready
3. **Access Control**: Basic staff-only permissions
4. **Rate Limiting**: No implemented rate limiting

### Production Recommendations
1. **Encryption**: Implement field-level encryption
2. **Key Management**: Use HSM/KMS for key storage
3. **Network Isolation**: Use private blockchain networks
4. **Multi-signature**: Implement multi-sig wallets
5. **Audit Logging**: Enhanced audit trail
6. **Rate Limiting**: Implement API rate limiting
7. **Monitoring**: Real-time blockchain monitoring

## Error Handling

The module implements comprehensive error handling:

- **Blockchain Errors**: Network connectivity, gas issues
- **Validation Errors**: Invalid addresses, amounts
- **Authorization Errors**: Insufficient permissions
- **Database Errors**: Model validation, constraints

All errors are logged for debugging and audit purposes.

## Monitoring and Logging

### Logging Configuration
- **Transaction Logs**: All blockchain operations
- **Error Logs**: Comprehensive error tracking
- **Performance Logs**: API response times
- **Security Logs**: Access attempts and failures

### Health Checks
Monitor blockchain connectivity and contract status:
- RPC endpoint availability
- Contract accessibility
- Gas price monitoring
- Network congestion alerts

## Development Guidelines

### Code Standards
- **English Comments**: All code documented in English
- **Type Hints**: Use Python type hints where applicable
- **Error Handling**: Comprehensive exception handling
- **Testing**: Minimum 80% test coverage
- **Security**: Regular security audits

### Contributing
1. Follow existing code patterns
2. Add comprehensive tests
3. Update documentation
4. Security review for sensitive changes
5. Performance testing for new features

## Future Enhancements

### Planned Features
- **Multi-token Support**: Support for additional tokens
- **DeFi Integration**: Staking and yield farming
- **Cross-chain**: Bridge to other blockchain networks
- **NFT Integration**: Educational achievement NFTs
- **Governance**: DAO-style platform governance

### Technical Improvements
- **Caching**: Redis-based balance caching
- **Queue System**: Celery for async transactions
- **Webhooks**: Real-time transaction notifications
- **Analytics**: Comprehensive blockchain analytics

## Support and Documentation

For additional information:
- **API Documentation**: `/docs/api.md`
- **Architecture Details**: `/docs/architecture.md`
- **Business Logic**: `/docs/business-logic.md`
- **Blockchain Specifics**: `/docs/blockchain/`

## License

This module is part of the School Platform project. See LICENSE file for details.

---

**⚠️ Important**: This is educational software using testnet tokens. Never use real funds or production private keys in this environment.

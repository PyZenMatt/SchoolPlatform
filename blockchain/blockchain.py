"""
TeoCoin Blockchain Service

Manages integration with the TeoCoin smart contract on Polygon Amoy testnet.
Provides functionality for token operations including minting, transfers, and balance queries.
"""

import os
from decimal import Decimal
from typing import Optional, Dict, Any
from web3 import Web3
from django.conf import settings
import json
import logging
from .teocoin_abi import TEOCOIN_ABI

logger = logging.getLogger(__name__)


class TeoCoinService:
    """
    Service class for managing TeoCoin contract operations.
    
    Provides methods for interacting with the TeoCoin smart contract including:
    - Balance queries
    - Token minting (admin only)
    - Token transfers
    - Transaction management
    """
    
    def __init__(self):
        """
        Initialize the TeoCoin service with Web3 connection and contract setup.
        
        Raises:
            ConnectionError: If unable to connect to the blockchain network
        """
        # Web3 Configuration - Load from environment variables for security
        self.rpc_url = getattr(settings, 'POLYGON_AMOY_RPC_URL', 'https://rpc-amoy.polygon.technology/')
        self.contract_address = getattr(settings, 'TEOCOIN_CONTRACT_ADDRESS', None)
        self.admin_private_key = getattr(settings, 'ADMIN_PRIVATE_KEY', None)
        
        # Reward Pool Configuration
        self.reward_pool_private_key = getattr(settings, 'REWARD_POOL_PRIVATE_KEY', None)
        self.reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
        
        # Validate required configuration
        if not self.contract_address:
            raise ValueError("TEOCOIN_CONTRACT_ADDRESS must be set in environment variables")
        
        # Initialize Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Add middleware for PoA chains (Polygon Amoy)
        try:
            from web3.middleware import ExtraDataToPOAMiddleware
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        except ImportError:
            # Fallback for older Web3.py versions
            logger.warning("Could not load PoA middleware - using fallback")
        
        # Verify blockchain connection
        if not self.w3.is_connected():
            logger.error("Unable to connect to Polygon Amoy network")
            raise ConnectionError("Blockchain connection failed")
        
        # Initialize contract instance
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address),
            abi=TEOCOIN_ABI
        )
        
        logger.info(f"TeoCoinService initialized - Contract: {self.contract_address}")
    
    def get_balance(self, wallet_address: str) -> Decimal:
        """
        Get TeoCoin balance for a wallet address.
        
        Args:
            wallet_address: The wallet address to check balance for
            
        Returns:
            Decimal: Balance in TEO tokens (converted from wei)
        """
        import time
        start_time = time.time()
        try:
            checksum_address = Web3.to_checksum_address(wallet_address)
            balance_wei = self.contract.functions.balanceOf(checksum_address).call()
            balance_teo = Web3.from_wei(balance_wei, 'ether')
            execution_time = time.time() - start_time
            logger.info(f"Balance query for {wallet_address} completed in {execution_time:.3f}s")
            if execution_time > 1.0:
                logger.warning(f"Slow blockchain balance query: {execution_time:.3f}s for {wallet_address}")
            return Decimal(str(balance_teo))
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error retrieving balance for {wallet_address} after {execution_time:.3f}s: {e}")
            return Decimal('0')
    
    def mint_tokens(self, to_address: str, amount: Decimal) -> Optional[str]:
        """
        Mint TeoCoin tokens to a specific address (admin only).
        
        Args:
            to_address: Recipient wallet address
            amount: Amount of TEO tokens to mint
            
        Returns:
            Optional[str]: Transaction hash if successful, None if failed
        """
        if not self.admin_private_key:
            logger.error("Private key admin non configurata")
            return None
        
        max_retries = 3
        base_gas_price = self.get_optimized_gas_price()
        
        for attempt in range(max_retries):
            try:
                # Account admin
                admin_account = self.w3.eth.account.from_key(self.admin_private_key)
                
                # Converti amount in wei
                amount_wei = Web3.to_wei(amount, 'ether')
                
                # Prepara transazione
                checksum_to = Web3.to_checksum_address(to_address)
                
                # Incrementa gas price per ogni retry
                gas_price_multiplier = 1 + (attempt * 0.2)  # +20% per ogni retry
                current_gas_price = int(base_gas_price * gas_price_multiplier)
                
                # Ottieni nonce corrente (include pending transactions)
                nonce = self.w3.eth.get_transaction_count(admin_account.address, 'pending')
                
                transaction = self.contract.functions.mintTo(
                    checksum_to, 
                    amount_wei
                ).build_transaction({
                    'from': admin_account.address,
                    'gas': 150000,  # Aumentato il gas limit per sicurezza
                    'gasPrice': current_gas_price,
                    'nonce': nonce,
                })
                
                # Firma e invia transazione
                signed_txn = self.w3.eth.account.sign_transaction(transaction, self.admin_private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                
                logger.info(f"Mintati {amount} TEO a {to_address} - TX: {tx_hash.hex()} (attempt {attempt + 1})")
                return tx_hash.hex()
                
            except Exception as e:
                if "replacement transaction underpriced" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"Gas price too low (attempt {attempt + 1}), retrying with higher gas price...")
                    continue
                elif "nonce too low" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"Nonce conflict (attempt {attempt + 1}), retrying...")
                    import time
                    time.sleep(1)  # Wait a moment before retry
                    continue
                else:
                    logger.error(f"Errore nel mint di {amount} TEO a {to_address}: {e}")
                    return None
        
        logger.error(f"Failed to mint {amount} TEO to {to_address} after {max_retries} attempts")
        return None
    
    def transfer_tokens(self, from_private_key: str, to_address: str, amount: Decimal) -> Optional[str]:
        """
        Trasferisce TeoCoins tra indirizzi
        
        Args:
            from_private_key: Chiave privata del mittente
            to_address: Indirizzo destinatario
            amount: Quantità di TEO da trasferire
            
        Returns:
            Transaction hash se successo, None se errore
        """
        try:
            # Account mittente
            from_account = self.w3.eth.account.from_key(from_private_key)
            
            # Converti amount in wei
            amount_wei = Web3.to_wei(amount, 'ether')
            
            # Prepara transazione
            checksum_to = Web3.to_checksum_address(to_address)
            
            # Ottieni gas price ottimizzato
            gas_price = self.get_optimized_gas_price()
            
            transaction = self.contract.functions.transfer(
                checksum_to, 
                amount_wei
            ).build_transaction({
                'from': from_account.address,
                'gas': 80000,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(from_account.address),
            })
            
            # Firma e invia transazione
            signed_txn = self.w3.eth.account.sign_transaction(transaction, from_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f"Trasferiti {amount} TEO da {from_account.address} a {to_address} - TX: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Errore nel trasferimento di {amount} TEO: {e}")
            return None
    
    def transfer_with_reward_pool_gas(self, from_address: str, to_address: str, amount: Decimal) -> Optional[str]:
        """
        Trasferisce TeoCoins tra indirizzi usando la reward pool per pagare le gas fees.
        Questo metodo è utile per il testing quando solo la reward pool ha MATIC per le gas fees.
        
        NOTA: Questo metodo richiede che il contratto supporti transferFrom o che la reward pool
        abbia l'allowance per trasferire dal from_address. Per ora implementiamo un workaround.
        
        Args:
            from_address: Indirizzo mittente (deve aver approvato la reward pool)
            to_address: Indirizzo destinatario  
            amount: Quantità di TEO da trasferire
            
        Returns:
            Transaction hash se successo, None se errore
        """
        reward_pool_private_key = getattr(settings, 'REWARD_POOL_PRIVATE_KEY', None)
        reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
        
        if not reward_pool_private_key or not reward_pool_address:
            logger.error("Configurazione reward pool mancante")
            return None
        
        try:
            # Account reward pool (pagherà le gas fees)
            reward_pool_account = self.w3.eth.account.from_key(reward_pool_private_key)
            
            # Converti amount in wei
            amount_wei = Web3.to_wei(amount, 'ether')
            
            # Prepara indirizzi
            checksum_from = Web3.to_checksum_address(from_address)
            checksum_to = Web3.to_checksum_address(to_address)
            
            # Ottieni gas price ottimizzato
            gas_price = self.get_optimized_gas_price()
            
            # Costruisci transazione transferFrom (reward pool paga gas fees)
            transaction = self.contract.functions.transferFrom(
                checksum_from,
                checksum_to, 
                amount_wei
            ).build_transaction({
                'from': reward_pool_account.address,  # La reward pool paga le gas fees
                'gas': 100000,  # Gas limit maggiore per transferFrom
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(reward_pool_account.address),
            })
            
            # Firma e invia transazione con la chiave reward pool
            signed_txn = self.w3.eth.account.sign_transaction(transaction, reward_pool_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f"Trasferiti {amount} TEO da {from_address} a {to_address} (gas pagato da reward pool) - TX: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Errore nel trasferimento con gas reward pool: {e}")
            # CRITICAL FIX: Do NOT fallback to giving TEO to student!
            # The original transfer failed, so return None to indicate failure
            logger.error("Transfer failed - this likely means the student hasn't approved the platform to spend their TEO")
            return None
    
    # Class-level cache for token info to avoid repeated RPC calls
    _token_info_cache = None
    _token_info_timestamp = None
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        Ottiene informazioni base del token con caching per performance
        
        Returns:
            Dizionario con nome, simbolo, decimali
        """
        import time
        from datetime import datetime, timedelta
        
        # Se abbiamo la cache e non è più vecchia di 1 ora, usiamo quella
        current_time = datetime.now()
        if (self._token_info_cache is not None and 
            self._token_info_timestamp is not None and 
            current_time - self._token_info_timestamp < timedelta(hours=1)):
            return self._token_info_cache
        
        # Altrimenti facciamo la query RPC e aggiorniamo la cache
        try:
            start_time = time.time()
            info = {
                'name': self.contract.functions.name().call(),
                'symbol': self.contract.functions.symbol().call(),
                'decimals': self.contract.functions.decimals().call(),
                'contract_address': self.contract_address,
                'total_supply': str(Web3.from_wei(self.contract.functions.totalSupply().call(), 'ether'))
            }
            execution_time = time.time() - start_time
            logger.info(f"Token info query completed in {execution_time:.3f}s")
            
            # Update cache
            self.__class__._token_info_cache = info
            self.__class__._token_info_timestamp = current_time
            
            return info
        except Exception as e:
            logger.error(f"Errore nel recupero info token: {e}")
            return {}
    
    def get_transaction_receipt(self, tx_hash) -> Optional[Dict]:
        """
        Ottiene la ricevuta di una transazione
        
        Args:
            tx_hash: Hash della transazione (string o bytes)
            
        Returns:
            Dizionario con i dettagli della transazione
        """
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return {
                'status': receipt['status'],
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed'],
                'transaction_hash': receipt['transactionHash'].hex(),
                'from': receipt['from'],
                'to': receipt['to']
            }
        except Exception as e:
            logger.error(f"Errore nel recupero ricevuta per {tx_hash}: {e}")
            return None
    
    def validate_address(self, address: str) -> bool:
        """
        Valida un indirizzo Ethereum
        
        Args:
            address: Indirizzo da validare
            
        Returns:
            True se valido, False altrimenti
        """
        try:
            Web3.to_checksum_address(address)
            return True
        except ValueError:
            return False
    
    def get_reward_pool_balance(self) -> Decimal:
        """
        Ottiene il balance della reward pool
        
        Returns:
            Balance della reward pool in TEO
        """
        reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
        if not reward_pool_address:
            logger.error("REWARD_POOL_ADDRESS non configurato")
            return Decimal('0')
        
        return self.get_balance(reward_pool_address)
    
    def get_reward_pool_matic_balance(self) -> Decimal:
        """
        Gets the native MATIC balance of the reward pool.
        
        Returns:
            Decimal: MATIC balance of the reward pool
        """
        reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
        if not reward_pool_address:
            logger.error("REWARD_POOL_ADDRESS not configured")
            return Decimal('0')
        
        try:
            checksum_address = Web3.to_checksum_address(reward_pool_address)
            balance_wei = self.w3.eth.get_balance(checksum_address)
            balance_matic = Web3.from_wei(balance_wei, 'ether')
            return Decimal(str(balance_matic))
        except Exception as e:
            logger.error(f"Error retrieving MATIC balance for reward pool {reward_pool_address}: {e}")
            return Decimal('0')
    
    def get_reward_pool_info(self) -> Dict[str, Any]:
        """
        Gets comprehensive information about the reward pool.
        
        Returns:
            Dict containing:
            - teo_balance: TeoCoin balance
            - matic_balance: MATIC balance
            - address: Reward pool address
            - warning_threshold: Warning threshold for MATIC balance
            - critical_threshold: Critical threshold for MATIC balance
            - status: 'ok', 'warning', or 'critical' based on MATIC balance
        """
        reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
        
        if not reward_pool_address:
            logger.error("REWARD_POOL_ADDRESS not configured")
            return {
                'teo_balance': '0',
                'matic_balance': '0',
                'address': None,
                'warning_threshold': '0.1',
                'critical_threshold': '0.05',
                'status': 'critical',
                'error': 'Reward pool address not configured'
            }
        
        # Define thresholds for MATIC balance
        warning_threshold = Decimal('0.1')  # 0.1 MATIC
        critical_threshold = Decimal('0.05')  # 0.05 MATIC
        
        # Get balances
        teo_balance = self.get_reward_pool_balance()
        matic_balance = self.get_reward_pool_matic_balance()
        
        # Determine status
        status = 'ok'
        if matic_balance <= critical_threshold:
            status = 'critical'
        elif matic_balance <= warning_threshold:
            status = 'warning'
        
        return {
            'teo_balance': str(teo_balance),
            'matic_balance': str(matic_balance),
            'address': reward_pool_address,
            'warning_threshold': str(warning_threshold),
            'critical_threshold': str(critical_threshold),
            'status': status
        }
    
    def transfer_from_reward_pool(self, to_address: str, amount: Decimal) -> Optional[str]:
        """
        Trasferisce TeoCoins dalla reward pool a un indirizzo specifico
        
        Args:
            to_address: Indirizzo destinatario
            amount: Quantità di TEO da trasferire
            
        Returns:
            Transaction hash se successo, None se errore
        """
        reward_pool_private_key = getattr(settings, 'REWARD_POOL_PRIVATE_KEY', None)
        if not reward_pool_private_key:
            logger.error("REWARD_POOL_PRIVATE_KEY non configurata")
            return None
        
        # Verifica che la reward pool abbia fondi sufficienti
        reward_pool_balance = self.get_reward_pool_balance()
        if reward_pool_balance < amount:
            logger.error(f"Fondi insufficienti nella reward pool. Balance: {reward_pool_balance}, Richiesto: {amount}")
            return None
        
        # Effettua il trasferimento
        return self.transfer_tokens(reward_pool_private_key, to_address, amount)
    
    def check_reward_pool_health(self) -> Dict[str, Any]:
        """
        Controlla lo stato di salute della reward pool
        
        Returns:
            Dizionario con informazioni sullo stato della pool
        """
        reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
        if not reward_pool_address:
            return {'error': 'REWARD_POOL_ADDRESS non configurato'}
        
        balance = self.get_reward_pool_balance()
        
        # Soglie di avviso (configurabili)
        warning_threshold = Decimal('100')  # 100 TEO
        critical_threshold = Decimal('50')   # 50 TEO
        
        status = 'healthy'
        if balance <= critical_threshold:
            status = 'critical'
        elif balance <= warning_threshold:
            status = 'warning'
        
        return {
            'address': reward_pool_address,
            'balance': float(balance),
            'status': status,
            'warning_threshold': float(warning_threshold),
            'critical_threshold': float(critical_threshold)
        }
    
    def fund_student_for_approval(self, student_address: str, matic_amount: Decimal = Decimal('0.01')) -> Optional[str]:
        """
        Trasferisce MATIC dalla reward pool allo studente per coprire le gas fees dell'approvazione.
        Questa funzione è usata in modalità test.
        
        Args:
            student_address: Indirizzo dello studente
            matic_amount: Quantità di MATIC da trasferire (default: 0.01)
            
        Returns:
            Transaction hash se successo, None se errore
        """
        reward_pool_private_key = getattr(settings, 'REWARD_POOL_PRIVATE_KEY', None)
        reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
        
        if not reward_pool_private_key or not reward_pool_address:
            logger.error("Reward pool non configurato correttamente")
            return None
        
        try:
            from web3 import Web3
            
            reward_pool_checksum = Web3.to_checksum_address(reward_pool_address)
            student_checksum = Web3.to_checksum_address(student_address)
            
            # Verifica balance MATIC reward pool
            pool_matic_balance = self.w3.from_wei(self.w3.eth.get_balance(reward_pool_checksum), 'ether')
            required_matic = matic_amount + Decimal('0.001')  # MATIC per trasferimento + buffer per gas
            
            if pool_matic_balance < required_matic:
                logger.error(f"Reward pool ha MATIC insufficienti: {pool_matic_balance} < {required_matic}")
                return None
            
            # Prepara transazione MATIC
            matic_amount_wei = Web3.to_wei(matic_amount, 'ether')
            
            # Ottieni nonce e gas price attuali
            nonce = self.w3.eth.get_transaction_count(reward_pool_checksum, 'pending')
            current_gas_price = self.w3.eth.gas_price
            # Aumenta il gas price del 20% per evitare "underpriced"
            gas_price = int(current_gas_price * 1.2)
            
            # Limiti gas price per test economici
            min_gas_price = self.w3.to_wei('25', 'gwei')
            max_gas_price = self.w3.to_wei('50', 'gwei')
            if gas_price < min_gas_price:
                gas_price = min_gas_price
            elif gas_price > max_gas_price:
                gas_price = max_gas_price
            
            matic_tx = {
                'to': student_checksum,
                'value': matic_amount_wei,
                'gas': 21000,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': 80002  # Polygon Amoy chain ID
            }
            
            # Firma e invia transazione
            signed_tx = self.w3.eth.account.sign_transaction(matic_tx, reward_pool_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            logger.info(f"Trasferiti {matic_amount} MATIC da reward pool a studente {student_address} - TX: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Errore nel trasferimento MATIC allo studente: {e}")
            return None

    def approve_reward_pool_as_spender(self, user_private_key: str, allowance_amount: Optional[Decimal] = None) -> Optional[str]:
        """
        Approva la reward pool come spender per l'utente.
        Questo permette alla reward pool di trasferire TeoCoins dall'utente pagando le gas fees.
        
        Args:
            user_private_key: Chiave privata dell'utente
            allowance_amount: Importo da approvare (default: importo molto alto per test)
            
        Returns:
            Transaction hash se successo, None se errore
        """
        reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
        if not reward_pool_address:
            logger.error("REWARD_POOL_ADDRESS non configurato")
            return None
        
        if allowance_amount is None:
            # Importo molto alto per test (1 milione di TEO)
            allowance_amount = Decimal('1000000')
        
        try:
            # Account utente
            user_account = self.w3.eth.account.from_key(user_private_key)
            
            # Converti allowance in wei
            allowance_wei = Web3.to_wei(allowance_amount, 'ether')
            
            # Prepara transazione approve
            checksum_spender = Web3.to_checksum_address(reward_pool_address)
            
            # Ottieni gas price ottimizzato
            gas_price = self.get_optimized_gas_price()
            
            transaction = self.contract.functions.approve(
                checksum_spender,
                allowance_wei
            ).build_transaction({
                'from': user_account.address,
                'gas': 80000,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(user_account.address),
            })
            
            # Firma e invia transazione
            signed_txn = self.w3.eth.account.sign_transaction(transaction, user_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f"Approvato {allowance_amount} TEO allowance per reward pool da {user_account.address} - TX: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Errore nell'approvazione allowance: {e}")
            return None
        
    def process_course_payment(self, student_private_key: str, teacher_address: str, 
                              course_price: Decimal, commission_rate: Decimal = Decimal('0.15')) -> Optional[dict]:
        """
        Processa il pagamento di un corso con la logica pulita:
        1. Lo studente fa approve() con i suoi MATIC per gas fees
        2. La reward pool fa transferFrom() studente->teacher (importo netto) con i suoi MATIC
        3. La reward pool fa transferFrom() studente->reward_pool (commissione) con i suoi MATIC
        
        PREREQUISITO: Lo studente DEVE avere abbastanza MATIC nel wallet per la transazione approve()
        
        Args:
            student_private_key: Chiave privata dello studente
            teacher_address: Indirizzo wallet del teacher
            course_price: Prezzo totale del corso
            commission_rate: Percentuale di commissione (default 15%)
            
        Returns:
            Dict con transaction hashes se successo, None se errore
        """
        reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
        reward_pool_private_key = getattr(settings, 'REWARD_POOL_PRIVATE_KEY', None)
        
        if not reward_pool_address or not reward_pool_private_key:
            logger.error("REWARD_POOL_ADDRESS o REWARD_POOL_PRIVATE_KEY non configurati")
            return None
        
        try:
            # Calcola importi
            commission_amount = course_price * commission_rate
            teacher_amount = course_price - commission_amount
            
            # Account studente e reward pool
            student_account = self.w3.eth.account.from_key(student_private_key)
            student_address = student_account.address
            reward_pool_account = self.w3.eth.account.from_key(reward_pool_private_key)
            
            # Verifica balance studente
            student_balance = self.get_balance(student_address)
            if student_balance < course_price:
                logger.error(f"Studente ha fondi insufficienti: {student_balance} < {course_price}")
                return None
            
            logger.info(f"Elaborando pagamento corso:")
            logger.info(f"  Studente: {student_address} paga {course_price} TEO")
            logger.info(f"  Teacher: {teacher_address} riceve {teacher_amount} TEO") 
            logger.info(f"  Reward Pool: {reward_pool_address} riceve {commission_amount} TEO")
            
            # Gestione nonce sequenziale per reward pool
            current_nonce = self.w3.eth.get_transaction_count(reward_pool_account.address)
            logger.info(f"Nonce iniziale reward pool: {current_nonce}")
            
            # Step 1: Studente approva reward pool per trasferire i suoi TeoCoins
            logger.info("Step 1: Approvazione reward pool da parte dello studente...")
            approval_tx = self.approve_reward_pool_as_spender(student_private_key, course_price)
            if not approval_tx:
                logger.error("Approvazione fallita")
                return None
            
            # Aspetta conferma approvazione prima delle successive transazioni
            import time
            time.sleep(8)
            
            # Debug: Verifica allowance dopo approvazione
            try:
                allowance = self.contract.functions.allowance(
                    Web3.to_checksum_address(student_address),
                    Web3.to_checksum_address(reward_pool_address)
                ).call()
                allowance_teo = Web3.from_wei(allowance, 'ether')
                logger.info(f"Allowance verificata: {allowance_teo} TEO")
                if allowance_teo < course_price:
                    logger.error(f"Allowance insufficiente: {allowance_teo} < {course_price}")
                    return None
            except Exception as e:
                logger.warning(f"Errore verifica allowance: {e}")
            
            # Step 2: Reward pool trasferisce dal studente al teacher (importo netto)
            logger.info("Step 2: Trasferimento studente -> teacher...")
            teacher_tx = self.transfer_from_student_via_reward_pool_with_nonce(
                student_address, teacher_address, teacher_amount, current_nonce
            )
            if not teacher_tx:
                logger.error("Trasferimento a teacher fallito")
                return None
            current_nonce += 1
            
            # Debug: Verifica allowance dopo primo trasferimento
            try:
                allowance = self.contract.functions.allowance(
                    Web3.to_checksum_address(student_address),
                    Web3.to_checksum_address(reward_pool_address)
                ).call()
                allowance_teo = Web3.from_wei(allowance, 'ether')
                logger.info(f"Allowance rimanente dopo trasferimento teacher: {allowance_teo} TEO")
            except Exception as e:
                logger.warning(f"Errore verifica allowance dopo teacher: {e}")
            
            # Aspetta conferma prima della prossima transazione
            time.sleep(5)
            
            # Step 3: Reward pool trasferisce dal studente a se stessa (commissione)
            logger.info("Step 3: Trasferimento commissione studente -> reward pool...")
            commission_tx = self.transfer_from_student_via_reward_pool_with_nonce(
                student_address, reward_pool_address, commission_amount, current_nonce
            )
            if not commission_tx:
                logger.error("Trasferimento commissione fallito")
                return None
            
            logger.info("✅ Pagamento corso completato con successo!")
            result = {
                'approval_tx': approval_tx,
                'teacher_payment_tx': teacher_tx,
                'commission_tx': commission_tx,
                'student_address': student_address,
                'teacher_address': teacher_address,
                'teacher_amount': teacher_amount,
                'commission_amount': commission_amount,
                'total_paid': course_price
            }
                
            return result
            
        except Exception as e:
            logger.error(f"Errore nel pagamento corso: {e}")
            return None
    
    def process_course_payment_approve_split(self, student_address: str, teacher_address: str, 
                                            course_price: Decimal, commission_rate: Decimal = Decimal('0.15')) -> Optional[dict]:
        """
        Processa il pagamento di un corso con il nuovo sistema "approve + backend split":
        1. Verifica che lo studente abbia già approvato il reward pool per l'importo del corso
        2. Il backend (reward pool) esegue transferFrom per il teacher (85%)
        3. Il backend (reward pool) esegue transferFrom per la commissione (15%)
        
        PREREQUISITO: Lo studente DEVE aver già fatto approve() al reward pool per course_price
        
        Args:
            student_address: Indirizzo wallet dello studente
            teacher_address: Indirizzo wallet del teacher
            course_price: Prezzo totale del corso (che lo studente ha approvato)
            commission_rate: Percentuale di commissione (default 15%)
            
        Returns:
            Dict con transaction hashes e importi se successo, None se errore
        """
        reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
        reward_pool_private_key = getattr(settings, 'REWARD_POOL_PRIVATE_KEY', None)
        
        if not reward_pool_address or not reward_pool_private_key:
            logger.error("REWARD_POOL_ADDRESS o REWARD_POOL_PRIVATE_KEY non configurati")
            return None
        
        try:
            # Calcola importi
            commission_amount = course_price * commission_rate
            teacher_amount = course_price - commission_amount
            
            logger.info(f"Elaborando pagamento corso (approve+split):")
            logger.info(f"  Studente: {student_address} ha approvato {course_price} TEO")
            logger.info(f"  Teacher: {teacher_address} riceverà {teacher_amount} TEO")
            logger.info(f"  Commissione: {commission_amount} TEO alla reward pool")
            
            # Verifica che lo studente abbia approvato abbastanza fondi
            try:
                allowance = self.contract.functions.allowance(
                    Web3.to_checksum_address(student_address),
                    Web3.to_checksum_address(reward_pool_address)
                ).call()
                allowance_teo = Decimal(str(Web3.from_wei(allowance, 'ether')))
                
                if allowance_teo < course_price:
                    logger.error(f"Allowance insufficiente: {allowance_teo} TEO < {course_price} TEO richiesti")
                    return {
                        'success': False,
                        'error': 'INSUFFICIENT_ALLOWANCE',
                        'allowance': str(allowance_teo),
                        'required': str(course_price)
                    }
                    
                logger.info(f"✅ Allowance verificata: {allowance_teo} TEO")
                
            except Exception as e:
                logger.error(f"Errore verifica allowance: {e}")
                return {
                    'success': False,
                    'error': 'ALLOWANCE_CHECK_FAILED',
                    'details': str(e)
                }
            
            # Verifica balance studente
            student_balance = self.get_balance(student_address)
            if student_balance < course_price:
                logger.error(f"Studente ha fondi insufficienti: {student_balance} < {course_price}")
                return {
                    'success': False,
                    'error': 'INSUFFICIENT_BALANCE',
                    'balance': str(student_balance),
                    'required': str(course_price)
                }
            
            # Account reward pool
            reward_pool_account = self.w3.eth.account.from_key(reward_pool_private_key)
            
            # Gestione nonce sequenziale per reward pool
            current_nonce = self.w3.eth.get_transaction_count(reward_pool_account.address, 'pending')
            logger.info(f"Nonce reward pool: {current_nonce}")
            
            # Step 1: Trasferimento studente -> teacher (importo netto)
            logger.info("Step 1: Trasferimento studente -> teacher...")
            teacher_tx = self.transfer_from_student_via_reward_pool_with_nonce(
                student_address, teacher_address, teacher_amount, current_nonce
            )
            if not teacher_tx:
                logger.error("Trasferimento a teacher fallito")
                return {
                    'success': False,
                    'error': 'TEACHER_TRANSFER_FAILED'
                }
            
            # Step 2: Trasferimento commissione studente -> reward pool
            logger.info("Step 2: Trasferimento commissione studente -> reward pool...")
            commission_tx = self.transfer_from_student_via_reward_pool_with_nonce(
                student_address, reward_pool_address, commission_amount, current_nonce + 1
            )
            if not commission_tx:
                logger.error("Trasferimento commissione fallito")
                return {
                    'success': False,
                    'error': 'COMMISSION_TRANSFER_FAILED',
                    'teacher_tx': teacher_tx  # Include teacher_tx per eventuale rollback manuale
                }
            
            logger.info("✅ Pagamento corso (approve+split) completato con successo!")
            
            result = {
                'success': True,
                'teacher_payment_tx': teacher_tx,
                'commission_tx': commission_tx,
                'student_address': student_address,
                'teacher_address': teacher_address,
                'teacher_amount': str(teacher_amount),
                'commission_amount': str(commission_amount),
                'total_paid': str(course_price),
                'commission_rate': str(commission_rate)
            }
                
            return result
            
        except Exception as e:
            logger.error(f"Errore nel pagamento corso (approve+split): {e}")
            return {
                'success': False,
                'error': 'GENERAL_ERROR',
                'details': str(e)
            }

    def check_student_approval(self, student_address: str, course_price: Decimal) -> Dict[str, Any]:
        """
        Verifica se lo studente ha approvato abbastanza fondi al reward pool.
        
        Args:
            student_address: Indirizzo wallet dello studente
            course_price: Prezzo del corso richiesto
            
        Returns:
            Dict con informazioni sull'approval
        """
        reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
        
        if not reward_pool_address:
            return {
                'approved': False,
                'error': 'REWARD_POOL_NOT_CONFIGURED'
            }
        
        try:
            # Controlla allowance
            allowance = self.contract.functions.allowance(
                Web3.to_checksum_address(student_address),
                Web3.to_checksum_address(reward_pool_address)
            ).call()
            allowance_teo = Decimal(str(Web3.from_wei(allowance, 'ether')))
            
            # Controlla balance
            student_balance = self.get_balance(student_address)
            
            result = {
                'approved': allowance_teo >= course_price,
                'allowance': str(allowance_teo),
                'required': str(course_price),
                'balance': str(student_balance),
                'has_sufficient_balance': student_balance >= course_price,
                'ready_for_payment': allowance_teo >= course_price and student_balance >= course_price
            }
            
            logger.info(f"Approval check: {student_address} - Allowance: {allowance_teo}, Required: {course_price}, Ready: {result['ready_for_payment']}")
            return result
            
        except Exception as e:
            logger.error(f"Errore check approval: {e}")
            return {
                'approved': False,
                'error': 'CHECK_FAILED',
                'details': str(e)
            }

    def check_course_payment_prerequisites(self, student_address: str, course_price: Decimal) -> Dict[str, Any]:
        """
        Verifica i prerequisiti per il pagamento di un corso.
        
        Args:
            student_address: Indirizzo dello studente
            course_price: Prezzo del corso
            
        Returns:
            Dict con informazioni sui prerequisiti
        """
        try:
            # Verifica balance studente
            student_balance = self.get_balance(student_address)
            has_sufficient_balance = student_balance >= course_price
            
            # Verifica allowance (per sistema approve+split)
            reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
            allowance_info = {}
            
            if reward_pool_address:
                try:
                    allowance = self.contract.functions.allowance(
                        Web3.to_checksum_address(student_address),
                        Web3.to_checksum_address(reward_pool_address)
                    ).call()
                    allowance_teo = Decimal(str(Web3.from_wei(allowance, 'ether')))
                    
                    allowance_info = {
                        'has_approval': allowance_teo >= course_price,
                        'allowance': str(allowance_teo),
                        'required': str(course_price)
                    }
                except Exception as e:
                    allowance_info = {
                        'has_approval': False,
                        'error': str(e)
                    }
            
            result = {
                'student_address': student_address,
                'course_price': str(course_price),
                'student_balance': str(student_balance),
                'has_sufficient_balance': has_sufficient_balance,
                'prerequisites_met': has_sufficient_balance,
                'allowance_info': allowance_info
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Errore verifica prerequisiti: {e}")
            return {
                'student_address': student_address,
                'error': str(e),
                'prerequisites_met': False
            }
    
    def get_optimized_gas_price(self) -> int:
        """
        Ottiene un gas price ottimizzato per la rete.
        
        Returns:
            int: Gas price in wei
        """
        try:
            gas_price = self.w3.eth.gas_price
            # Aggiungi 10% per sicurezza
            gas_price = int(gas_price * 1.1)
            
            # Limiti min/max
            min_gas_price = self.w3.to_wei('25', 'gwei')
            max_gas_price = self.w3.to_wei('50', 'gwei')
            
            if gas_price < min_gas_price:
                gas_price = min_gas_price
            elif gas_price > max_gas_price:
                gas_price = max_gas_price
                
            return gas_price
        except:
            return self.w3.to_wei('30', 'gwei')

    def transfer_from_student_via_reward_pool_with_nonce(self, student_address: str, to_address: str, 
                                                        amount: Decimal, nonce: int) -> Optional[str]:
        """
        Trasferisce TeoCoins dal wallet dello studente a un destinatario usando transferFrom,
        con nonce esplicito per evitare conflitti.
        
        Args:
            student_address: Indirizzo studente (from)
            to_address: Indirizzo destinatario
            amount: Quantità di TEO da trasferire
            nonce: Nonce specifico da utilizzare
            
        Returns:
            Transaction hash se successo, None se errore
        """
        reward_pool_private_key = getattr(settings, 'REWARD_POOL_PRIVATE_KEY', None)
        if not reward_pool_private_key:
            logger.error("REWARD_POOL_PRIVATE_KEY non configurata")
            return None
        
        try:
            # Account reward pool (pagherà le gas fees)
            reward_pool_account = self.w3.eth.account.from_key(reward_pool_private_key)
            
            # Converti amount in wei
            amount_wei = Web3.to_wei(amount, 'ether')
            
            # Indirizzi checksum
            checksum_from = Web3.to_checksum_address(student_address)
            checksum_to = Web3.to_checksum_address(to_address)
            
            # Gas price ottimizzato
            gas_price = self.get_optimized_gas_price()
            
            # Costruisci transazione transferFrom con nonce esplicito
            transaction = self.contract.functions.transferFrom(
                checksum_from,  # Da studente
                checksum_to,    # A destinatario (teacher o reward pool)
                amount_wei
            ).build_transaction({
                'from': reward_pool_account.address,  # Reward pool paga gas
                'gas': 100000,
                'gasPrice': gas_price,
                'nonce': nonce,
            })
            
            # Firma e invia transazione con chiave reward pool
            signed_txn = self.w3.eth.account.sign_transaction(transaction, reward_pool_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f"TransferFrom: {amount} TEO da {student_address} a {to_address} (nonce: {nonce}) - TX: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Errore in transferFrom con nonce {nonce}: {e}")
            return None

    def get_reward_pool_address(self) -> Optional[str]:
        """
        Restituisce l'indirizzo della reward pool.
        
        Returns:
            str: Indirizzo della reward pool o None se non configurato
        """
        return getattr(settings, 'REWARD_POOL_ADDRESS', None)

    def get_reward_pool_account(self):
        """
        PHASE 2.2: Get reward pool account for gas-free transactions
        
        Returns:
            Account object for reward pool that can sign transactions
        """
        reward_pool_private_key = getattr(settings, 'REWARD_POOL_PRIVATE_KEY', None)
        
        if not reward_pool_private_key:
            raise ValueError("REWARD_POOL_PRIVATE_KEY not configured")
            
        return self.w3.eth.account.from_key(reward_pool_private_key)

    # ============================================
    # STAKING MANAGEMENT METHODS
    # ============================================

    def get_teacher_staking_info(self, teacher_address: str) -> Dict[str, Any]:
        """
        Get comprehensive staking information for a teacher.
        
        Args:
            teacher_address: Teacher's wallet address
            
        Returns:
            Dictionary with staking information
        """
        try:
            checksum_address = Web3.to_checksum_address(teacher_address)
            
            # Get current balance and staked amount
            balance = self.get_balance(teacher_address)
            
            # For MVP implementation, we'll use a simple staking simulation
            # In production, this would interact with a dedicated staking contract
            staked_amount = self._get_simulated_staked_amount(teacher_address)
            
            # Calculate tier based on staked amount
            tier_info = self._calculate_tier_from_staked_amount(staked_amount)
            
            return {
                'wallet_address': teacher_address,
                'available_balance': str(balance),
                'staked_amount': str(staked_amount),
                'staking_tier': tier_info['tier'],
                'commission_rate': tier_info['commission_rate'],
                'next_tier': tier_info['next_tier'],
                'next_tier_requirement': str(tier_info['next_tier_requirement']),
                'can_stake_more': balance > 0,
                'minimum_stake_amount': '10',  # Minimum 10 TEO to stake
                'unstaking_periods': {
                    'immediate_withdrawal_limit': '10%',  # 10% can be withdrawn immediately
                    'standard_waiting_period': '30 days',
                    'emergency_penalty_rate': '10%'
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting staking info for {teacher_address}: {e}")
            return {
                'error': str(e),
                'wallet_address': teacher_address,
                'available_balance': '0',
                'staked_amount': '0'
            }

    def stake_tokens(self, teacher_address: str, amount: Decimal) -> Dict[str, Any]:
        """
        Stake TEO tokens for a teacher to improve their commission rate.
        
        This MVP implementation simulates staking by transferring tokens to a staking pool.
        In production, this would interact with a dedicated TeoCoin staking contract.
        
        Args:
            teacher_address: Teacher's wallet address
            amount: Amount of TEO to stake
            
        Returns:
            Dictionary with staking result
        """
        try:
            checksum_address = Web3.to_checksum_address(teacher_address)
            
            # Check if teacher has enough balance
            current_balance = self.get_balance(teacher_address)
            if current_balance < amount:
                return {
                    'success': False,
                    'error': f'Insufficient balance. Available: {current_balance} TEO, Required: {amount} TEO'
                }
            
            # For MVP: Transfer tokens to staking pool to simulate staking
            staking_pool_address = getattr(settings, 'STAKING_POOL_ADDRESS', None)
            if not staking_pool_address:
                # Fallback: use reward pool as staking pool
                staking_pool_address = self.reward_pool_address
            
            if not staking_pool_address:
                return {
                    'success': False,
                    'error': 'Staking pool not configured'
                }
            
            # Execute transfer to staking pool (simulates staking)
            # In production, this would call a staking contract method
            amount_wei = Web3.to_wei(amount, 'ether')
            
            # Use reward pool to pay gas fees for staking transaction
            tx_hash = self._execute_staking_transaction(teacher_address, staking_pool_address, amount_wei)
            
            if not tx_hash:
                return {
                    'success': False,
                    'error': 'Staking transaction failed'
                }
            
            # Calculate new total staked amount
            current_staked = self._get_simulated_staked_amount(teacher_address)
            new_total_staked = current_staked + amount
            
            # Update simulated staking record
            self._update_simulated_staking_record(teacher_address, new_total_staked)
            
            logger.info(f"Staked {amount} TEO for teacher {teacher_address}. New total: {new_total_staked} TEO")
            
            return {
                'success': True,
                'tx_hash': tx_hash,
                'staked_amount': str(amount),
                'total_staked': str(new_total_staked),
                'staking_contract_address': staking_pool_address
            }
            
        except Exception as e:
            logger.error(f"Error staking tokens for {teacher_address}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def unstake_tokens(self, teacher_address: str, amount: Decimal) -> Dict[str, Any]:
        """
        Unstake TEO tokens with appropriate waiting periods and penalties.
        
        Args:
            teacher_address: Teacher's wallet address
            amount: Amount of TEO to unstake
            
        Returns:
            Dictionary with unstaking result
        """
        try:
            checksum_address = Web3.to_checksum_address(teacher_address)
            
            # Get current staked amount
            current_staked = self._get_simulated_staked_amount(teacher_address)
            
            if current_staked < amount:
                return {
                    'success': False,
                    'error': f'Insufficient staked tokens. Current staked: {current_staked} TEO, Requested: {amount} TEO'
                }
            
            # Calculate immediate withdrawal limit (10% of staked amount)
            immediate_limit = current_staked * Decimal('0.1')
            
            # Determine if this requires waiting period
            waiting_period = amount > immediate_limit
            penalty_rate = Decimal('0')  # No penalty for standard unstaking
            waiting_period_days = 30 if waiting_period else 0
            
            # For emergency unstaking (immediate large withdrawals), apply penalty
            if amount > immediate_limit and not waiting_period:
                penalty_rate = Decimal('0.1')  # 10% penalty
                amount_after_penalty = amount * (Decimal('1') - penalty_rate)
            else:
                amount_after_penalty = amount
            
            # Execute unstaking transaction
            staking_pool_address = getattr(settings, 'STAKING_POOL_ADDRESS', self.reward_pool_address)
            
            # For MVP: Transfer from staking pool back to teacher (simulates unstaking)
            if waiting_period:
                # Create unstaking request (would be handled by smart contract in production)
                self._create_unstaking_request(teacher_address, amount, waiting_period_days)
                tx_hash = f"0x{hash(f'{teacher_address}-{amount}-{waiting_period_days}'):064x}"  # Simulated hash
            else:
                # Immediate unstaking
                tx_hash = self._execute_unstaking_transaction(staking_pool_address, teacher_address, amount_after_penalty)
                if not tx_hash:
                    return {
                        'success': False,
                        'error': 'Unstaking transaction failed'
                    }
            
            # Update staked amount
            new_staked_amount = current_staked - amount
            self._update_simulated_staking_record(teacher_address, new_staked_amount)
            
            logger.info(f"Unstaked {amount} TEO for teacher {teacher_address}. Remaining: {new_staked_amount} TEO")
            
            return {
                'success': True,
                'tx_hash': tx_hash,
                'unstaked_amount': str(amount),
                'remaining_staked': str(new_staked_amount),
                'waiting_period': waiting_period,
                'waiting_period_days': waiting_period_days,
                'penalty_rate': str(penalty_rate),
                'penalty_amount': str(amount - amount_after_penalty) if penalty_rate > 0 else '0'
            }
            
        except Exception as e:
            logger.error(f"Error unstaking tokens for {teacher_address}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_unstaking_schedule(self, teacher_address: str) -> list:
        """
        Get pending unstaking requests for a teacher.
        
        Args:
            teacher_address: Teacher's wallet address
            
        Returns:
            List of pending unstaking requests
        """
        try:
            # In MVP implementation, use Django cache or database to store unstaking requests
            # In production, this would query the staking smart contract
            from django.core.cache import cache
            
            cache_key = f"unstaking_schedule_{teacher_address.lower()}"
            unstaking_requests = cache.get(cache_key, [])
            
            # Filter out expired requests
            from datetime import datetime
            current_time = datetime.now()
            active_requests = []
            
            for request in unstaking_requests:
                unlock_date = datetime.fromisoformat(request['unlock_date'])
                if unlock_date > current_time:
                    active_requests.append(request)
            
            # Update cache with filtered requests
            cache.set(cache_key, active_requests, 86400 * 365)  # 1 year
            
            return active_requests
            
        except Exception as e:
            logger.error(f"Error getting unstaking schedule for {teacher_address}: {e}")
            return []

    def withdraw_unstaked_tokens(self, teacher_address: str, unstaking_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Withdraw tokens that have completed their unstaking period.
        
        Args:
            teacher_address: Teacher's wallet address
            unstaking_id: Specific unstaking request ID (optional)
            
        Returns:
            Dictionary with withdrawal result
        """
        try:
            # Get unstaking schedule
            unstaking_requests = self.get_unstaking_schedule(teacher_address)
            
            from datetime import datetime
            current_time = datetime.now()
            
            # Find requests ready for withdrawal
            withdrawable_requests = []
            if unstaking_id:
                # Specific request
                for request in unstaking_requests:
                    if request['id'] == unstaking_id:
                        unlock_date = datetime.fromisoformat(request['unlock_date'])
                        if unlock_date <= current_time:
                            withdrawable_requests.append(request)
                        break
            else:
                # All available requests
                for request in unstaking_requests:
                    unlock_date = datetime.fromisoformat(request['unlock_date'])
                    if unlock_date <= current_time:
                        withdrawable_requests.append(request)
            
            if not withdrawable_requests:
                return {
                    'success': False,
                    'error': 'No tokens available for withdrawal'
                }
            
            # Calculate total withdrawal amount
            total_amount = sum(Decimal(request['amount']) for request in withdrawable_requests)
            
            # Execute withdrawal transaction from staking pool
            staking_pool_address = getattr(settings, 'STAKING_POOL_ADDRESS', self.reward_pool_address)
            tx_hash = self._execute_unstaking_transaction(staking_pool_address, teacher_address, total_amount)
            
            if not tx_hash:
                return {
                    'success': False,
                    'error': 'Withdrawal transaction failed'
                }
            
            # Remove withdrawn requests from cache
            from django.core.cache import cache
            cache_key = f"unstaking_schedule_{teacher_address.lower()}"
            remaining_requests = [req for req in unstaking_requests if req not in withdrawable_requests]
            cache.set(cache_key, remaining_requests, 86400 * 365)
            
            logger.info(f"Withdrew {total_amount} TEO for teacher {teacher_address}")
            
            return {
                'success': True,
                'tx_hash': tx_hash,
                'withdrawn_amount': str(total_amount),
                'withdrawn_requests': len(withdrawable_requests),
                'remaining_pending_amount': str(sum(Decimal(req['amount']) for req in remaining_requests))
            }
            
        except Exception as e:
            logger.error(f"Error withdrawing unstaked tokens for {teacher_address}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_platform_staking_statistics(self) -> Dict[str, Any]:
        """
        Get platform-wide staking statistics for admin dashboard.
        
        Returns:
            Dictionary with staking statistics
        """
        try:
            # In MVP implementation, aggregate from database records
            # In production, this would query the staking contract directly
            
            staking_pool_address = getattr(settings, 'STAKING_POOL_ADDRESS', self.reward_pool_address)
            
            if staking_pool_address:
                total_staked_blockchain = self.get_balance(staking_pool_address)
            else:
                total_staked_blockchain = Decimal('0')
            
            return {
                'total_staked_blockchain': str(total_staked_blockchain),
                'staking_pool_address': staking_pool_address,
                'active_stakers': 0,  # Would be calculated from contract events
                'average_stake_period': '90 days',  # Statistical data
                'total_unstaking_requests': 0,  # From contract data
                'last_updated': 'now'
            }
            
        except Exception as e:
            logger.error(f"Error getting platform staking statistics: {e}")
            return {
                'error': str(e),
                'total_staked_blockchain': '0'
            }

    # Helper methods for MVP staking implementation

    def _get_simulated_staked_amount(self, teacher_address: str) -> Decimal:
        """Get simulated staked amount from Django cache/database."""
        try:
            from django.core.cache import cache
            cache_key = f"staked_amount_{teacher_address.lower()}"
            staked_amount = cache.get(cache_key, '0')
            return Decimal(str(staked_amount))
        except:
            return Decimal('0')

    def _update_simulated_staking_record(self, teacher_address: str, new_amount: Decimal):
        """Update simulated staking record in Django cache."""
        try:
            from django.core.cache import cache
            cache_key = f"staked_amount_{teacher_address.lower()}"
            cache.set(cache_key, str(new_amount), 86400 * 365)  # 1 year
        except Exception as e:
            logger.error(f"Error updating staking record: {e}")

    def _calculate_tier_from_staked_amount(self, staked_amount: Decimal) -> Dict[str, Any]:
        """Calculate tier and commission rate based on staked amount."""
        if staked_amount >= 2000:
            return {'tier': 'Diamond', 'commission_rate': '25.0', 'next_tier': None, 'next_tier_requirement': 0}
        elif staked_amount >= 1000:
            return {'tier': 'Platinum', 'commission_rate': '35.0', 'next_tier': 'Diamond', 'next_tier_requirement': 2000}
        elif staked_amount >= 500:
            return {'tier': 'Gold', 'commission_rate': '40.0', 'next_tier': 'Platinum', 'next_tier_requirement': 1000}
        elif staked_amount >= 100:
            return {'tier': 'Silver', 'commission_rate': '45.0', 'next_tier': 'Gold', 'next_tier_requirement': 500}
        else:
            return {'tier': 'Bronze', 'commission_rate': '50.0', 'next_tier': 'Silver', 'next_tier_requirement': 100}

    def _execute_staking_transaction(self, from_address: str, staking_pool_address: str, amount_wei: int) -> Optional[str]:
        """Execute staking transaction using reward pool for gas fees."""
        try:
            # For MVP: Use reward pool to facilitate staking transaction
            # In production: Teacher would approve and call staking contract directly
            
            reward_pool_private_key = getattr(settings, 'REWARD_POOL_PRIVATE_KEY', None)
            if not reward_pool_private_key:
                logger.error("REWARD_POOL_PRIVATE_KEY not configured for staking")
                return None
            
            # Simulate staking by transferring to staking pool
            # This is a simplified implementation - production would use a proper staking contract
            
            checksum_from = Web3.to_checksum_address(from_address)
            checksum_to = Web3.to_checksum_address(staking_pool_address)
            
            reward_pool_account = self.w3.eth.account.from_key(reward_pool_private_key)
            
            # Build transferFrom transaction (teacher must have approved reward pool)
            transaction = self.contract.functions.transferFrom(
                checksum_from,
                checksum_to,
                amount_wei
            ).build_transaction({
                'from': reward_pool_account.address,
                'gas': 100000,
                'gasPrice': self.get_optimized_gas_price(),
                'nonce': self.w3.eth.get_transaction_count(reward_pool_account.address),
            })
            
            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(transaction, reward_pool_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error executing staking transaction: {e}")
            return None

    def _execute_unstaking_transaction(self, staking_pool_address: str, teacher_address: str, amount: Decimal) -> Optional[str]:
        """Execute unstaking transaction from staking pool to teacher."""
        try:
            reward_pool_private_key = getattr(settings, 'REWARD_POOL_PRIVATE_KEY', None)
            if not reward_pool_private_key:
                logger.error("REWARD_POOL_PRIVATE_KEY not configured for unstaking")
                return None
            
            # Transfer from staking pool back to teacher
            amount_wei = Web3.to_wei(amount, 'ether')
            
            checksum_from = Web3.to_checksum_address(staking_pool_address)
            checksum_to = Web3.to_checksum_address(teacher_address)
            
            reward_pool_account = self.w3.eth.account.from_key(reward_pool_private_key)
            
            # Build transfer transaction
            transaction = self.contract.functions.transfer(
                checksum_to,
                amount_wei
            ).build_transaction({
                'from': reward_pool_account.address,
                'gas': 100000,
                'gasPrice': self.get_optimized_gas_price(),
                'nonce': self.w3.eth.get_transaction_count(reward_pool_account.address),
            })
            
            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(transaction, reward_pool_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error executing unstaking transaction: {e}")
            return None

    def _create_unstaking_request(self, teacher_address: str, amount: Decimal, waiting_period_days: int):
        """Create an unstaking request with waiting period."""
        try:
            from django.core.cache import cache
            from datetime import datetime, timedelta
            import uuid
            
            # Create unstaking request
            request_id = str(uuid.uuid4())
            unlock_date = datetime.now() + timedelta(days=waiting_period_days)
            
            request = {
                'id': request_id,
                'teacher_address': teacher_address,
                'amount': str(amount),
                'created_date': datetime.now().isoformat(),
                'unlock_date': unlock_date.isoformat(),
                'waiting_period_days': waiting_period_days,
                'status': 'pending'
            }
            
            # Add to unstaking schedule
            cache_key = f"unstaking_schedule_{teacher_address.lower()}"
            current_requests = cache.get(cache_key, [])
            current_requests.append(request)
            cache.set(cache_key, current_requests, 86400 * 365)  # 1 year
            
            logger.info(f"Created unstaking request {request_id} for {teacher_address}: {amount} TEO")
            
        except Exception as e:
            logger.error(f"Error creating unstaking request: {e}")


# Funzione di convenienza globale per BlockchainService compatibility
def check_course_payment_prerequisites(student_address: str, course_price: Decimal):
    """
    Funzione globale per verificare i prerequisiti di pagamento corso.
    Mantiene compatibilità con il codice esistente.
    """
    service = TeoCoinService()
    return service.check_course_payment_prerequisites(student_address, course_price)

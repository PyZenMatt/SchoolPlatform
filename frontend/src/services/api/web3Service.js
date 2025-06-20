/**
 * Web3 Service for TeoCoin2 integration
 * Handles Metamask connection and smart contract interactions
 */

import { ethers } from 'ethers';

// TeoCoin2 Contract Configuration
const TEOCOIN_CONTRACT_ADDRESS = '0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8';
const POLYGON_AMOY_CHAIN_ID = '0x13882'; // 80002 in hex
const POLYGON_AMOY_RPC_URL = 'https://rpc-amoy.polygon.technology/';

// Simplified ABI - only the functions we need
const TEOCOIN_ABI = [
  'function name() view returns (string)',
  'function symbol() view returns (string)', 
  'function decimals() view returns (uint8)',
  'function balanceOf(address) view returns (uint256)',
  'function totalSupply() view returns (uint256)',
  'function transfer(address to, uint256 amount) returns (bool)',
  'function approve(address spender, uint256 amount) returns (bool)',
  'function allowance(address owner, address spender) view returns (uint256)',
  // Events
  'event Transfer(address indexed from, address indexed to, uint256 value)',
  'event TokensMinted(address indexed mintedTo, uint256 quantityMinted)',
  'event Approval(address indexed owner, address indexed spender, uint256 value)'
];

class Web3Service {
  constructor() {
    this.provider = null;
    this.signer = null;
    this.contract = null;
    this.userAddress = null;
    this.isWalletLocked = false; // New: flag to prevent automatic account changes
    this.lockedWalletAddress = null; // New: the originally connected wallet address
    this._hasStableConnectionSetup = false; // Internal flag to prevent multiple setups
    
    // Restore locked state from localStorage if it exists
    this.restoreLockedState();
  }

  /**
   * Restore locked wallet state from localStorage
   */
  restoreLockedState() {
    try {
      const isLocked = localStorage.getItem('isWalletLocked') === 'true';
      const lockedAddress = localStorage.getItem('lockedWalletAddress');
      
      if (isLocked && lockedAddress) {
        this.isWalletLocked = true;
        this.lockedWalletAddress = lockedAddress;
        this.userAddress = lockedAddress;
        
        // Setup read-only provider immediately
        this.provider = new ethers.JsonRpcProvider(POLYGON_AMOY_RPC_URL);
        this.contract = new ethers.Contract(
          TEOCOIN_CONTRACT_ADDRESS,
          TEOCOIN_ABI,
          this.provider
        );
        
        console.log('🔒 Stato wallet bloccato ripristinato:', lockedAddress);
      }
    } catch (error) {
      console.warn('Errore nel ripristino stato wallet bloccato:', error);
    }
  }

  /**
   * Check if Metamask is installed
   */
  isMetamaskInstalled() {
    return typeof window !== 'undefined' && typeof window.ethereum !== 'undefined';
  }

  /**
   * Connect to Metamask wallet and lock the connection
   */
  async connectWallet() {
    if (!this.isMetamaskInstalled()) {
      throw new Error('Metamask non è installato. Installa Metamask per continuare.');
    }

    try {
      // Connect to Metamask ONLY to get the initial address
      await window.ethereum.request({ method: 'eth_requestAccounts' });
      
      // Setup temporary provider just to get the address
      const tempProvider = new ethers.BrowserProvider(window.ethereum);
      const tempSigner = await tempProvider.getSigner();
      const initialAddress = await tempSigner.getAddress();

      // Lock the wallet to this address - this is our PERMANENT connection
      this.isWalletLocked = true;
      this.lockedWalletAddress = initialAddress;
      this.userAddress = initialAddress;

      // Save locked address to localStorage to prevent overwrite
      localStorage.setItem('connectedWalletAddress', initialAddress);
      localStorage.setItem('isWalletLocked', 'true');
      localStorage.setItem('lockedWalletAddress', initialAddress);

      // Use a static read-only provider for all future operations
      this.provider = new ethers.JsonRpcProvider(POLYGON_AMOY_RPC_URL);
      
      // Create read-only contract instance (no signer needed for balance queries)
      this.contract = new ethers.Contract(
        TEOCOIN_CONTRACT_ADDRESS,
        TEOCOIN_ABI,
        this.provider
      );

      // Setup event listeners to maintain stable connection
      this.setupStableConnection();

      console.log('🔒 Wallet connesso e bloccato:', this.lockedWalletAddress);
      console.log('📡 Usando provider read-only per operazioni');
      return this.lockedWalletAddress;

    } catch (error) {
      console.error('Errore connessione wallet:', error);
      throw new Error('Errore nella connessione del wallet: ' + error.message);
    }
  }

  /**
   * Switch to Polygon Amoy testnet
   */
  async switchToPolygonAmoy() {
    try {
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: POLYGON_AMOY_CHAIN_ID }],
      });
    } catch (switchError) {
      // Chain not added to Metamask
      if (switchError.code === 4902) {
        try {
          await window.ethereum.request({
            method: 'wallet_addEthereumChain',
            params: [{
              chainId: POLYGON_AMOY_CHAIN_ID,
              chainName: 'Polygon Amoy Testnet',
              nativeCurrency: {
                name: 'MATIC',
                symbol: 'MATIC',
                decimals: 18,
              },
              rpcUrls: [POLYGON_AMOY_RPC_URL],
              blockExplorerUrls: ['https://amoy.polygonscan.com/'],
            }],
          });
        } catch (addError) {
          throw new Error('Errore nell\'aggiunta della rete Polygon Amoy');
        }
      } else {
        throw new Error('Errore nel cambio di rete');
      }
    }
  }

  /**
   * Get current connected address (always returns the locked address if wallet is locked)
   */
  async getCurrentAddress() {
    // If wallet is locked, ALWAYS return the locked address
    if (this.isWalletLocked && this.lockedWalletAddress) {
      console.log('🔒 getCurrentAddress: Returning locked address:', this.lockedWalletAddress);
      return this.lockedWalletAddress;
    }
    
    // If not locked, try to connect or return current address
    if (!this.provider) {
      await this.connectWallet();
    }
    return this.lockedWalletAddress || this.userAddress;
  }

  /**
   * Get current connected address (alias for compatibility)
   */
  async getCurrentAccount() {
    return this.getCurrentAddress();
  }

  /**
   * Get accounts from Metamask
   */
  async getAccounts() {
    if (!this.isMetamaskInstalled()) {
      return [];
    }
    
    try {
      const accounts = await window.ethereum.request({ 
        method: 'eth_accounts' 
      });
      return accounts;
    } catch (error) {
      console.error('Error getting accounts:', error);
      return [];
    }
  }

  /**
   * Get TeoCoin balance for any wallet address (read-only)
   */
  async getBalance(address = null) {
    // ALWAYS use locked wallet address if no address specified and wallet is locked
    const targetAddress = address || (this.isWalletLocked ? this.lockedWalletAddress : this.userAddress);
    if (!targetAddress) {
      throw new Error('Nessun indirizzo wallet specificato');
    }

    try {
      // ALWAYS use read-only provider to prevent MetaMask interference
      const provider = new ethers.JsonRpcProvider(POLYGON_AMOY_RPC_URL);
      const contract = new ethers.Contract(TEOCOIN_CONTRACT_ADDRESS, TEOCOIN_ABI, provider);
      const balance = await contract.balanceOf(targetAddress);
      
      if (this.isWalletLocked && !address) {
        console.log('🔒 Balance ottenuto per wallet bloccato:', targetAddress, 'Balance:', ethers.formatEther(balance));
      }
      
      return ethers.formatEther(balance);
      
    } catch (error) {
      console.error('Errore nel recupero balance per indirizzo', targetAddress, ':', error);
      throw new Error('Errore nel recupero del saldo');
    }
  }

  /**
   * Get token information
   */
  async getTokenInfo() {
    if (!this.contract) {
      // Use a read-only provider for token info
      const provider = new ethers.JsonRpcProvider(POLYGON_AMOY_RPC_URL);
      const contract = new ethers.Contract(TEOCOIN_CONTRACT_ADDRESS, TEOCOIN_ABI, provider);
      
      try {
        const [name, symbol, decimals, totalSupply] = await Promise.all([
          contract.name(),
          contract.symbol(), 
          contract.decimals(),
          contract.totalSupply()
        ]);

        return {
          name,
          symbol,
          decimals: Number(decimals),
          totalSupply: ethers.formatEther(totalSupply),
          contractAddress: TEOCOIN_CONTRACT_ADDRESS
        };
      } catch (error) {
        console.error('Errore nel recupero info token:', error);
        throw new Error('Errore nel recupero informazioni token');
      }
    }

    try {
      const [name, symbol, decimals, totalSupply] = await Promise.all([
        this.contract.name(),
        this.contract.symbol(),
        this.contract.decimals(), 
        this.contract.totalSupply()
      ]);

      return {
        name,
        symbol,
        decimals: Number(decimals),
        totalSupply: ethers.formatEther(totalSupply),
        contractAddress: TEOCOIN_CONTRACT_ADDRESS
      };
    } catch (error) {
      console.error('Errore nel recupero info token:', error);
      throw new Error('Errore nel recupero informazioni token');
    }
  }

  /**
   * Listen for token transfer events
   */
  onTokenTransfer(callback) {
    if (!this.contract) {
      console.warn('Contract non inizializzato per gli eventi');
      return;
    }

    this.contract.on('Transfer', (from, to, value, event) => {
      callback({
        from,
        to,
        value: ethers.formatEther(value),
        transactionHash: event.transactionHash,
        blockNumber: event.blockNumber
      });
    });
  }

  /**
   * Listen for token mint events
   */
  onTokensMinted(callback) {
    if (!this.contract) {
      console.warn('Contract non inizializzato per gli eventi');
      return;
    }

    this.contract.on('TokensMinted', (mintedTo, quantityMinted, event) => {
      callback({
        mintedTo,
        quantity: ethers.formatEther(quantityMinted),
        transactionHash: event.transactionHash,
        blockNumber: event.blockNumber
      });
    });
  }

  /**
   * Check wallet connection and return address if connected
   * IMPORTANT: If wallet is locked, ALWAYS return the locked address without checking MetaMask
   */
  async checkConnection() {
    // If wallet is locked, ALWAYS return the locked address - never check MetaMask
    if (this.isWalletLocked && this.lockedWalletAddress) {
      console.log('🔒 checkConnection: Wallet is locked, returning locked address:', this.lockedWalletAddress);
      return this.lockedWalletAddress;
    }
    
    // Check for saved wallet address first (only if not locked)
    if (!this.isWalletLocked) {
      const savedAddress = localStorage.getItem('connectedWalletAddress');
      if (savedAddress && !this.userAddress) {
        this.userAddress = savedAddress;
      }
    }
    
    if (this.userAddress) {
      return this.userAddress;
    }
    
    // Check MetaMask connection if available (only if wallet is not locked)
    if (this.isMetamaskInstalled()) {
      try {
        const accounts = await window.ethereum.request({ method: 'eth_accounts' });
        if (accounts.length > 0) {
          this.userAddress = accounts[0];
          return this.userAddress;
        }
      } catch (error) {
        console.error('Error checking MetaMask connection:', error);
      }
    }
    
    return null;
  }

  /**
   * Disconnect wallet (alias for disconnectWallet)
   */
  disconnect() {
    return this.disconnectWallet();
  }

  /**
   * Check if wallet is connected (returns true if locked or normally connected)
   */
  isConnected() {
    // If wallet is locked, we're always considered connected
    if (this.isWalletLocked && this.lockedWalletAddress) {
      return true;
    }
    return this.userAddress !== null;
  }

  /**
   * Generate a new wallet with mnemonic phrase
   */
  generateWallet() {
    try {
      // Generate a random wallet
      const wallet = ethers.Wallet.createRandom();
      
      return {
        address: wallet.address,
        privateKey: wallet.privateKey,
        mnemonic: wallet.mnemonic.phrase
      };
      
    } catch (error) {
      console.error('Error generating wallet:', error);
      throw new Error('Errore nella generazione del wallet');
    }
  }

  /**
   * Recover wallet from mnemonic phrase
   */
  recoverWallet(mnemonicPhrase) {
    try {
      const wallet = ethers.Wallet.fromPhrase(mnemonicPhrase.trim());
      
      return {
        address: wallet.address,
        privateKey: wallet.privateKey,
        mnemonic: wallet.mnemonic.phrase
      };
      
    } catch (error) {
      console.error('Error recovering wallet:', error);
      throw new Error('Frase di recupero non valida');
    }
  }

  /**
   * Setup generated wallet for blockchain operations
   */
  async setupGeneratedWallet(privateKey) {
    try {
      // Create provider for Polygon Amoy
      this.provider = new ethers.JsonRpcProvider(POLYGON_AMOY_RPC_URL);
      
      // Create wallet instance from private key
      const wallet = new ethers.Wallet(privateKey, this.provider);
      this.signer = wallet;
      this.userAddress = wallet.address;

      // Setup contract instance
      this.contract = new ethers.Contract(
        TEOCOIN_CONTRACT_ADDRESS,
        TEOCOIN_ABI,
        this.signer
      );

      console.log('Generated wallet setup completed:', this.userAddress);
      return this.userAddress;

    } catch (error) {
      console.error('Error setting up generated wallet:', error);
      throw new Error('Errore nella configurazione del wallet generato');
    }
  }

  /**
   * Transfer TeoCoin tokens to another address
   */
  async transferTokens(toAddress, amount) {
    if (!this.isConnected()) {
      throw new Error('Wallet non connesso');
    }

    if (!this.contract) {
      throw new Error('Contratto non inizializzato');
    }

    try {
      // Convert amount to wei (18 decimals for TeoCoin)
      const amountWei = ethers.parseEther(amount.toString());
      
      // Validate the recipient address
      if (!ethers.isAddress(toAddress)) {
        throw new Error('Indirizzo destinatario non valido');
      }

      console.log(`Transferring ${amount} TEO to ${toAddress}`);
      
      // Execute the transfer
      const transaction = await this.contract.transfer(toAddress, amountWei);
      
      console.log('Transaction sent:', transaction.hash);
      
      // Wait for confirmation
      const receipt = await transaction.wait();
      
      if (receipt.status === 1) {
        console.log('Transfer completed successfully:', receipt.hash);
        return receipt.hash;
      } else {
        throw new Error('Transaction failed');
      }
      
    } catch (error) {
      console.error('Transfer error:', error);
      
      // Handle specific error types
      if (error.code === 'INSUFFICIENT_FUNDS') {
        throw new Error('Fondi insufficienti per la transazione');
      } else if (error.code === 'USER_REJECTED') {
        throw new Error('Transazione rifiutata dall\'utente');
      } else if (error.message.includes('insufficient funds')) {
        throw new Error('TEO insufficienti o fondi per gas insufficienti');
      } else if (error.message.includes('user rejected')) {
        throw new Error('Transazione rifiutata dall\'utente');
      }
      
      throw new Error(`Errore nel trasferimento: ${error.message}`);
    }
  }

  /**
   * Transfer tokens using reward pool for gas fees (for testing)
   */
  async transferTokensWithPoolGas(fromAddress, toAddress, amount) {
    try {
      const response = await fetch('/api/blockchain/transfer-with-pool-gas/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          from_address: fromAddress,
          to_address: toAddress,
          amount: amount.toString()
        })
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Transfer failed');
      }

      return data.transaction_hash;
    } catch (error) {
      console.error('Error in transferTokensWithPoolGas:', error);
      throw error;
    }
  }

  /**
   * Simulate user payment via reward pool (for testing without gas fees)
   */
  async simulatePaymentViaPool(fromAddress, toAddress, amount) {
    try {
      const response = await fetch('/api/v1/blockchain/simulate-payment/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          from_user_address: fromAddress,
          to_address: toAddress,
          amount: amount.toString()
        })
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Payment simulation failed');
      }

      return data.transaction_hash;
    } catch (error) {
      console.error('Error in simulatePaymentViaPool:', error);
      throw error;
    }
  }

  /**
   * Wait for transaction confirmation
   */
  async waitForTransactionConfirmation(txHash, confirmations = 1) {
    if (!this.provider) {
      throw new Error('Provider non inizializzato');
    }

    try {
      console.log(`Waiting for ${confirmations} confirmation(s) for transaction: ${txHash}`);
      
      const receipt = await this.provider.waitForTransaction(txHash, confirmations);
      
      if (receipt && receipt.status === 1) {
        console.log('Transaction confirmed:', txHash);
        return receipt;
      } else {
        throw new Error('Transaction failed or was reverted');
      }
      
    } catch (error) {
      console.error('Error waiting for transaction confirmation:', error);
      throw new Error(`Errore nella conferma della transazione: ${error.message}`);
    }
  }

  /**
   * Process course payment using MetaMask for transaction signing:
   * - Frontend handles all transactions via MetaMask
   * - Student signs approve() transaction
   * - Backend coordinates transferFrom() via reward pool
   * - All transaction hashes sent to backend for recording
   */
  async processCoursePayment(studentAddress, teacherAddress, coursePrice, courseId) {
    // Always use locked wallet address if available, otherwise use provided studentAddress
    const effectiveAddress = this.getLockedWalletAddress() || studentAddress;
    
    if (!effectiveAddress) {
      throw new Error('Wallet non connesso');
    }

    try {
      console.log('🎓 Processing course payment via MetaMask...');
      console.log(`Student: ${effectiveAddress}`);
      console.log(`Teacher: ${teacherAddress}`);
      console.log(`Price: ${coursePrice} TEO`);

      // Step 1: Check if student has enough MATIC for gas fees
      console.log('🔍 Checking MATIC balance for gas fees...');
      const maticCheck = await this.checkMaticForGas(effectiveAddress, '0.01'); // Require minimum 0.01 MATIC
      
      if (!maticCheck.hasEnough) {
        throw new Error(
          `MATIC insufficienti per gas fees. ` +
          `Hai ${maticCheck.balance} MATIC, servono almeno ${maticCheck.required} MATIC. ` +
          `Ottieni MATIC da: https://faucet.polygon.technology/`
        );
      }
      
      console.log(`✅ MATIC check passed: ${maticCheck.balance} MATIC available`);

      // Step 2: Check student's TEO balance
      console.log('🔍 Checking TEO balance...');
      const teoBalance = await this.getBalance(effectiveAddress);
      if (parseFloat(teoBalance) < parseFloat(coursePrice)) {
        throw new Error(
          `TEO insufficienti. Hai ${teoBalance} TEO, servono ${coursePrice} TEO`
        );
      }
      console.log(`✅ TEO check passed: ${teoBalance} TEO available`);

      // Step 3: Setup MetaMask connection and ensure correct account
      console.log('🔗 Setting up MetaMask connection...');
      
      if (!this.isMetamaskInstalled()) {
        throw new Error('MetaMask non è installato. Installa MetaMask per continuare.');
      }

      // Request access to accounts and switch to the correct one
      await window.ethereum.request({ method: 'eth_requestAccounts' });
      
      // Setup provider and signer
      const metamaskProvider = new ethers.BrowserProvider(window.ethereum);
      await this.switchToPolygonAmoy();
      const signer = await metamaskProvider.getSigner();
      
      // Check if MetaMask is on the correct account
      const currentMetaMaskAddress = await signer.getAddress();
      console.log('� Current MetaMask address:', currentMetaMaskAddress);
      console.log('🎯 Required address:', effectiveAddress);
      
      if (currentMetaMaskAddress.toLowerCase() !== effectiveAddress.toLowerCase()) {
        // Try multiple methods to switch to the correct account
        console.log('🔄 Attempting to switch MetaMask to correct account...');
        
        let switchSuccessful = false;
        let lastError = null;
        
        // Method 1: Try experimental wallet_switchEthereumAccount (if available)
        try {
          console.log('📱 Trying wallet_switchEthereumAccount...');
          await window.ethereum.request({
            method: 'wallet_switchEthereumAccount',
            params: [effectiveAddress]
          });
          
          // Check if switch was successful
          const newSigner = await metamaskProvider.getSigner();
          const newAddress = await newSigner.getAddress();
          
          if (newAddress.toLowerCase() === effectiveAddress.toLowerCase()) {
            console.log('✅ Successfully switched via wallet_switchEthereumAccount');
            this.signer = newSigner;
            switchSuccessful = true;
          }
        } catch (error) {
          console.log('❌ wallet_switchEthereumAccount failed or not supported:', error.message);
          lastError = error;
        }
        
        // Method 2: Try wallet_requestPermissions with account hint
        if (!switchSuccessful) {
          try {
            console.log('📱 Trying wallet_requestPermissions with account hint...');
            await window.ethereum.request({
              method: 'wallet_requestPermissions',
              params: [{ 
                eth_accounts: {},
                // Try to hint the desired account
                ...(effectiveAddress && { preferredAccount: effectiveAddress })
              }]
            });
            
            // Wait a bit for the UI to update
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Check if switch was successful
            const newSigner = await metamaskProvider.getSigner();
            const newAddress = await newSigner.getAddress();
            
            if (newAddress.toLowerCase() === effectiveAddress.toLowerCase()) {
              console.log('✅ Successfully switched via wallet_requestPermissions');
              this.signer = newSigner;
              switchSuccessful = true;
            }
          } catch (error) {
            console.log('❌ wallet_requestPermissions failed:', error.message);
            lastError = error;
          }
        }
        
        // Method 3: Try force re-requesting accounts
        if (!switchSuccessful) {
          try {
            console.log('📱 Trying force eth_requestAccounts...');
            
            // First disconnect any existing permissions
            try {
              await window.ethereum.request({
                method: 'wallet_revokePermissions',
                params: [{ eth_accounts: {} }]
              });
            } catch (revokeError) {
              console.log('Revoke permissions not supported or failed');
            }
            
            // Then request accounts again
            const accounts = await window.ethereum.request({
              method: 'eth_requestAccounts',
              params: []
            });
            
            console.log('Available accounts after request:', accounts);
            
            // Wait a bit for the UI to update
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // Check if switch was successful
            const newSigner = await metamaskProvider.getSigner();
            const newAddress = await newSigner.getAddress();
            
            if (newAddress.toLowerCase() === effectiveAddress.toLowerCase()) {
              console.log('✅ Successfully switched via force eth_requestAccounts');
              this.signer = newSigner;
              switchSuccessful = true;
            }
          } catch (error) {
            console.log('❌ force eth_requestAccounts failed:', error.message);
            lastError = error;
          }
        }
        
        // Method 4: As last resort, try to trigger MetaMask popup with specific error
        if (!switchSuccessful) {
          try {
            console.log('📱 Trying to trigger MetaMask account selection...');
            
            // Send a dummy transaction request that will fail but should trigger account selection
            const dummyTx = {
              from: effectiveAddress, // This should trigger MetaMask to ask for account switch
              to: effectiveAddress,
              value: '0x0',
              data: '0x'
            };
            
            try {
              await window.ethereum.request({
                method: 'eth_sendTransaction',
                params: [dummyTx]
              });
            } catch (txError) {
              // We expect this to fail, but it might trigger account selection
              console.log('Dummy transaction triggered account selection popup');
            }
            
            // Wait for user interaction
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Check if switch was successful
            const newSigner = await metamaskProvider.getSigner();
            const newAddress = await newSigner.getAddress();
            
            if (newAddress.toLowerCase() === effectiveAddress.toLowerCase()) {
              console.log('✅ Successfully switched via dummy transaction trigger');
              this.signer = newSigner;
              switchSuccessful = true;
            }
          } catch (error) {
            console.log('❌ dummy transaction trigger failed:', error.message);
            lastError = error;
          }
        }
        
        // If all automatic methods failed, provide enhanced user instructions
        if (!switchSuccessful) {
          const availableAccounts = await window.ethereum.request({ method: 'eth_accounts' });
          const isAccountAvailable = availableAccounts.some(account => 
            account.toLowerCase() === effectiveAddress.toLowerCase()
          );
          
          if (!isAccountAvailable) {
            throw new Error(
              `❌ L'account richiesto non è disponibile in MetaMask.\n\n` +
              `Account richiesto: ${effectiveAddress}\n` +
              `Account disponibili in MetaMask: ${availableAccounts.join(', ')}\n\n` +
              `📥 Prima importa l'account in MetaMask:\n` +
              `1. 🦊 Apri MetaMask\n` +
              `2. ➕ Clicca "Aggiungi account o hardware wallet"\n` +
              `3. 📋 Scegli "Importa account"\n` +
              `4. 🔑 Inserisci la chiave privata per ${effectiveAddress}\n` +
              `5. 🔄 Riprova l'acquisto`
            );
          }
          
          throw new Error(
            `🔄 MetaMask ha aperto la pagina di gestione connessioni.\n\n` +
            `Account attuale connesso: ${currentMetaMaskAddress}\n` +
            `Account richiesto: ${effectiveAddress}\n\n` +
            `📋 Nella pagina MetaMask che si è aperta:\n` +
            `1. ✅ Collega l'account che termina con: ...${effectiveAddress.slice(-6)}\n` +
            `2. ❌ Scollega altri account se necessario\n` +
            `3. 🔄 Torna qui e riprova l'acquisto\n\n` +
            `💡 Account disponibili: ${availableAccounts.map(acc => `...${acc.slice(-6)}`).join(', ')}\n` +
            `🔍 Dettaglio tecnico: ${lastError?.message || 'Switch automatico completato, verifica le connessioni'}`
          );
        }
      } else {
        console.log('✅ MetaMask is already on the correct account');
        this.signer = signer;
      }
      
      // Create contract instance with the correct signer
      this.contract = new ethers.Contract(
        TEOCOIN_CONTRACT_ADDRESS,
        TEOCOIN_ABI,
        this.signer
      );

      // Calculate amounts
      const coursePriceWei = ethers.parseEther(coursePrice.toString());
      const commissionRate = 0.15; // 15%
      const commissionAmount = parseFloat(coursePrice) * commissionRate;
      const teacherAmount = parseFloat(coursePrice) - commissionAmount;

      console.log(`💰 Amounts: Course=${coursePrice} TEO, Teacher=${teacherAmount} TEO, Commission=${commissionAmount} TEO`);

      // Step 4: Get reward pool address from backend
      const prerequisitesResponse = await fetch('/api/v1/blockchain/check-course-payment-prerequisites/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || localStorage.getItem('access')}`
        },
        body: JSON.stringify({
          student_address: effectiveAddress,
          course_price: coursePrice.toString()
        })
      });

      if (!prerequisitesResponse.ok) {
        throw new Error('Failed to get payment prerequisites');
      }

      const prerequisites = await prerequisitesResponse.json();
      const rewardPoolAddress = prerequisites.reward_pool_address;

      if (!rewardPoolAddress) {
        throw new Error('Reward pool address not configured');
      }

      console.log(`🏦 Reward pool address: ${rewardPoolAddress}`);

      // Step 5: Student approves reward pool to spend their TEO (MetaMask signature)
      console.log('✍️ Requesting student approval via MetaMask...');
      
      // First verify we're on the correct network
      const network = await this.signer.provider.getNetwork();
      console.log('🌐 Current network:', network.chainId, network.name);
      if (network.chainId !== 80002n) { // Polygon Amoy chainId as BigInt
        console.log('⚠️ Wrong network detected, switching...');
        await this.switchToPolygonAmoy();
      }
      
      // Estimate gas before sending transaction
      let gasEstimate;
      try {
        gasEstimate = await this.contract.connect(this.signer).approve.estimateGas(
          rewardPoolAddress,
          coursePriceWei
        );
        console.log('⛽ Gas estimate for approval:', gasEstimate.toString());
      } catch (gasError) {
        console.warn('⚠️ Gas estimation failed:', gasError.message);
        gasEstimate = 50000n; // Fallback gas limit
      }
      
      // Send approval transaction with explicit gas limit
      const approvalTx = await this.contract.connect(this.signer).approve(
        rewardPoolAddress,
        coursePriceWei,
        {
          gasLimit: gasEstimate * 110n / 100n // Add 10% buffer
        }
      );

      console.log('⏳ Waiting for approval confirmation...');
      const approvalReceipt = await approvalTx.wait();
      console.log(`✅ Approval confirmed: ${approvalReceipt.hash}`);

      // Step 6: Send transaction details to backend for transferFrom execution
      console.log('📤 Sending transaction details to backend...');
      const response = await fetch('/api/v1/blockchain/execute-course-payment/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || localStorage.getItem('access')}`
        },
        body: JSON.stringify({
          student_address: effectiveAddress,
          teacher_address: teacherAddress,
          course_price: coursePrice.toString(),
          course_id: courseId,
          approval_tx_hash: approvalReceipt.hash,
          teacher_amount: teacherAmount.toString(),
          commission_amount: commissionAmount.toString()
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Payment execution failed');
      }

      const result = await response.json();
      console.log('✅ Course payment executed successfully:', result);
      console.log('🔍 Debug - teacher_payment_tx value:', result.teacher_payment_tx);
      console.log('🔍 Debug - commission_tx value:', result.commission_tx);

      return {
        transactionHash: result.teacher_payment_tx,
        studentAddress: effectiveAddress,
        teacherAddress: result.teacher_address,
        teacherAmount: result.teacher_amount,
        commissionAmount: result.commission_amount,
        totalPaid: coursePrice.toString(),
        approvalTx: approvalReceipt.hash,
        commissionTx: result.commission_tx
      };

    } catch (error) {
      console.error('❌ Course payment failed:', error);
      
      // Handle specific MetaMask errors
      if (error.code === 4001) {
        throw new Error('Transazione rifiutata dall\'utente');
      } else if (error.code === -32603) {
        throw new Error('Errore interno della rete blockchain. Verifica di essere connesso a Polygon Amoy e riprova.');
      } else if (error.message.includes('insufficient funds')) {
        throw new Error('Fondi insufficienti per le gas fee. Aggiungi MATIC al tuo wallet.');
      } else if (error.message.includes('gas')) {
        throw new Error('Errore nelle gas fee. Prova ad aumentare il gas limit in MetaMask.');
      } else if (error.message.includes('network')) {
        throw new Error('Errore di rete. Verifica la connessione e riprova.');
      }
      
      throw error;
    }
  }

  /**
   * Get MATIC balance for wallet address
   */
  async getMaticBalance(address) {
    if (!address || address.trim() === '') {
      throw new Error('Nessun indirizzo wallet specificato');
    }

    try {
      // Use read-only provider to prevent MetaMask interference
      const provider = new ethers.JsonRpcProvider(POLYGON_AMOY_RPC_URL);
      const balance = await provider.getBalance(address);
      
      console.log('⛽ MATIC balance ottenuto per indirizzo:', address, 'Balance:', ethers.formatEther(balance));
      return ethers.formatEther(balance);
      
    } catch (error) {
      console.error('Errore nel recupero balance MATIC per indirizzo', address, ':', error);
      throw new Error('Errore nel recupero del saldo MATIC');
    }
  }

  /**
   * Check if user has enough MATIC for gas fees
   */
  async checkMaticForGas(address, minMaticRequired = '0.01') {
    try {
      const maticBalance = await this.getMaticBalance(address);
      const hasEnoughMatic = parseFloat(maticBalance) >= parseFloat(minMaticRequired);
      
      return {
        balance: maticBalance,
        hasEnough: hasEnoughMatic,
        required: minMaticRequired
      };
    } catch (error) {
      console.error('Errore nel controllo MATIC:', error);
      return {
        balance: '0',
        hasEnough: false,
        required: minMaticRequired,
        error: error.message
      };
    }
  }

  /**
   * Setup stable connection that ignores MetaMask account changes
   */
  setupStableConnection() {
    if (window.ethereum && !this._hasStableConnectionSetup) {
      this._hasStableConnectionSetup = true;
      
      const handleAccountsChanged = (accounts) => {
        console.log('⚠️ MetaMask account change detected:', accounts);
        console.log('🔒 Wallet remains locked to:', this.lockedWalletAddress);
        console.log('🚫 Ignoring MetaMask account change - wallet is locked');
        // Do NOT change userAddress or re-initialize the connection
        // Keep the original wallet address locked
        // This is critical for stable wallet connection
      };

      const handleChainChanged = (chainId) => {
        console.log('🔗 MetaMask chain changed:', chainId);
        // Only reload if we're still on the correct chain
        if (chainId === POLYGON_AMOY_CHAIN_ID) {
          console.log('✅ Still on correct chain');
        } else {
          console.warn('⚠️ Warning: Not on Polygon Amoy network');
        }
      };

      // Add event listeners
      window.ethereum.on('accountsChanged', handleAccountsChanged);
      window.ethereum.on('chainChanged', handleChainChanged);
      
      // Store cleanup function
      this._removeStableConnectionListeners = () => {
        if (window.ethereum) {
          window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
          window.ethereum.removeListener('chainChanged', handleChainChanged);
        }
        this._hasStableConnectionSetup = false;
      };
    }
  }

  /**
   * Disconnect wallet and unlock the connection
   */
  disconnectWallet() {
    // Remove event listeners
    if (this._removeStableConnectionListeners) {
      this._removeStableConnectionListeners();
    }
    
    // Clear localStorage
    localStorage.removeItem('connectedWalletAddress');
    localStorage.removeItem('isWalletLocked');
    localStorage.removeItem('lockedWalletAddress');
    
    // Reset all connection state
    this.provider = null;
    this.signer = null;
    this.contract = null;
    this.userAddress = null;
    this.isWalletLocked = false;
    this.lockedWalletAddress = null;
    
    console.log('🔓 Wallet disconnected and unlocked');
  }

  /**
   * Check if wallet is locked to a specific address
   */
  isWalletLockedToAddress() {
    return this.isWalletLocked && this.lockedWalletAddress;
  }

  /**
   * Get the locked wallet address
   */
  getLockedWalletAddress() {
    return this.lockedWalletAddress;
  }

  /**
   * Enable signing for locked wallet (needed for transactions)
   */
  async enableSigning() {
    if (!this.isWalletLocked || !this.lockedWalletAddress) {
      throw new Error('Wallet non bloccato - impossibile abilitare firma');
    }
    
    if (!window.ethereum) {
      throw new Error('MetaMask non disponibile');
    }
    
    try {
      // Create MetaMask provider for signing
      const metamaskProvider = new ethers.BrowserProvider(window.ethereum);
      
      // Ensure we're on the correct network
      await this.switchToPolygonAmoy();
      
      // Get signer
      this.signer = await metamaskProvider.getSigner();
      
      // Verify the signer address matches locked address
      const signerAddress = await this.signer.getAddress();
      if (signerAddress.toLowerCase() !== this.lockedWalletAddress.toLowerCase()) {
        // This is a critical error - the user needs to switch accounts in MetaMask
        throw new Error(
          `MetaMask è connesso all'account ${signerAddress} ma il wallet bloccato è ${this.lockedWalletAddress}. ` +
          `Per favore cambia account in MetaMask e seleziona l'account ${this.lockedWalletAddress} prima di procedere.`
        );
      }
      
      // Create contract instance with signer for transactions
      this.contract = new ethers.Contract(
        TEOCOIN_CONTRACT_ADDRESS,
        TEOCOIN_ABI,
        this.signer
      );
      
      console.log('✅ Signing enabled for locked wallet:', this.lockedWalletAddress);
      return true;
      
    } catch (error) {
      console.error('❌ Error enabling signing:', error);
      throw new Error('Impossibile abilitare firma: ' + error.message);
    }
  }

  /**
   * Helper function to prepare MetaMask for the correct account
   * This can be called before transactions to ensure smooth UX
   */
  async prepareMetaMaskAccount(requiredAddress) {
    if (!this.isMetamaskInstalled()) {
      throw new Error('MetaMask non è installato');
    }

    try {
      console.log('🔧 Preparing MetaMask for account:', requiredAddress);
      
      // Request account access
      await window.ethereum.request({ method: 'eth_requestAccounts' });
      
      const provider = new ethers.BrowserProvider(window.ethereum);
      const signer = await provider.getSigner();
      const currentAddress = await signer.getAddress();
      
      if (currentAddress.toLowerCase() !== requiredAddress.toLowerCase()) {
        // Try to trigger account selection
        await window.ethereum.request({
          method: 'wallet_requestPermissions',
          params: [{ eth_accounts: {} }]
        });
        
        // Check again after permission request
        const newSigner = await provider.getSigner();
        const newAddress = await newSigner.getAddress();
        
        return {
          success: newAddress.toLowerCase() === requiredAddress.toLowerCase(),
          currentAddress: newAddress,
          requiredAddress: requiredAddress
        };
      }
      
      return {
        success: true,
        currentAddress: currentAddress,
        requiredAddress: requiredAddress
      };
      
    } catch (error) {
      console.error('Error preparing MetaMask account:', error);
      return {
        success: false,
        error: error.message,
        requiredAddress: requiredAddress
      };
    }
  }
}

// Export singleton instance
export const web3Service = new Web3Service();
export default web3Service;

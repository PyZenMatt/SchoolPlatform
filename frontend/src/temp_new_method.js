  /**
   * NEW APPROVE+SPLIT PROCESS: Process course payment with single approval
   * Student approves tokens to reward pool, backend handles the split
   */
  async processCoursePaymentApproveAndSplit(studentAddress, teacherAddress, coursePrice, courseId) {
    // Always use locked wallet address if available, otherwise use provided studentAddress
    const effectiveAddress = this.getLockedWalletAddress() || studentAddress;
    
    if (!effectiveAddress) {
      throw new Error('Wallet non connesso');
    }

    try {
      console.log('🎓 APPROVE+SPLIT: Processing course payment with single approval...');
      console.log(`Student: ${effectiveAddress}`);
      console.log(`Teacher: ${teacherAddress}`);
      console.log(`Price: ${coursePrice} TEO`);

      // Step 1: Check if student has enough MATIC for gas fees (much less needed now)
      console.log('🔍 Checking MATIC balance for gas fees...');
      const maticCheck = await this.checkMaticForGas(effectiveAddress, '0.005'); // Reduced from 0.01
      
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

      // Step 3: Setup MetaMask connection
      console.log('🔗 Setting up MetaMask connection...');
      
      if (!this.isMetamaskInstalled()) {
        throw new Error('MetaMask non è installato. Installa MetaMask per continuare.');
      }

      await window.ethereum.request({ method: 'eth_requestAccounts' });
      
      const metamaskProvider = new ethers.BrowserProvider(window.ethereum);
      await this.switchToPolygonAmoy();
      const signer = await metamaskProvider.getSigner();
      
      // Verify correct account
      const currentMetaMaskAddress = await signer.getAddress();
      if (currentMetaMaskAddress.toLowerCase() !== effectiveAddress.toLowerCase()) {
        throw new Error(
          `MetaMask è connesso all'account ${currentMetaMaskAddress} ma è richiesto l'account ${effectiveAddress}. ` +
          `Cambia account in MetaMask e riprova.`
        );
      }
      
      console.log('✅ MetaMask connected to correct account');
      this.signer = signer;
      
      // Create contract instance
      this.contract = new ethers.Contract(
        TEOCOIN_CONTRACT_ADDRESS,
        TEOCOIN_ABI,
        this.signer
      );

      // Step 4: Get reward pool address from backend
      console.log('🏦 Getting reward pool address...');
      const poolResponse = await fetch('/api/v1/blockchain/reward-pool-address/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || localStorage.getItem('access')}`
        }
      });

      if (!poolResponse.ok) {
        const errorData = await poolResponse.json();
        throw new Error(errorData.error || 'Failed to get reward pool address');
      }

      const poolResult = await poolResponse.json();
      const rewardPoolAddress = poolResult.reward_pool_address;

      if (!rewardPoolAddress) {
        throw new Error('Reward pool address not configured');
      }

      console.log(`🏦 Reward pool address: ${rewardPoolAddress}`);

      // Step 5: Check current allowance
      console.log('🔍 Checking current allowance...');
      const coursePriceWei = ethers.parseEther(coursePrice.toString());
      const currentAllowance = await this.contract.allowance(effectiveAddress, rewardPoolAddress);
      
      console.log(`Current allowance: ${ethers.formatEther(currentAllowance)} TEO`);
      console.log(`Required: ${coursePrice} TEO`);

      // Step 6: Approve tokens if needed
      if (currentAllowance < coursePriceWei) {
        console.log('💳 SINGLE SIGNATURE: Approving tokens to reward pool...');
        
        const approveTx = await this.contract.connect(this.signer).approve(
          rewardPoolAddress,
          coursePriceWei,
          {
            gasLimit: 60000n // Set explicit gas limit
          }
        );

        console.log('⏳ Waiting for approval confirmation...');
        const approveReceipt = await approveTx.wait();
        console.log(`✅ Approval confirmed: ${approveReceipt.hash}`);
      } else {
        console.log('✅ Sufficient allowance already exists');
      }

      // Step 7: Backend processes the payment split
      console.log('🚀 Backend processing payment split...');
      const paymentResponse = await fetch('/api/v1/blockchain/process-course-payment-direct/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || localStorage.getItem('access')}`
        },
        body: JSON.stringify({
          student_address: effectiveAddress,
          teacher_address: teacherAddress,
          price_in_teo: coursePriceWei.toString(), // Send in wei
          course_id: courseId
        })
      });

      if (!paymentResponse.ok) {
        const errorData = await paymentResponse.json();
        throw new Error(errorData.error || 'Payment processing failed');
      }

      const paymentResult = await paymentResponse.json();
      console.log('✅ Payment processed successfully by backend');

      return {
        success: true,
        studentAddress: effectiveAddress,
        teacherAddress: teacherAddress,
        totalPaid: coursePrice.toString(),
        teacherAmount: paymentResult.teacher_amount,
        commissionAmount: paymentResult.commission_amount,
        teacherTxHash: paymentResult.transaction_hash,
        commissionTxHash: paymentResult.commission_tx_hash,
        enrollmentId: paymentResult.enrollment_id,
        message: 'Pagamento completato con una sola firma - Backend ha gestito la distribuzione automaticamente'
      };

    } catch (error) {
      console.error('❌ Approve+Split course payment failed:', error);
      
      // Handle specific MetaMask errors
      if (error.code === 4001) {
        throw new Error('Transazione rifiutata dall\'utente');
      } else if (error.code === -32603) {
        throw new Error('Errore interno della rete blockchain. Verifica di essere connesso a Polygon Amoy e riprova.');
      } else if (error.message.includes('insufficient funds')) {
        throw new Error('Fondi insufficienti per le gas fee. Aggiungi MATIC al tuo wallet.');
      } else if (error.message.includes('INSUFFICIENT_ALLOWANCE')) {
        throw new Error('Approvazione token non riuscita. Riprova la transazione.');
      } else if (error.message.includes('INSUFFICIENT_BALANCE')) {
        throw new Error('TEO insufficienti nel wallet. Aggiungi più TEO e riprova.');
      } else if (error.message.includes('gas')) {
        throw new Error('Errore nelle gas fee. Prova ad aumentare il gas limit in MetaMask.');
      } else if (error.message.includes('network')) {
        throw new Error('Errore di rete. Verifica la connessione e riprova.');
      }
      
      throw error;
    }
  }

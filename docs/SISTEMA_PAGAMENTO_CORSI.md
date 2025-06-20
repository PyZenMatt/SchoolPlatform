# Sistema di Pagamento Corsi - TeoArt School Platform

## Panoramica

Il sistema di pagamento per i corsi della TeoArt School Platform utilizza un approccio **"approve + backend split"** che garantisce:
- Una sola transazione MetaMask per l'utente (migliore UX)
- Pagamento completo da parte dello studente (TEO + gas)
- Distribuzione automatica dei fondi tramite backend
- Sicurezza e trasparenza nelle transazioni

## Architettura del Sistema

### Flusso di Pagamento

```
1. Studente → Approve TEO tokens al contratto
2. Backend → Verifica approval
3. Backend → Esegue transferFrom per distribuire i fondi
4. Sistema → Conferma acquisto corso
```

### Componenti Coinvolti

- **Frontend React**: Interfaccia utente e integrazione MetaMask
- **Backend Django**: Logica di business e gestione transazioni
- **Smart Contract TEO**: Gestione dei token e trasferimenti
- **Blockchain Polygon**: Rete per le transazioni

## Implementazione Tecnica

### 1. Frontend (React)

#### File: `frontend/src/services/api/web3Service.js`

```javascript
// Funzione principale per il pagamento diretto
async processCoursePaymentDirect(courseId, priceInTeo, teacherAddress) {
    // 1. Verifica connessione wallet
    // 2. Calcola approval amount
    // 3. Esegue approve al contratto
    // 4. Chiama backend per conferma
}
```

#### File: `frontend/src/components/courses/CourseCheckoutModal.jsx`

- Interfaccia utente per il checkout
- Gestione stati di caricamento
- Feedback visivo per l'utente
- Integrazione con web3Service

### 2. Backend (Django)

#### File: `blockchain/views.py`

```python
# Endpoint per elaborare il pagamento
@api_view(['POST'])
def process_course_payment_direct(request):
    # 1. Verifica parametri
    # 2. Controlla approval
    # 3. Esegue transferFrom
    # 4. Distribuisce fondi
    # 5. Registra transazione
```

#### File: `blockchain/blockchain.py`

```python
# Servizio blockchain per gestione pagamenti
class BlockchainService:
    def student_pays_course_directly(self, student_address, course_price, teacher_address):
        # Logica di distribuzione fondi
        # 95% al teacher, 5% alla reward pool
```

### 3. Smart Contract Integration

#### Funzioni Utilizzate

- `approve(spender, amount)`: Student approva il contratto
- `transferFrom(from, to, amount)`: Backend trasferisce i fondi
- `balanceOf(address)`: Verifica saldi
- `allowance(owner, spender)`: Verifica approval

## Distribuzione dei Fondi

### Schema di Distribuzione

```
Prezzo Corso (100% TEO) →
├── Teacher (95%) 
└── Reward Pool (5%)
```

### Calcolo Automatico

```python
teacher_amount = int(course_price * 0.95)
reward_pool_amount = course_price - teacher_amount
```

## Vantaggi del Sistema

### Per gli Studenti

1. **Una sola transazione**: Solo un'approvazione MetaMask richiesta
2. **Costi chiari**: Pagano solo gas per l'approval
3. **Sicurezza**: Non devono inviare fondi a indirizzi multipli
4. **Esperienza fluida**: Processo semplificato

### Per i Teacher

1. **Pagamento automatico**: Ricevono il 95% immediatamente
2. **Nessuna gestione**: Non devono gestire transazioni
3. **Trasparenza**: Tutto tracciabile on-chain

### Per la Piattaforma

1. **Controllo**: Gestione centralizzata delle distribuzioni
2. **Flessibilità**: Possibilità di modificare percentuali
3. **Monitoraggio**: Tracking completo delle transazioni
4. **Sicurezza**: Riduce rischi di errori utente

## Gestione degli Errori

### Scenari di Errore

1. **Insufficient Balance**: Studente non ha abbastanza TEO
2. **Insufficient Allowance**: Approval non sufficiente
3. **Network Error**: Problemi di connessione blockchain
4. **Transaction Failed**: Fallimento transazione

### Handling degli Errori

```javascript
try {
    await web3Service.processCoursePaymentDirect(courseId, price, teacher);
} catch (error) {
    if (error.code === 'INSUFFICIENT_FUNDS') {
        // Messaggio specifico per fondi insufficienti
    } else if (error.code === 'USER_REJECTED') {
        // Messaggio per transazione rifiutata
    }
    // Gestione generica errori
}
```

## Sicurezza

### Misure di Sicurezza

1. **Validazione Input**: Tutti i parametri vengono validati
2. **Controlli Balance**: Verifica fondi prima dell'esecuzione
3. **Rate Limiting**: Limitazione richieste per prevenire spam
4. **Logging**: Tracking completo per audit
5. **Error Handling**: Gestione sicura degli errori

### Best Practices

- Validazione lato client e server
- Timeout per le transazioni
- Retry logic per fallimenti temporanei
- Monitoring delle transazioni

## Monitoring e Analytics

### Metriche Tracciate

- Numero di acquisti completati
- Tempo medio di completamento
- Tasso di fallimento transazioni
- Distribuzione errori per tipo

### Dashboard Admin

- Visualizzazione transazioni in tempo reale
- Report sui pagamenti
- Analisi performance sistema
- Alert per anomalie

## Configurazione

### Variabili di Ambiente

```bash
# Contratto TEO
TEO_CONTRACT_ADDRESS=0x...
TEO_CONTRACT_ABI_PATH=path/to/abi.json

# Wallet Backend
BACKEND_WALLET_PRIVATE_KEY=0x...
BACKEND_WALLET_ADDRESS=0x...

# Reward Pool
REWARD_POOL_ADDRESS=0x...

# Network
POLYGON_RPC_URL=https://polygon-rpc.com
CHAIN_ID=137
```

### Percentuali di Distribuzione

```python
# In settings.py o configurazione
TEACHER_PERCENTAGE = 0.95  # 95% al teacher
REWARD_POOL_PERCENTAGE = 0.05  # 5% alla reward pool
```

## Testing

### Test Unitari

```python
# Test distribuzione fondi
def test_course_payment_distribution():
    # Verifica calcolo percentuali
    # Verifica trasferimenti
    # Verifica registrazione transazioni

# Test integrazione
def test_full_payment_flow():
    # Test completo end-to-end
    # Verifica tutti i componenti
```

### Test E2E

- Simulazione completa pagamento
- Test con diversi scenari di errore
- Verifica UX su diversi browser

## Deployment

### Checklist Pre-Deploy

- [ ] Test su testnet completati
- [ ] Configurazione produzione verificata
- [ ] Backup database aggiornato
- [ ] Monitoring configurato
- [ ] Team informato sui cambiamenti

### Procedura di Deploy

1. Deploy del backend
2. Test API endpoints
3. Deploy del frontend
4. Test integrazione completa
5. Monitoring post-deploy

## Troubleshooting

### Problemi Comuni

#### 1. Transazione Pending Troppo a Lungo

**Causa**: Gas price troppo basso o congestione rete
**Soluzione**: Aumentare gas price o attendere

#### 2. Approval Non Riconosciuto

**Causa**: Delay nella blockchain o RPC non sincronizzato
**Soluzione**: Retry dopo qualche secondo

#### 3. Distribuzione Fondi Fallita

**Causa**: Insufficiente gas nel wallet backend
**Soluzione**: Ricaricare wallet backend con MATIC

### Log di Debug

```python
logger.info(f"Processing payment: student={student}, course={course_id}")
logger.info(f"Approval amount: {approval_amount}")
logger.info(f"Distribution: teacher={teacher_amount}, pool={pool_amount}")
```

## Roadmap Futuri Sviluppi

### Miglioramenti Pianificati

1. **Gas Optimization**: Riduzione costi gas per transazioni
2. **Multi-Token Support**: Supporto per altri token di pagamento
3. **Subscription Model**: Pagamenti ricorrenti per abbonamenti
4. **Escrow System**: Sistema di deposito garanzia
5. **Mobile App**: Integrazione con wallet mobile

### Considerazioni Tecniche

- Migrazione a Layer 2 per costi ridotti
- Implementazione meta-transactions
- Integrazione con altri DEX per liquidità
- Sistema di referral automatizzato

## Conclusioni

Il sistema "approve + backend split" offre il miglior equilibrio tra:
- **User Experience**: Una sola transazione per lo studente
- **Sicurezza**: Controllo completo dei fondi
- **Flessibilità**: Facile modifica delle logiche di distribuzione
- **Trasparenza**: Tutto tracciabile on-chain

Questa architettura garantisce scalabilità e maintainability per il futuro della piattaforma.

---

**Versione**: 2.0  
**Data**: Giugno 2025  
**Autore**: TeoArt Development Team  
**Stato**: Implementato e Testato

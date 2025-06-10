# Blockchain Tests

Questa cartella contiene tutti i test relativi all'integrazione blockchain e TeoCoin.

## Test di Setup e Configurazione
- `test_blockchain_setup.py` - Verifica la configurazione base della blockchain
- `test_config.py` - Test delle configurazioni
- `simple_contract_test.py` - Test semplice del contratto

## Test di Minting e Transfer
- `simple_mint_test.py` - Test di minting semplice
- `test_direct_mint.py` - Test di minting diretto
- `test_minimal_transfer.py` - Test di transfer minimale
- `test_single_transfer.py` - Test di transfer singolo

## Test di Gas e Ottimizzazione
- `test_high_gas_mint.py` - Test con gas alto
- `test_optimized_gas.py` - Test con gas ottimizzato
- `test_updated_gas_price.py` - Test con prezzo gas aggiornato

## Test di Integrazione
- `test_blockchain_integration.py` - Test di integrazione completa
- `test_blockchain_api.py` - Test delle API blockchain
- `test_blockchain_rewards.py` - Test del sistema di ricompense
- `test_contract_permissions.py` - Test dei permessi del contratto

## Test di Debug
- `debug_blockchain_user_issue.py` - Debug problemi utenti
- `debug_mint_failure.py` - Debug fallimenti di minting

## Test Specifici
- `test_admin_wallet_student.py` - Test wallet admin e studenti

## Come eseguire i test

```bash
# Eseguire un test specifico
python test_blockchain_setup.py

# Eseguire tutti i test blockchain
python -m pytest blockchain/tests/

# Eseguire test con output dettagliato
python test_blockchain_integration.py -v
```

## Note
- Assicurarsi di avere MATIC sufficiente per i test che richiedono transazioni
- I test utilizzano la testnet Polygon Amoy
- Verificare che le variabili d'ambiente siano configurate correttamente

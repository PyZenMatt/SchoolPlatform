🎯 Obiettivo tecnico

Realizzare un MVP scalabile e manutenibile, con API REST pulite, sicure e ben documentate. L’MVP prevede:

    Registrazione/Login con gestione sicura del token

    Wallet TeoCoin virtuale con saldo e cronologia

    Corsi creati dai maestri

    Lezioni con contenuti multimediali

    Esercizi svolti dagli studenti

    Sistema di ricompensa in TeoCoin

    Valutazioni da parte dei maestri

🔧 Stack Tecnologico

    Backend: Django + Django REST Framework

    Database: PostgreSQL (consigliato)

    Token (fase 1): TeoCoin simulato nel DB

    Token (fase 2): Integrazione con smart contract su Polygon

    Deployment locale: Ubuntu 24.04 + WSL

    IDE: Visual Studio Code

    Storage (futuro): AWS S3 o IPFS

    FrontEnd : ReactJs , Datta theme

✅ Best Practice richieste (seguire SEMPRE)
1. Architettura e struttura

    Usa la struttura "apps modulari" (users, courses, wallet, rewards, ecc.)

    Mantieni separazione tra models, serializers, views, permissions, tests

    Evita la logica nelle view: usa services.py o use cases per la business logic

    Supporta la futura scalabilità del progetto (es. multi-tenant ready)

2. API Design

    Usa ViewSet + Router (solo se ha senso) oppure APIView generiche ben strutturate

    Rispetta le convenzioni RESTful (GET, POST, PATCH, DELETE coerenti)

    Rispondi sempre con HTTP status appropriati e messaggi standardizzati

    Usa paginazione, filtri, e ordina per default

3. Sicurezza

    Autenticazione via Token JWT o Sessioni (scalabile, sicuro, configurato con djoser o simili)

    Permessi granulari: IsAuthenticated, IsOwner, IsTeacher, ecc.

    Proteggi da iniezioni, accessi non autorizzati, enumerazioni

    Mai esporre dati sensibili negli errori

4. Testing

    Ogni model, serializer, view, permission, service deve avere test unitari

    Usa pytest + pytest-django con factory_boy per creare test data

    Mantieni il codice testabile e isolato

5. Performance & Query Optimization

    Usa select_related e prefetch_related dove necessario

    Evita query N+1

    Tutti gli endpoint devono essere misurabili e tracciabili (es. con django-silk, sentry)

6. Serializers

    Usa ModelSerializer, ma definisci read_only_fields e extra_kwargs esplicitamente

    Valida i dati in modo esplicito in validate_* e validate()

    Evita logiche nei serializer, spostale nei servizi

7. Gestione Wallet & Token

    TeoCoin è un field gestito lato server (mai modificabile via API)

    Ogni modifica al wallet deve passare da una funzione centrale di transazione

    Le reward devono essere approvate o automatizzate, ma sempre tracciabili in log

    Usa un sistema di registrazione delle transazioni (TransactionLog, RewardLog, ecc.)

8. Documentazione & Dev Experience

    Auto-documentazione via drf-spectacular o drf-yasg

    README chiaro con make setup, make run, make test

    Tutto il codice documentato con docstring stile Google

9. Versionamento API

    Prevedi /api/v1/ per tutto (anche in MVP)

    Permetti futura evoluzione senza rompere compatibilità

10. Deployment & CI

    Usa .env e django-environ per la configurazione

    Configura Dockerfile e docker-compose.yml anche solo per dev

    Usa pre-commit hooks con black, flake8, isort, mypy

Sei chiamato a contribuire al progetto solo seguendo queste best practice. Ogni scelta deve essere giustificata da scalabilità, sicurezza e manutenibilità.
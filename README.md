# SchoolPlatform

SchoolPlatform è una piattaforma concepita per rivoluzionare l’apprendimento e l’insegnamento, abbinando metodi tradizionali e tecnologia moderna. L’obiettivo è quello di democratizzare l’accesso a risorse formative di qualità, mettendo in contatto studenti e insegnanti in un ambiente interattivo e incentivato.

## Missione

- **Per gli studenti:** Fornire un ambiente in cui la pratica, l’apprendimento e il miglioramento vengono premiati (ad es. attraverso un sistema di token o TeoCoin simulati).
- **Per gli insegnanti:** Offrire strumenti per caricare lezioni, valutare i progressi degli studenti e ricevere compensazioni in base al proprio impegno formativo.
- **Per la comunità:** Creare un ecosistema educativo aperto, in cui la conoscenza diventa accessibile e valorizzata.

## Tecnologie Utilizzate

- **Backend:** [Django](https://www.djangoproject.com/) e [Django REST Framework](https://www.django-rest-framework.org/)  
- **Frontend:** (Evento in sviluppo – puoi inserire qui il framework utilizzato, ad esempio Next.js se previsto)  
- **Database:** PostgreSQL (o SQLite per il testing locale)
- **Ambiente di sviluppo:** Ubuntu 24.04 su WSL, Visual Studio Code
- **Token (fase sperimentale):** TeoCoin simulato sul database  
- **Storage:** In previsione di AWS S3 o IPFS per la gestione di asset e file

## Funzionalità Attuali

Al momento la piattaforma implementa:
- Un’architettura modulare e una struttura di base per il backend in Django.
- Interfacce API per il recupero e la gestione dei dati.
- Gestione delle migrazioni e organizzazione dei moduli per modelli, viste e serializers.
- Una struttura iniziale (scaffolding) per consentire lo sviluppo incrementale delle funzionalità future.

## Come Iniziare

### Prerequisiti
- Python 3.8+
- Node.js (se il frontend è in sviluppo)
- Virtualenv

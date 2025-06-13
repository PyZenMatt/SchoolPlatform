# README per il Sito Jekyll di TeoArt School Platform

## Descrizione
Questo è il sito di documentazione per la TeoArt School Platform, costruito con Jekyll per essere hostato gratuitamente su GitHub Pages.

## Struttura del Progetto

```
docs-site/
├── _config.yml          # Configurazione Jekyll
├── _layouts/             # Template layout
│   ├── default.html      # Layout principale
│   └── page.html         # Layout per pagine
├── assets/
│   ├── css/
│   │   └── main.scss     # Stili personalizzati
│   ├── js/
│   │   └── main.js       # JavaScript personalizzato
│   └── images/           # Immagini del sito
├── index.md              # Homepage
├── features.md           # Pagina funzionalità
├── technology.md         # Pagina tecnologie
├── demo.md               # Pagina demo
├── contact.md            # Pagina contatti
├── Gemfile               # Dipendenze Ruby
└── README.md             # Questo file
```

## Setup Locale

### Prerequisiti
- Ruby (versione 2.7 o superiore)
- Bundler

### Installazione
```bash
# Installa le dipendenze
bundle install

# Avvia il server di sviluppo
bundle exec jekyll serve

# Il sito sarà disponibile su http://localhost:4000
```

## Deploy su GitHub Pages

1. Crea un repository su GitHub
2. Carica tutti i file in questo repository
3. Vai nelle impostazioni del repository
4. Nella sezione "Pages", seleziona "Deploy from a branch"
5. Scegli il branch "main" e la cartella "/" (root)
6. Il sito sarà disponibile su `https://username.github.io/repository-name`

## Personalizzazione

### Configurazione
Modifica `_config.yml` per personalizzare:
- Titolo del sito
- Descrizione
- URL base
- Link social
- Menu di navigazione

### Contenuti
- **Homepage**: Modifica `index.md`
- **Funzionalità**: Modifica `features.md`
- **Tecnologie**: Modifica `technology.md`
- **Demo**: Modifica `demo.md`
- **Contatti**: Modifica `contact.md`

### Stili
Modifica `assets/css/main.scss` per personalizzare:
- Colori del brand
- Typography
- Layout responsive
- Animazioni

### Immagini
Aggiungi le tue immagini in `assets/images/`:
- `logo.png` - Logo del sito
- `favicon.ico` - Icona del browser
- `platform-dashboard.png` - Screenshot della dashboard
- `hero-background.jpg` - Immagine hero
- Altri asset grafici

## Funzionalità Incluse

### Design
- ✅ Design responsive (mobile-first)
- ✅ Dark mode support
- ✅ Animazioni CSS moderne
- ✅ Gradients e effetti visivi
- ✅ Typography ottimizzata

### Componenti
- ✅ Hero section con CTA
- ✅ Feature cards animate
- ✅ Tech stack showcase
- ✅ Demo interattive (placeholder)
- ✅ Form di contatto
- ✅ FAQ section
- ✅ Footer completo

### Performance
- ✅ CSS/JS minificati
- ✅ Immagini ottimizzate
- ✅ Font web ottimizzati
- ✅ Lazy loading
- ✅ SEO ottimizzato

### Integrations
- ✅ Bootstrap 5
- ✅ Font Awesome icons
- ✅ Jekyll SEO tag
- ✅ Jekyll sitemap
- ✅ Jekyll feed
- ✅ Google Analytics ready

## Customizzazione Avanzata

### Aggiungere Nuove Pagine
1. Crea un nuovo file `.md` nella root
2. Aggiungi il front matter YAML:
```yaml
---
layout: page
title: "Titolo Pagina"
description: "Descrizione per SEO"
---
```
3. Aggiungi il link nel menu modificando `_config.yml`

### Aggiungere Blog
1. Crea la cartella `_posts/`
2. Aggiungi post con formato `YYYY-MM-DD-title.md`
3. Crea la pagina blog/index.md

### Integrazioni Esterne
- **Google Analytics**: Aggiungi il tracking ID in `_config.yml`
- **Contact Forms**: Integra con Netlify Forms o Formspree
- **Newsletter**: Integra con Mailchimp o ConvertKit
- **Chat**: Aggiungi widget Intercom o Crisp

## Best Practices

### SEO
- ✅ Meta tags ottimizzati
- ✅ Structured data
- ✅ Sitemap XML
- ✅ RSS feed
- ✅ URL friendly

### Performance
- ✅ Minificazione CSS/JS
- ✅ Ottimizzazione immagini
- ✅ Caching headers
- ✅ CDN ready

### Accessibilità
- ✅ Semantic HTML
- ✅ Alt text per immagini
- ✅ Contrast ratio conforme
- ✅ Keyboard navigation

## Licenza
Questo template è rilasciato sotto licenza MIT. Puoi usarlo liberamente per i tuoi progetti.

## Supporto
Per domande o problemi, contatta il team di sviluppo all'indirizzo: dev@teoart.it
